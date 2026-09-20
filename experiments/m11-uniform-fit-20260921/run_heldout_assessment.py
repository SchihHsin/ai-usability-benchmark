"""Frozen-selection-gated assessment; same three bounded technical attempts as development."""
from pathlib import Path
from types import SimpleNamespace
import concurrent.futures,json
import assess
ROOT=Path(__file__).resolve().parent

def run(job):
    item,kind=job
    results=[]
    for path in sorted((ROOT/'assessments/heldout').glob(f"{item['case']}-{kind}*.json")):
        d=json.loads(path.read_text())
        ids=[x.get('id') for x in d.get('metrics' if kind=='predictors' else 'requirements',[])]
        if not d.get('error') and ids==([f'M{i}' for i in range(1,9)] if kind=='predictors' else list(range(1,7))):
            return {'case':item['case'],'kind':kind,'status':'cached_valid'}
    for timeout in (300,300,600):
        result=assess.run_one(item,kind,SimpleNamespace(overwrite=True,timeout=timeout))
        results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        if result['status'] in ('done','cached','skipped'):break
    return {'case':item['case'],'kind':kind,'attempts':results}

def main():
    if not (ROOT/'frozen-selection.json').exists():raise SystemExit('freeze development selection first')
    data=json.loads((ROOT/'assessment-input/heldout.json').read_text())
    jobs=[(item,kind) for item in data for kind in ('predictors','outcome')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(run,jobs))
    (ROOT/'heldout-assessment-queue-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
