#!/usr/bin/env python3
"""只读采集审计：核对过程完整性、哈希、模型、预算与搜索结果索引。

不打开最终回答做质量判断，也不修改任何 run 的 process.jsonl/evaluation.json。
"""
from __future__ import annotations
import argparse, base64, hashlib, json, re, sys
from pathlib import Path

URL_RE = re.compile(r'https?://[^\s<>"\'\]\)}`]+')

def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unpack(payload):
    if not isinstance(payload, dict): return ''
    if payload.get('encoding') == 'utf-8': return payload.get('content', '')
    if payload.get('encoding') == 'base64':
        return base64.b64decode(payload.get('content', '')).decode('utf-8', errors='replace')
    return ''
def dump(path, value): Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def protocol_key(meta):
    p = meta.get('protocol') or {}
    return (meta.get('task_id'), str(meta.get('ecosystem', '')).lower(), p.get('budget_arm'))

def limits(meta):
    p = meta.get('protocol') or {}; arm = p.get('budget_arm')
    arms = p.get('budget_arms', {})
    cfg = arms.get(arm, {}) if isinstance(arms, dict) else {}
    return {'search': cfg.get('search_limit', cfg.get('search_budget', cfg.get('search'))),
            'fetch': cfg.get('fetch_limit', cfg.get('fetch_budget', cfg.get('fetch')))}

def event_json(row):
    return json.loads(unpack(row.get('content', {}))) if row.get('type') == 'client_note' else None

