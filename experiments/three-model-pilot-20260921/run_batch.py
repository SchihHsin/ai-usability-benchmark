"""Fixed pilot order; resume completed cells without rerunning their scores."""
from pathlib import Path
from types import SimpleNamespace
import concurrent.futures,json
import runner
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text())
args=SimpleNamespace(root=R,protocol=R/'protocol.json',tasks=R/'tasks.json',skill=R/'frozen-skill',search_budget=None,fetch_budget=None,repetition=1)
jobs=[(t,e,m) for t in p['development'] for e in p['ecosystems'] for m in p['models']]
(R/'order.json').write_text(json.dumps(jobs,indent=2)+'\n')
def run(job):
 t,e,m=job
 return runner.one_run(args,t,e,'standard',m)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  list(pool.map(run,jobs))
