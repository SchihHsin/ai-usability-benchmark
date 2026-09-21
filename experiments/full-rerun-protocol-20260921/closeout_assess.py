"""Targeted assessment only. Explicit authorization, immutable raw attempts, first success."""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib,fcntl,concurrent.futures,datetime
import assess_model
R=Path(__file__).resolve().parent
TARGET_OLD='case-462457829d9f'
def one(item,kind):
 key=item['case']+'-'+kind;log=R/('closeout-assessment-'+key+'.json');lock=R/'.assessment-locks'/key
 with lock.open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  saved=json.loads(log.read_text()) if log.exists() else {'case':item['case'],'kind':kind,'run_id':item['run_name'],'authorization':'User grants at most two additional attempts for DeepSeek R-CUDA predictors; ordinary two attempts for newly collected U-CUDA assessments.','attempts':[]}
  for _ in range(2):
   for name,h in json.load(open(R/'freeze-manifest.json')).items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
   files=list((R/'assessments/development').glob(key+'*.json'))
   if any(not json.loads(p.read_text()).get('error') for p in files):return
   if len(saved['attempts'])>=2:return
   a={'number':len(saved['attempts'])+1,'status':'dispatching','time':datetime.datetime.now().isoformat()};saved['attempts'].append(a);log.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n')
   status=assess_model.assess.run_one(item,kind,SimpleNamespace(timeout=900,overwrite=bool(files)))
   a.update(status='returned',result=status);log.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'target':key,**status}),flush=True)
def main():
 items=json.load(open(R/'assessment-input/development.json'));jobs=[]
 for i in items:
  if i['case']==TARGET_OLD:jobs.append((i,'predictors'))
  elif i['task_id']=='U' and i['ecosystem']=='cuda' and ('T222641' in i['run_name'] or (i['run_name'].startswith('U-cuda-kimi') and 'T133844' not in i['run_name'])):jobs.extend((i,k) for k in ['predictors','outcome'])
 for i,k in jobs:
  for s in i['sources']:
   if s.get('status')=='not_dispatched':s['role']='blocked_request'
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda j:one(*j),jobs))
if __name__=='__main__':main()
