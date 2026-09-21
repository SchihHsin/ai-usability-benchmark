"""Two supplementary post-assessment workers; same prompts and per-case locks."""
import concurrent.futures
import fcntl
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import assess_model  # Installs the identical fixed prompt and gate used by serial workers.
from assess_model import assess

R=Path(__file__).resolve().parent

def remaining(item,kind):
    files=list((R/'assessments/development').glob(item['case']+'-'+kind+'*.json'))
    values=[json.loads(f.read_text()) for f in files]
    if any(not v.get('error') for v in values):return False,False
    nonquota=0
    for v in values:
        raw=v.get('raw_stdout',[])
        raw=raw if isinstance(raw,list) else [raw]
        quota=any(isinstance(e,dict) and any(i.get('category')=='quota' or i.get('code')==14018 for i in e.get('errors_info',[]) if isinstance(i,dict)) for e in raw)
        nonquota+=not quota
    return nonquota<2,bool(files)


def work(pair):
    item,kind=pair
    locks=R/'.assessment-locks';locks.mkdir(exist_ok=True)
    with (locks/(item['case']+'-'+kind)).open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        allowed,overwrite=remaining(item,kind)
        if not allowed:return
        args=SimpleNamespace(timeout=900,overwrite=overwrite)
        print(json.dumps(assess.run_one(item,kind,args)),flush=True)


def main():
    for name,digest in json.loads((R/'freeze-manifest.json').read_text()).items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
    items=json.loads((R/'assessment-input/development.json').read_text())
    for item in items:
        for source in item['sources']:
            if source.get('status')=='not_dispatched':source['role']='blocked_request'
    pending=[(i,k) for i in items for k in ('predictors','outcome') if remaining(i,k)[0]]
    if '--dry-run' in sys.argv:
        print(json.dumps({'pending_before_locks':len(pending),'supplementary_workers':2}))
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(work,pending))

if __name__=='__main__':main()
