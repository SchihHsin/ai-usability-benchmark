#!/usr/bin/env python3
"""统一批次 driver：固定顺序、两预算条件、断点续跑不覆盖既有运行。"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, json, random
from pathlib import Path
from types import SimpleNamespace
import runner

SEED = 20260921

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, value): Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def jobs_from(protocol):
    task_ids = list(protocol.get('development', [])) + list(protocol.get('heldout', []))
    ecosystems = list(protocol.get('ecosystems', []))
    arms = protocol.get('budget_arms', protocol.get('budgets', {}))
    jobs = [{'task_id': t, 'ecosystem': e, 'budget_name': b}
            for t in task_ids for e in ecosystems for b in arms]
    return jobs

def prepare(root, protocol_path):
    protocol = read(protocol_path)
    jobs = jobs_from(protocol)
    expected = int(protocol.get('expected_runs', len(jobs)))
    if len(jobs) != expected:
        raise SystemExit(f'协议 expected_runs={expected}，实际预声明作业={len(jobs)}，拒绝生成')
    random.Random(int(protocol.get('seed', SEED))).shuffle(jobs)
    payload = {'schema_version': 'uniform-fit-order-1', 'seed': int(protocol.get('seed', SEED)),
               'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'protocol_sha256': hashlib.sha256(Path(protocol_path).read_bytes()).hexdigest(),
               'jobs': jobs}
    write(root / 'order.json', payload)
    print(json.dumps({'prepared': True, 'path': str(root / 'order.json'), 'count': len(jobs),
                      'sha256': hashlib.sha256((root / 'order.json').read_bytes()).hexdigest()}, ensure_ascii=False))

def key(meta):
    return (meta.get('task_id'), str(meta.get('ecosystem', '')).lower(),
            (meta.get('protocol') or {}).get('budget_arm'))

def existing_keys(root):
    found = {}
    runs = root / 'runs'
    if not runs.exists(): return found
    for d in runs.iterdir():
        p = d / 'process.jsonl'
        if not p.is_file(): continue
        try:
            rows = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
            if rows and rows[0].get('type') == 'run_start':
                found.setdefault(key(rows[0].get('metadata', {})), str(d))
        except Exception:
            # Preserve unreadable directories as an operator-visible error; never overwrite them.
            found.setdefault(('unreadable', d.name, None), str(d))
    return found

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--protocol', type=Path, required=True); p.add_argument('--tasks', type=Path, required=True)
    p.add_argument('--skill', type=Path, required=True)
    p.add_argument('--prepare', action='store_true'); p.add_argument('--run', action='store_true')
    p.add_argument('--workers', type=int, default=2)
    args = p.parse_args(); root = args.root.resolve(); protocol_path = args.protocol.resolve()
    protocol = read(protocol_path)
    if args.prepare:
        prepare(root, protocol_path)
    if not args.run: return
    if protocol.get('status') != 'frozen':
        raise SystemExit('protocol.status 必须为 frozen 才允许启动批次')
    order_path = root / 'order.json'
    if not order_path.exists(): raise SystemExit('缺少预生成 order.json；先执行 --prepare，再冻结协议')
    order = read(order_path); expected = jobs_from(protocol)
    expected_set = {(j['task_id'], j['ecosystem'], j['budget_name']) for j in expected}
    actual_set = {(j['task_id'], j['ecosystem'], j['budget_name']) for j in order.get('jobs', [])}
    if actual_set != expected_set or len(order.get('jobs', [])) != len(expected_set):
        raise SystemExit('order.json 与当前冻结 protocol 作业集合不一致，拒绝启动')
    if order.get('protocol_sha256') != hashlib.sha256(protocol_path.read_bytes()).hexdigest():
        raise SystemExit('order.json 对应的 protocol 哈希不一致，拒绝启动')
    existing = existing_keys(root)
    todo = []
    for job in order['jobs']:
        k = (job['task_id'], job['ecosystem'], job['budget_name'])
        if k in existing:
            print(json.dumps({'skip_existing': job, 'run_dir': existing[k]}, ensure_ascii=False), flush=True)
        else: todo.append(job)
    common = SimpleNamespace(root=root, protocol=args.protocol, tasks=args.tasks, skill=args.skill,
                             repetition=1, search_budget=None, fetch_budget=None)
    def execute(job):
        return runner.one_run(common, job['task_id'], job['ecosystem'], job['budget_name'],
                              protocol.get('generator_model', 'deepseek-v4.1-flash'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(args.workers, 1), 2)) as pool:
        for result in pool.map(execute, todo): print(json.dumps({'finished': result}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
