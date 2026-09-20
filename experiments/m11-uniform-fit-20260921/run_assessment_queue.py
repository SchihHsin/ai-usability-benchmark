"""Assess completed development runs while collection continues; bounded retries."""
from pathlib import Path
import concurrent.futures,json,time,traceback,signal
from types import SimpleNamespace
import assess,prepare_assessment as prep
ROOT=Path(__file__).resolve().parent
protocol=json.loads((ROOT/'protocol.json').read_text());tasks=json.loads((ROOT/'tasks.json').read_text())['tasks']
expected=len(protocol['development'])*len(protocol['ecosystems'])*len(protocol['budget_arms'])

def valid(case,kind):
    for p in (ROOT/'assessments/development').glob(f'{case}-{kind}*.json'):
        try:
            d=json.loads(p.read_text());ids=[x.get('id') for x in d.get('metrics' if kind=='predictors' else 'requirements',[])]
            if not d.get('error') and ids==([f'M{i}' for i in range(1,9)] if kind=='predictors' else list(range(1,7))):return True
        except Exception:pass
    return False

def main():
    stopping=[False]
    signal.signal(signal.SIGINT,lambda *_:stopping.__setitem__(0,True))
    running={};tried={};terminal=set();pool=concurrent.futures.ThreadPoolExecutor(max_workers=4)
    while True:
        items={}
        for path in (ROOT/'runs').glob('*/process.jsonl'):
            try:
                first=json.loads(path.open().readline())
                if first['metadata']['task_id'] not in protocol['development']:continue
                item=prep.parse_run(path,tasks,protocol);items[item['case']]=item
            except (ValueError,json.JSONDecodeError):continue
        for future,key in list(running.items()):
            if future.done():
                try: result=future.result();print(json.dumps(result,ensure_ascii=False),flush=True)
                except Exception as error:print(json.dumps({'key':key,'queue_error':repr(error)},ensure_ascii=False),flush=True)
                del running[future]
                if valid(*key) or tried[key]>=2:terminal.add(key)
        jobs=[(case,kind) for case in sorted(items) for kind in ('predictors','outcome')]
        for key in jobs:
            if valid(*key):terminal.add(key);continue
            if stopping[0] or key in terminal or key in running.values() or len(running)>=4:continue
            tried[key]=tried.get(key,0)+1
            future=pool.submit(assess.run_one,items[key[0]],key[1],SimpleNamespace(overwrite=True,timeout=300))
            running[future]=key;print(json.dumps({'assessing':key,'queue_attempt':tried[key]},ensure_ascii=False),flush=True)
        if stopping[0] and not running:
            pool.shutdown();print('QUEUE DRAINED',flush=True);return
        if len(items)==expected and all(key in terminal for key in jobs) and not running:break
        time.sleep(5)
    pool.shutdown()
    (ROOT/'assessment-queue-summary.json').write_text(json.dumps({'expected_development_runs':expected,'completed_development_runs':len(items),'new_attempts':{':'.join(k):v for k,v in tried.items()},'valid_pairs':sum(valid(c,k) for c,k in jobs),'failed_pairs':[list(key) for key in jobs if not valid(*key)]},ensure_ascii=False,indent=2)+'\n')
    print('DEVELOPMENT ASSESSMENT QUEUE FINISHED',flush=True)
if __name__=='__main__':main()