def run_audit(run_dir, protocol_path, tasks_path, skill_path, expected_manifest):
    p = run_dir / 'process.jsonl'
    result = {'run_dir': str(run_dir), 'status': 'pending', 'issues': [], 'warnings': []}
    if not p.is_file():
        result['issues'].append('missing_process_jsonl'); return result, []
    try: rows = [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
    except Exception as exc:
        result['issues'].append('process_parse_error:' + repr(exc)); return result, []
    if not rows or rows[0].get('type') != 'run_start':
        result['issues'].append('missing_run_start'); return result, []
    meta = rows[0].get('metadata', {}); result['run_id'] = meta.get('run_id'); result['key'] = protocol_key(meta)
    result['task_id'], result['ecosystem'], result['budget_arm'] = result['key']
    result['model_requested'] = meta.get('model_id')
    result['hashes'] = {'protocol_match': meta.get('protocol_sha256') == sha(protocol_path),
                        'tasks_match': meta.get('tasks_sha256') == sha(tasks_path),
                        'question_matches_metadata': bool(meta.get('question_sha256'))}
    if not result['hashes']['protocol_match']: result['issues'].append('protocol_sha256_mismatch')
    if not result['hashes']['tasks_match']: result['issues'].append('tasks_sha256_mismatch')
    # Verify question bytes against metadata, without looking at final answer.
    q = rows[0].get('question', {})
    qbytes = unpack(q).encode('utf-8')
    result['hashes']['question_matches_metadata'] = hashlib.sha256(qbytes).hexdigest() == meta.get('question_sha256')
    if not result['hashes']['question_matches_metadata']: result['issues'].append('question_sha256_mismatch')
    actual_skill = {}
    if skill_path.exists():
        actual_skill = {str(x.relative_to(skill_path)): sha(x) for x in sorted(skill_path.rglob('*'))
                        if x.is_file() and '__pycache__' not in x.parts}
    declared = meta.get('skill_hashes') or {}
    skill_bad = [k for k, v in declared.items() if actual_skill.get(k) != v]
    result['hashes']['skill_matches_metadata'] = not skill_bad
    result['skill_hash_mismatches'] = skill_bad
    if skill_bad: result['issues'].append('skill_hash_mismatch')
    if expected_manifest and meta.get('skill_manifest_check', {}).get('mismatches'):
        result['issues'].append('skill_manifest_check_mismatch')

    # Sequence and request/result/dispatch correspondence; final answer is not inspected.
    ids = [r.get('id') for r in rows]; result['sequence_valid'] = all(r.get('seq') == i + 1 for i, r in enumerate(rows)) and len(ids) == len(set(ids))
    if not result['sequence_valid']: result['issues'].append('event_sequence_invalid')
    requests = {r['id']: r for r in rows if r.get('type') == 'tool_request'}
    dispatches = {r.get('request_id') for r in rows if r.get('type') == 'tool_dispatch'}
    results = {r.get('request_id'): r for r in rows if r.get('type') == 'tool_result'}
    missing = [rid for rid in requests if rid not in results]
    orphan_d = [rid for rid in dispatches if rid not in requests]
    orphan_r = [rid for rid in results if rid not in requests]
    result['tool_correspondence'] = {'requests': len(requests), 'dispatches': len(dispatches), 'results': len(results),
                                     'missing_results': missing, 'orphan_dispatches': list(orphan_d), 'orphan_results': list(orphan_r)}
    if missing or orphan_d or orphan_r: result['issues'].append('tool_request_result_correspondence')
    # A prior answer must occur in visible client output before the first tool request.
    first_tool_seq = min((r['seq'] for r in rows if r.get('type') == 'tool_request'), default=None)
    prior_before = []
    for r in rows:
        if first_tool_seq is not None and r.get('seq', 10**9) >= first_tool_seq: break
        if r.get('type') != 'client_note': continue
        try:
            ev = event_json(r)
            msg = ev.get('message', {}) if isinstance(ev, dict) else {}
            for block in msg.get('content', []) if isinstance(msg, dict) and isinstance(msg.get('content'), list) else []:
                if block.get('type') in {'text', 'output_text'} and '<prior_answer>' in block.get('text', ''):
                    prior_before.append(r['id'])
        except Exception: pass
    result['prior_answer'] = {'first_tool_seq': first_tool_seq, 'visible_prior_event_ids': prior_before,
                              'present_before_first_tool': bool(prior_before)}
    if first_tool_seq is not None and not prior_before: result['issues'].append('prior_answer_not_observed_before_first_tool')
    # Actual response provider model identifiers (metadata remains the requested alias).
    provider_models = set()
    for r in rows:
        if r.get('type') != 'client_note': continue
        try:
            ev = event_json(r)
            for obj in (ev, ev.get('message', {}) if isinstance(ev, dict) else {}):
                if isinstance(obj, dict):
                    if obj.get('model'): provider_models.add(str(obj['model']))
                    if isinstance(obj.get('providerData'), dict) and obj['providerData'].get('model'): provider_models.add(str(obj['providerData']['model']))
        except Exception: pass
    result['provider_models'] = sorted(provider_models)
    if not provider_models: result['warnings'].append('provider_model_not_observed')
    # Budget ledger is a client_note containing the raw temporary ledger.
    ledger_rows = []
    for r in rows:
        if r.get('type') != 'client_note': continue
        try:
            ev = event_json(r)
            raw = ev.get('budget_ledger') if isinstance(ev, dict) else None
            if raw:
                ledger_rows = [json.loads(x) for x in str(raw).splitlines() if x.strip()]
        except Exception: pass
    lim = limits(meta); allowed = {role: sum(bool(x.get('allowed')) and x.get('role') == role for x in ledger_rows) for role in ('search', 'fetch')}
    dispatched_count = {role: sum(1 for rid in dispatches if requests.get(rid, {}).get('role') == role) for role in ('search', 'fetch')}
    result['budget'] = {'limits': lim, 'ledger_allowed': allowed, 'dispatched': dispatched_count,
                        'allowed_within_limit': {r: (lim[r] is not None and allowed[r] <= lim[r]) for r in ('search', 'fetch')},
                        'dispatch_matches_ledger': {r: allowed[r] == dispatched_count[r] for r in ('search', 'fetch')}}
    if any(not x for x in result['budget']['allowed_within_limit'].values()): result['issues'].append('budget_allowed_exceeds_limit')
    if ledger_rows and any(not x for x in result['budget']['dispatch_matches_ledger'].values()): result['warnings'].append('dispatch_count_differs_from_ledger_allowed')
    if not ledger_rows and requests: result['issues'].append('budget_ledger_missing')
    if not requests: result['warnings'].append('no_tool_calls; ledger not created; M8 not automatically five')
    end = next((r for r in reversed(rows) if r.get('type') == 'run_end'), None)
    result['status'] = 'complete' if end else 'pending'
    if not end: result['issues'].append('missing_run_end')
    # Run log's built-in structural checker, without evaluating answer quality.
    try:
        sys.path.insert(0, str(skill_path)); from scripts import run_log
        result['log_check'] = run_log.check(run_dir)
        if result['log_check'].get('issues'): result['issues'].append('run_log_check_issues')
    except Exception as exc: result['issues'].append('run_log_check_error:' + repr(exc))
    # A live run is expected to lack its terminal ledger/result. Keep these visible,
    # but classify them as pending checks so completed-run quality issues remain clear.
    if result['status'] == 'pending':
        pending_codes = {'tool_request_result_correspondence', 'budget_ledger_missing',
                         'missing_run_end', 'run_log_check_issues'}
        result['pending_checks'] = [x for x in result['issues'] if x in pending_codes]
        result['issues'] = [x for x in result['issues'] if x not in pending_codes]
    # Search results only: preserve URL and exact character offsets; no rank claim.
    search_index = []
    for rid, req in requests.items():
        if req.get('role') != 'search' or rid not in results: continue
        text = unpack(results[rid].get('response', {}))
        for m in URL_RE.finditer(text):
            search_index.append({'run_id': meta.get('run_id'), 'task_id': meta.get('task_id'), 'ecosystem': meta.get('ecosystem'),
                                 'budget_arm': (meta.get('protocol') or {}).get('budget_arm'), 'request_event_id': rid,
                                 'result_event_id': results[rid].get('id'), 'url': m.group(0),
                                 'offset_start': m.start(), 'offset_end': m.end(), 'source': 'tool_result_text'})
    return result, search_index

def main():
    default_root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, default=default_root)
    p.add_argument('--protocol', type=Path, default=default_root / 'protocol.json')
    p.add_argument('--tasks', type=Path, default=default_root / 'tasks.json')
    p.add_argument('--skill', type=Path, default=default_root / 'frozen-skill')
    args = p.parse_args(); root = args.root.resolve(); rows = []; index = []
    for d in sorted((root / 'runs').glob('*')) if (root / 'runs').exists() else []:
        if d.is_dir():
            a, idx = run_audit(d, args.protocol.resolve(), args.tasks.resolve(), args.skill.resolve(), True); rows.append(a); index.extend(idx)
    # Include predeclared cells that have no directory yet; these are pending collection,
    # not failures. This keeps the audit denominator at the protocol's expected 48 cells.
    protocol = read_json(args.protocol.resolve())
    expected = []
    arms = protocol.get('budget_arms', protocol.get('budgets', {}))
    for task_id in list(protocol.get('development', [])) + list(protocol.get('heldout', [])):
        for ecosystem in protocol.get('ecosystems', []):
            for budget_arm in arms:
                expected.append((task_id, ecosystem.lower(), budget_arm))
    seen = {(x.get('task_id'), str(x.get('ecosystem', '')).lower(), x.get('budget_arm')) for x in rows}
    for task_id, ecosystem, budget_arm in expected:
        if (task_id, ecosystem, budget_arm) not in seen:
            rows.append({'run_dir': None, 'status': 'pending', 'task_id': task_id,
                         'ecosystem': ecosystem.upper(), 'budget_arm': budget_arm,
                         'issues': [], 'warnings': [], 'pending_checks': ['run_not_started']})
    dump(root / 'collection-audit.json', {'schema_version': 'collection-audit-1', 'runs': rows,
         'summary': {'total_seen': len(rows), 'complete': sum(x['status'] == 'complete' for x in rows),
                     'pending': sum(x['status'] == 'pending' for x in rows),
                     'completed_with_issues': sum(x['status'] == 'complete' and bool(x['issues']) for x in rows),
                     'pending_checks': sum(len(x.get('pending_checks', [])) for x in rows)}})
    dump(root / 'search-index.json', {'schema_version': 'search-index-1', 'entries': index,
         'note': 'URL character offsets refer to exact tool_result response text; no search ranking is inferred.'})
    print(json.dumps({'audited_runs': len(rows), 'complete': sum(x['status'] == 'complete' for x in rows), 'search_urls': len(index)}, ensure_ascii=False))
if __name__ == '__main__': main()
