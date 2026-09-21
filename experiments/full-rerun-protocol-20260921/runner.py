#!/usr/bin/env python3
"""参数化的 WorkBuddy 统一重跑器。

本脚本只读取外部 protocol.json、tasks.json 和冻结 Skill，不改写它们，也不读上一轮拟合结果。
每个运行目录只保留 process.jsonl 与 evaluation.json；调试错误、预算账本和完整工具返回均通过
client_note/tool_result 写入 process.jsonl。reasoning/thinking 字段在写入前剥离。
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, json, os, queue, re
from pathlib import Path
import shutil, subprocess, sys, tempfile, threading, time

CLI = '/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy'
MODEL_ALIASES = {
    'deepseek': 'deepseek-v4.1-flash',
    'glm': 'glm-5.3',
    'kimi': 'kimi-k3-2',
    'luna': 'gpt-5.6-luna',
    'gpt-5.6-luna': 'gpt-5.6-luna',
}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def dump_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def json_obj(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def clean(value):
    """删去客户端的隐藏思维字段，但保留工具返回、可见答案及模型标识。"""
    if isinstance(value, list):
        return [clean(v) for v in value if not (isinstance(v, dict) and
                v.get('type') in {'thinking', 'reasoning', 'reasoning_text', 'redacted_thinking'})]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()
                if k not in {'thinking', 'reasoning_content', 'rawContent', 'signature'}}
    return value

def text_content(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(str(x.get('text', '')) for x in value
                         if isinstance(x, dict) and x.get('type') in {'text', 'output_text'})
    if isinstance(value, dict):
        return str(value.get('text', value.get('content', '')))
    return str(value)

def tool_role(name: str) -> str:
    return {'WebSearch': 'search', 'WebFetch': 'fetch',
            'web_search': 'search', 'web_fetch': 'fetch'}.get(name, 'other')

def normalize_model(requested: str) -> str:
    return MODEL_ALIASES.get(requested, requested)

def load_task(tasks, task_id: str, ecosystem: str) -> str:
    if isinstance(tasks, dict) and isinstance(tasks.get('tasks'), dict):
        tasks = tasks['tasks']
    entry = tasks[task_id] if isinstance(tasks, dict) else next(x for x in tasks if x.get('id') == task_id)
    if isinstance(entry, dict):
        for key in (ecosystem, ecosystem.lower(), ecosystem.upper()):
            if key in entry:
                return str(entry[key])
        raise KeyError(f'任务 {task_id} 没有生态 {ecosystem}')
    raise TypeError('tasks.json 任务必须是映射')

def resolve_budget(protocol: dict, name: str | None, search: int | None, fetch: int | None):
    if name:
        arms = protocol.get('budgets', protocol.get('budget_arms', {}))
        arm = arms.get(name) if isinstance(arms, dict) else None
        if arm is None:
            raise ValueError(f'protocol.json 未定义预算条件 {name}')
        search = arm.get('search', arm.get('search_budget', arm.get('search_limit')))
        fetch = arm.get('fetch', arm.get('fetch_budget', arm.get('fetch_limit')))
    if search is None: search = protocol.get('search_budget')
    if fetch is None: fetch = protocol.get('fetch_budget')
    if type(search) is not int or type(fetch) is not int or search < 0 or fetch < 0:
        raise ValueError('搜索/获取预算必须是非负整数')
    return {'search': search, 'fetch': fetch}

def active_skill_files(skill: Path, protocol: dict):
    names = protocol.get('active_skill_files') or protocol.get('skill_files')
    if names is None:
        names = ['SKILL.md'] + [str(p.relative_to(skill)) for p in sorted((skill / 'references').glob('*.md'))]
    files = []
    for name in names:
        p = skill / name
        if not p.is_file(): raise FileNotFoundError(f'冻结 Skill 缺少 {name}')
        files.append((str(name), p))
    return files

def all_skill_hashes(skill: Path):
    return {str(p.relative_to(skill)): sha256_file(p)
            for p in sorted(skill.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def verify_skill_manifest(skill: Path):
    """冻结副本自带 manifest 时逐文件核对；缺失或不一致直接阻止运行。"""
    manifest_path = skill / 'manifest.json'
    actual = all_skill_hashes(skill)
    if not manifest_path.exists():
        return actual, {'manifest_present': False, 'mismatches': []}
    declared = json_obj(manifest_path)
    declared = declared.get('files', declared) if isinstance(declared, dict) else {}
    # manifest.json normally lists the other frozen files and cannot contain its own hash.
    comparable = {k: v for k, v in actual.items() if k != 'manifest.json'}
    mismatches = [{'path': name, 'declared': declared.get(name), 'actual': comparable.get(name)}
                  for name in sorted(set(declared) | set(comparable)) if declared.get(name) != comparable.get(name)]
    if mismatches:
        raise ValueError('冻结 Skill manifest 哈希不一致: ' + json.dumps(mismatches, ensure_ascii=False))
    return actual, {'manifest_present': True, 'mismatches': []}

def make_prompt(question: str, ecosystem: str, files, protocol: dict, budget: dict, model_label: str):
    text = f"""你正在参加一项预先定义的开发者知识可用性实验。\n\n实际任务（原文）：\n{question}\n\n生态：{ecosystem}\n请求的模型别名：{model_label}\n工具限制：只能使用 WebSearch 和 WebFetch；每次只发一个搜索查询；最多 WebSearch {budget['search']} 次、WebFetch {budget['fetch']} 次。超出请求会被调度器拒绝。\n\n请严格执行下面冻结的 Skill。工具调用前先输出完整的 <prior_answer>，说明仅凭已有知识可以怎样回答以及不确定处；工具调用后在 <answer> 中给出完整最终答案，并用 <stop_reason> 说明实际停止原因。请保留命令、代码、参数、来源 URL 与无法核实处。不要自报分数、哈希、预算账本或过程文件；调度器会记录这些事实。不要执行本地代码、调用其他模型或子 Agent。\n\n这是一次统一协议下的研究运行；不要读取其他运行、旧答案或拟合系数。\n"""
    for name, path in files:
        text += f"\n--- FROZEN SKILL FILE: {name} ---\n{path.read_text(encoding='utf-8')}\n"
    return text

class Adapter:
    def __init__(self, dest: Path, scratch: Path, log, budget_state: Path):
        self.dest, self.scratch, self.log = dest, scratch, log
        self.budget_state = budget_state
        self.requests, self.responses = {}, set()
        self.texts, self.prior_texts, self.models, self.errors = [], [], set(), []
        self.first_tool_id = None
        self.result = None
        self.event_number = 0

    def report(self, value, kind='client_note'):
        self.event_number += 1
        p = self.scratch / f'client-note-{self.event_number:05}.txt'
        p.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), encoding='utf-8')
        self.log.report(self.dest, f'client-note-{self.event_number:05}', p, kind)

    def _message_content(self, event):
        msg = event.get('message') if isinstance(event.get('message'), dict) else {}
        return msg.get('content', event.get('content', []))

    def consume(self, raw):
        event = clean(raw)
        self.report(event)
        typ = event.get('type')
        if event.get('model'): self.models.add(str(event['model']))
        if isinstance(event.get('providerData'), dict) and event['providerData'].get('model'):
            self.models.add(str(event['providerData']['model']))
        msg = event.get('message') if isinstance(event.get('message'), dict) else {}
        if msg.get('model'): self.models.add(str(msg['model']))
        if isinstance(msg.get('providerData'), dict) and msg['providerData'].get('model'):
            self.models.add(str(msg['providerData']['model']))
        if typ == 'result': self.result = event
        content = self._message_content(event)
        blocks = content if isinstance(content, list) else []
        for block in blocks:
            if not isinstance(block, dict): continue
            btyp = block.get('type')
            if typ == 'assistant' and btyp in {'text', 'output_text'}:
                self.texts.append(str(block.get('text', '')))
                if not self.requests:
                    self.prior_texts.append(str(block.get('text', '')))
            if btyp == 'tool_use':
                ident = block.get('id')
                name = block.get('name')
                if not ident or ident in self.requests: continue
                self.requests[ident] = block
                if self.first_tool_id is None: self.first_tool_id = ident
                self.log.begin(self.dest, ident, tool_role(name), name, block.get('input', {}))
            if btyp == 'tool_result':
                self._finish_result(block, event)
        # Some client versions emit tool_result as a top-level event.
        if typ in {'tool_result', 'tool'} and event.get('tool_use_id'):
            self._finish_result(event, event)

    def _finish_result(self, block, event):
        ident = block.get('tool_use_id') or block.get('id')
        if not ident or ident in self.responses: return
        req = self.requests.get(ident)
        if req is None:
            self.errors.append(f'result_without_request:{ident}')
            self.report({'unmatched_tool_result': block})
            return
        body = block.get('content', block.get('result', ''))
        body_text = text_content(body)
        denied = False
        try:
            from scripts.budget_hook import rejection_for
            denied = rejection_for(self.budget_state, ident) is not None
        except Exception as exc:
            self.errors.append('budget_rejection_lookup:' + repr(exc))
        if not denied:
            self.log.dispatch(self.dest, ident)
        payload = self.scratch / f'tool-{len(self.responses)+1:05}.txt'
        payload.write_text(body_text, encoding='utf-8')
        self.log.finish(self.dest, ident, payload,
                        'not_dispatched' if denied else ('error' if block.get('is_error') else 'ok'),
                        {'client_timestamp': event.get('__timestamp'),
                         'original_blocks': body,
                         'client_tool_meta': block.get('_meta', {}),
                         'dispatch_evidence': ('hook refusal matched tool_use_id' if denied
                                               else 'matched tool result; exact dispatch time not exposed'),
                         'representation': 'model_visible_text; raw HTML availability follows tool return'})
        self.responses.add(ident)

def one_run(args, task_id, ecosystem, budget_name, model_arg):
    root = Path(args.root).resolve(); protocol_path = Path(args.protocol).resolve()
    tasks_path = Path(args.tasks).resolve(); skill = Path(args.skill).resolve()
    protocol = json_obj(protocol_path); tasks = json_obj(tasks_path)
    if protocol.get('status') != 'frozen': raise ValueError('protocol must be frozen before execution')
    budget = resolve_budget(protocol, budget_name, args.search_budget, args.fetch_budget)
    model = normalize_model(model_arg or protocol.get('generator_model', protocol.get('model', 'deepseek-v4.1-flash')))
    q = load_task(tasks, task_id, ecosystem)
    scope = tasks['tasks'][task_id]['applicability'][ecosystem]
    files = active_skill_files(skill, protocol)
    full_skill_hashes, manifest_check = verify_skill_manifest(skill)
    timestamp = dt.datetime.now().strftime('%Y%m%dT%H%M%S')
    safeeco = re.sub(r'[^A-Za-z0-9_-]+', '_', ecosystem.lower())
    rid = f'{task_id}-{safeeco}-{model.replace(".", "_")}-{budget_name or "budget"}-{timestamp}'
    dest = root / 'runs' / rid
    with tempfile.TemporaryDirectory(prefix='uniform-fit-') as temp:
        scratch = Path(temp); cwd = scratch / 'workspace'; cwd.mkdir()
        question = scratch / 'question.txt'; question.write_text(q, encoding='utf-8')
        budget_state = scratch / 'budget.jsonl'
        prompt = make_prompt(q, ecosystem, files, protocol, budget, model_arg or model) + "\n本任务预先固定的评价范围（不得增加题外要求）：\n" + json.dumps(scope, ensure_ascii=False)
        from importlib import util
        sys.path.insert(0, str(skill))
        from scripts import run_log as log
        from scripts.budget_hook import workbuddy_settings
        skill_hashes = {name: sha256_file(path) for name, path in files}
        metadata = {
            'run_id': rid, 'task_id': task_id, 'ecosystem': ecosystem.upper(), 'model_id': model,
            'repetition': int(args.repetition), 'protocol_version': str(protocol.get('protocol_version', 'unspecified')),
            'rubric_version': str(protocol.get('rubric_version', 'unspecified')),
            'protocol': {**protocol, 'budget_arm': budget_name, 'search_budget': budget['search'], 'fetch_budget': budget['fetch']},
            'question_sha256': sha256_bytes(q.encode()), 'protocol_sha256': sha256_file(protocol_path),
            'tasks_sha256': sha256_file(tasks_path), 'skill_root': str(skill),
            'skill_hashes': full_skill_hashes, 'active_skill_hashes': skill_hashes,
            'skill_manifest_check': manifest_check,
            'model_identity_basis': 'requested CLI alias plus response event provider model; aliases are not immutable snapshots',
            'visible_prompt': prompt, 'active_skill_files': [x[0] for x in files],
        }
        log.init_run(dest, metadata, question)
        settings = {'permissions': {'allow': ['WebSearch', 'WebFetch'], 'defaultMode': 'default'}}
        settings.update(workbuddy_settings(budget_state, budget['search'], budget['fetch']))
        cmd = ['node', CLI, '--print', '--model', model, '--agent', 'cli', '--tools', 'WebSearch,WebFetch',
               '--settings', json.dumps(settings, ensure_ascii=False), '--strict-mcp-config', '--mcp-config',
               '{"mcpServers":{}}', '--permission-mode', 'default', '--session-id', rid,
               '--effort', str(protocol.get('generator_effort', 'low')),
               '--max-turns', str(protocol.get('max_turns', 22)), '--output-format', 'stream-json', '--verbose']
        log.append(dest, {'id': 'runner-command', 'type': 'client_note',
                          'content': log.pack(json.dumps({'command': cmd, 'model_requested': model}, ensure_ascii=False).encode())})
        env = os.environ.copy(); env.update({
            'CODEBUDDY_CONFIG_DIR': '/Users/hsin/.workbuddy', 'CODEBUDDY_DISABLE_AUTO_MEMORY': '1',
            'CODEBUDDY_CODE_DISABLE_AUTO_MEMORY': '1', 'CODEBUDDY_MEMORY_ENABLED': '0',
            'CODEBUDDY_TEAM_MEMORY_ENABLED': '0', 'CODEBUDDY_TYPED_MEMORY_ENABLED': '0'})
        adapter = Adapter(dest, scratch, log, budget_state)
        stderr_path = scratch / 'stderr.txt'; reason = 'client_complete'; code = None
        started = time.monotonic()
        try:
            with stderr_path.open('w', encoding='utf-8') as err:
                proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=err, text=True)
                assert proc.stdin is not None and proc.stdout is not None
                proc.stdin.write(prompt); proc.stdin.close()
                lines = queue.Queue()
                def pump():
                    for line in proc.stdout: lines.put(line)
                    lines.put(None)
                threading.Thread(target=pump, daemon=True).start()
                limit = int(protocol.get('timeout_seconds', 600))
                while True:
                    if time.monotonic() - started > limit:
                        reason = 'controller_timeout'; proc.terminate(); break
                    try: line = lines.get(timeout=1)
                    except queue.Empty: continue
                    if line is None: break
                    try: event = json.loads(line)
                    except json.JSONDecodeError:
                        adapter.report({'unparsed_client_output': line}); continue
                    adapter.consume(event)
                try: code = proc.wait(timeout=15)
                except subprocess.TimeoutExpired: proc.kill(); code = proc.wait(); reason = 'client_kill_after_timeout'
        except Exception as exc:
            reason = 'runner_error'; adapter.errors.append(repr(exc))
            if 'proc' in locals():
                try: proc.terminate()
                except Exception: pass
        adapter.report({'prior_answer_before_first_tool': '\n'.join(adapter.prior_texts),
                        'first_tool_request_id': adapter.first_tool_id,
                        'first_tool_observed': adapter.first_tool_id is not None}, 'client_note')
        stderr = stderr_path.read_text(encoding='utf-8', errors='replace') if stderr_path.exists() else ''
        adapter.report({'client_exit_code': code, 'response_models': sorted(adapter.models),
                        'adapter_errors': adapter.errors, 'stderr': stderr,
                        'filtered_client_events': adapter.event_number,
                        'elapsed_seconds': round(time.monotonic() - started, 2)})
        if budget_state.exists():
            adapter.report({'budget_ledger': budget_state.read_text(encoding='utf-8')})
        final = adapter.result.get('result', '') if adapter.result else '\n'.join(adapter.texts)
        answer = scratch / 'answer.txt'; answer.write_text(str(final), encoding='utf-8')
        if adapter.result and adapter.result.get('is_error'): reason = 'client_error'
        log.end_run(dest, answer, reason)
        value = log.metric_template(log.events(dest))
        value['rubric_version'] = metadata['rubric_version']
        value['assessor'] = {'id': 'post-run-required', 'method': 'automatic_template_pending_review'}
        value['limitations'] = ['运行完成后须按冻结规则独立后评；本运行器不计算正式分数。']
        value['execution'] = {'exit_code': code, 'models': sorted(adapter.models), 'adapter_errors': adapter.errors,
                              'requests': len(adapter.requests), 'returned_results': len(adapter.responses),
                              'budget': budget, 'model_requested': model}
        log.save_evaluation(dest, value)
        check = log.check(dest)
        dump_json(root / f'{rid}-check.json', check)
        print(json.dumps({'finished': rid, 'check': check}, ensure_ascii=False), flush=True)
    return rid

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default=Path(__file__).resolve().parent, type=Path)
    p.add_argument('--protocol', required=True, type=Path); p.add_argument('--tasks', required=True, type=Path)
    p.add_argument('--skill', required=True, type=Path)
    p.add_argument('--task', action='append', dest='tasks_to_run', required=True)
    p.add_argument('--ecosystem', action='append', required=True)
    p.add_argument('--budget-name'); p.add_argument('--search-budget', type=int); p.add_argument('--fetch-budget', type=int)
    p.add_argument('--model'); p.add_argument('--repetition', type=int, default=1); p.add_argument('--workers', type=int, default=1)
    p.add_argument('--dry-run', action='store_true', help='只校验外部输入并打印作业，不启动 WorkBuddy')
    args = p.parse_args()
    jobs = [(t, e) for t in args.tasks_to_run for e in args.ecosystem]
    if args.dry_run:
        protocol = json_obj(Path(args.protocol)); tasks = json_obj(Path(args.tasks)); skill = Path(args.skill).resolve()
        budget = resolve_budget(protocol, args.budget_name, args.search_budget, args.fetch_budget)
        files = active_skill_files(skill, protocol)
        for task_id, eco in jobs:
            load_task(tasks, task_id, eco)
        print(json.dumps({'dry_run': True, 'jobs': jobs, 'budget': budget,
                          'model': normalize_model(args.model or protocol.get('generator_model', 'deepseek-v4.1-flash')),
                          'skill_files': [n for n, _ in files],
                          'protocol_status': protocol.get('status')}, ensure_ascii=False, indent=2))
        return
    if args.workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(lambda x: one_run(args, x[0], x[1], args.budget_name, args.model), jobs))
    else:
        for task_id, eco in jobs: one_run(args, task_id, eco, args.budget_name, args.model)

if __name__ == '__main__': main()
