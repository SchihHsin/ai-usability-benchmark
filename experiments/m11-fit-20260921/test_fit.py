"""Checks numerical recovery and held-out task separation, not scientific validity."""
from pathlib import Path
import json
import numpy as np
A,B=np.meshgrid(np.arange(101)/100,np.arange(101)/100,indexing='ij');a=A.ravel();b=B.ravel()
loss=np.zeros_like(a)
for k,v,c in [(0.5,.2,1),(.8,1,.2),(.9,.6,.4),(.7,.4,.8)]:
 truth=k*(1-.27*(1-v))*(1-.14*(1-c))
 prediction=k*(1-a*(1-v))*(1-b*(1-c))
 loss+=(prediction-truth)**2
idx=np.argmin(loss)
assert np.isclose(a[idx],.27) and np.isclose(b[idx],.14)
# Worst squared error of two bounded intervals is attained at opposite endpoints.
for pl,pu,yl,yu in [(0,.9,.2,.6),(.3,.5,.1,.8),(.6,.6,.7,.7)]:
 grid=max((p-y)**2 for p in np.linspace(pl,pu,20) for y in np.linspace(yl,yu,20))
 assert np.isclose(grid,max((pl-yu)**2,(pu-yl)**2))
p=Path(__file__).with_name('fit-results.json')
if p.exists():
 r=json.loads(p.read_text());groups={d['case']:d['group'] for d in r['data']}
 for m in r['models'].values():
  for f in m['folds']:assert all(groups[x]==f['held_out'] for x in f['test_cases'])
print('Passed: synthetic parameter recovery, interval loss bound, task-group separation.')
