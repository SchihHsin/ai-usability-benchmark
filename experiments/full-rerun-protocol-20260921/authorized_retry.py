"""Explicitly authorized, bounded retries; keeps an independent attempt ledger."""
from pathlib import Path
from types import SimpleNamespace
import datetime as dt, hashlib, json, sys, fcntl
import runner
try:
    from completion_guard_closeout import errors as completion_errors
except ImportError:
    from completion_guard import errors as completion_errors

R = Path(__file__).resolve().parent
AUTH = R / "authorized-retry-20260921.json"
LOCK = R / "authorized-retry-20260921.lock"
AUTH_ID = "user-authorized-retry-20260921-U-CUDA-and-R-CUDA"

def frozen_hashes():
    manifest = json.loads((R/'freeze-manifest.json').read_text())
    got = {n: hashlib.sha256((R/n).read_bytes()).hexdigest() for n in manifest}
    return manifest, got

def state():
    LOCK.touch(exist_ok=True)
    with LOCK.open('r') as lf:
        fcntl.flock(lf, fcntl.LOCK_SH)
        if AUTH.exists():
            out = json.loads(AUTH.read_text())
        else:
            out = {'authorization_id': AUTH_ID, 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'attempts': []}
        fcntl.flock(lf, fcntl.LOCK_UN)
        return out

def save(s):
    LOCK.touch(exist_ok=True)
    with LOCK.open('r+') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        # Merge by (target, attempt) so concurrently running authorized targets
        # cannot overwrite one another's dispatch/final records.
        cur = json.loads(AUTH.read_text()) if AUTH.exists() else {'authorization_id': AUTH_ID, 'attempts': []}
        merged = {(x.get('target'), x.get('attempt')): x for x in cur.get('attempts', [])}
        for x in s.get('attempts', []): merged[(x.get('target'), x.get('attempt'))] = x
        out = dict(cur); out.update({k:v for k,v in s.items() if k not in ('attempts',)})
        out['attempts'] = list(merged.values())
        AUTH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
        fcntl.flock(lf, fcntl.LOCK_UN)

def run_target(model, task, ecosystem):
    if (model,task,ecosystem) not in {('glm-5.3','U','cuda'),('kimi-k3-2','U','cuda')}:
        raise ValueError('Collection authorization is limited to GLM/Kimi U-CUDA; DeepSeek R-CUDA is assessment only.')
    manifest, got = frozen_hashes()
    mismatches = [n for n in manifest if manifest[n] != got[n]]
    if mismatches:
        raise RuntimeError('freeze hash mismatch: '+','.join(mismatches))
    s = state(); s['freeze_check'] = {'entries': len(manifest), 'mismatches': [],
      'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
      'note': ''}
    save(s)
    key = f'{model}:{task}:{ecosystem}'
    prior = [x for x in s['attempts'] if x.get('target') == key]
    if any(x.get('status') == 'dispatching' for x in prior):
        raise SystemExit(f'authorized retry already dispatching: {key}')
    if any(x.get('completed') for x in prior):
        raise SystemExit(f'authorized retry already succeeded: {key}')
    if len(prior) >= 2:
        raise SystemExit(f'authorized retry cap reached: {key}')
    attempt = len(prior) + 1
    pre = {'authorization_id': AUTH_ID, 'target': key, 'model': model, 'task': task,
      'ecosystem': ecosystem, 'attempt': attempt, 'status': 'dispatching',
      'dispatch_persisted_at': dt.datetime.now(dt.timezone.utc).isoformat(),
      'freeze_mismatches': mismatches}
    s['attempts'].append(pre); save(s)
    args = SimpleNamespace(root=R, protocol=R/'protocol.json', tasks=R/'tasks.json',
                           skill=R/'frozen-skill', search_budget=None, fetch_budget=None, repetition=1)
    rid = runner.one_run(args, task, ecosystem, 'standard', model)
    ev = json.loads((R/'runs'/rid/'evaluation.json').read_text())
    ex = ev['revisions'][-1]['evaluation'].get('execution', {})
    check = json.loads((R/(rid+'-check.json')).read_text())
    errs = completion_errors(R/'runs'/rid)
    completed = ex.get('exit_code') == 0 and not ex.get('adapter_errors') and ex.get('stop_reason') == 'client_complete' and not check.get('issues') and bool(ex.get('models')) and not errs
    rec = {'authorization_id': AUTH_ID, 'authorized_retry': True, 'retry_attempt': attempt,
      'target': key, 'task': task, 'ecosystem': ecosystem, 'model': model, 'run_id': rid,
      'status': 'completed' if completed else 'failed',
      'completed': completed, 'stop_reason': ex.get('stop_reason'), 'check_issues': check.get('issues'),
      'completion_errors': errs, 'exit_code': ex.get('exit_code'), 'response_models': ex.get('models'),
      'adapter_errors': ex.get('adapter_errors'), 'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    s = state();
    for x in s['attempts']:
        if x.get('target') == key and x.get('attempt') == attempt: x.update(rec)
    save(s)
    with (R/f'ledger-{model}.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False)+'\n')
    return rec

if __name__ == '__main__':
    if len(sys.argv) != 4: raise SystemExit('usage: authorized_retry.py MODEL TASK ECOSYSTEM')
    print(json.dumps(run_target(sys.argv[1], sys.argv[2], sys.argv[3]), ensure_ascii=False), flush=True)
