"""Fit fixed noisy-OR family to separate outcome assessments; grouped validation.
Run: uv run --with numpy python experiments/m11-fit-20260921/fit.py
"""
from pathlib import Path
import json,itertools,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
def load(p):return json.loads(p.read_text())
def arr(v):return [float(v),float(v)]
data=[];excluded=[]
for e in manifest:
 pp=ROOT/'reviewed'/f"{e['case']}-predictors.json";op=ROOT/'reviewed'/f"{e['case']}-outcome.json"
 if not pp.exists() or not op.exists():excluded.append({'case':e['case'],'reason':'assessment unavailable'});continue
 p,o=load(pp),load(op);ms={x['id']:x for x in p['metrics']};intervals=[];bad=[]
 for i in range(1,9):
  m=ms.get('M'+str(i),{});lo=m.get('lower');hi=m.get('upper');sc=m.get('score')
  if m.get('status')=='not_applicable':bad.append('M'+str(i)+' not applicable');continue
  if sc is not None:lo=hi=sc
  if lo is None or hi is None or not 1<=lo<=hi<=5:bad.append('M'+str(i)+' missing/invalid bounds');continue
  intervals.append([lo/5,hi/5])
 req=o['requirements'];ids=[x['id'] for x in req]
 if sorted(ids)!=list(range(1,7)):bad.append('six outcome requirements invalid')
 if bad:excluded.append({'case':e['case'],'reason':'; '.join(bad)});continue
 supp=sum(x['status']=='supported' for x in req);unk=sum(x['status']=='unverified' for x in req)
 assert all(x['status'] in ('supported','absent','contradicted','unverified') for x in req)
 # Sanity-check controller count, not evaluator arithmetic.
 cost=sum(e['counts'].values())
 expected=1 if cost>=9 else 2 if cost>=7 else 3 if cost>=5 else 4 if cost>=3 else 5 if cost>=1 else None
 assert ms['M8'].get('score')==expected,(e['case'],'M8 count mismatch')
 data.append({'case':e['case'],'group':e['task_group'],'protocol':e['protocol'],'input_intervals':intervals,'outcome_interval':[supp/6,(supp+unk)/6],'supported':supp,'unverified':unk})
if not data:raise RuntimeError('No usable assessments; do not fit fabricated data')
A,B=np.meshgrid(np.arange(101)/100,np.arange(101)/100,indexing='ij');aa=A.ravel();bb=B.ravel()
def k(xs):return 1-(1-xs[0]*xs[1]*xs[2])*(1-xs[4]*xs[5])*(1-xs[6])
pred=[];loss=[];optimistic=[]
for d in data:
 x=np.array(d['input_intervals']);kl=k(x[:,0]);ku=k(x[:,1]);vl,vu=x[3];cl,cu=x[7]
 low=kl*(1-aa*(1-vl))*(1-bb*(1-cl));high=ku*(1-aa*(1-vu))*(1-bb*(1-cu));yl,yu=d['outcome_interval']
 pred.append((low,high));loss.append(np.maximum((low-yu)**2,(high-yl)**2));optimistic.append(np.maximum(0,np.maximum(yl-high,low-yu))**2)
loss=np.array(loss);optimistic=np.array(optimistic);groups=sorted({d['group'] for d in data})
def avg(values,indices):
 gs=sorted({data[i]['group'] for i in indices})
 return np.mean([values[[i for i in indices if data[i]['group']==g]].mean(axis=0) for g in gs],axis=0)
def best(values,mask=None):
 mask=np.ones(len(aa),dtype=bool) if mask is None else mask
 idx=np.where(mask)[0];mn=values[idx].min();ties=idx[values[idx]<=mn+1e-12]
 chosen=min(ties,key=lambda i:(aa[i]+bb[i],aa[i],bb[i]));return chosen,ties
masks={'no_factors':(aa==0)&(bb==0),'version_only':bb==0,'cost_only':aa==0,'both':np.ones(len(aa),dtype=bool),'original':(aa==.3)&(bb==.1)}
indices=list(range(len(data)));full=avg(loss,indices);models={}
for name,mask in masks.items():
 idx,ties=best(full,mask);folds=[]
 for g in groups:
  train=[i for i in indices if data[i]['group']!=g];test=[i for i in indices if data[i]['group']==g]
  if not train:continue
  j,_=best(avg(loss,train),mask)
  folds.append({'held_out':g,'a':float(aa[j]),'b':float(bb[j]),'test_worst_case_mse':float(loss[test,j].mean()),'test_cases':[data[i]['case'] for i in test]})
 models[name]={'a':float(aa[idx]),'b':float(bb[idx]),'training_worst_case_mse':float(full[idx]),'folds':folds,'cv_worst_case_mse':float(np.mean([f['test_worst_case_mse'] for f in folds])) if folds else None,'exact_grid_minimizers':len(ties)}
# All task-group bootstrap resamples (3^3 for three groups), descriptive only.
boots=[]
if len(groups)<=5:
 for sample in itertools.product(groups,repeat=len(groups)):
  vals=np.mean([loss[[i for i in indices if data[i]['group']==g]].mean(axis=0) for g in sample],axis=0);idx,_=best(vals)
  boots.append({'sample':list(sample),'a':float(aa[idx]),'b':float(bb[idx])})
# Point fitting only for point-identified records, otherwise explicit null.
point=[i for i,d in enumerate(data) if all(l==h for l,h in d['input_intervals']) and d['outcome_interval'][0]==d['outcome_interval'][1]]
point_result=None
if point:
 idx,_=best(avg(loss,point));point_result={'n':len(point),'groups':sorted({data[i]['group'] for i in point}),'a':float(aa[idx]),'b':float(bb[idx]),'warning':'May have too few groups for generalisation'}
idx,ties=best(avg(optimistic,indices))
optimistic_result={'minimum_interval_distance_mse':float(avg(optimistic,indices)[idx]),'exact_grid_minimizers':len(ties),'a_range':[float(aa[ties].min()),float(aa[ties].max())],'b_range':[float(bb[ties].min()),float(bb[ties].max())]}
res={'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),'assessment_type':'automatic evidence-based assessment; not human gold labels; no hardware execution','n':len(data),'groups':groups,'excluded':excluded,'data':data,'models':models,'point_fit':point_result,'optimistic_interval_fit':optimistic_result,'task_bootstrap':boots,'scope':'Exploratory fitting with fixed formula, uncertain inputs/outcomes and three task groups. No claim of unique optimal coefficients.'}
(ROOT/'fit-results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in res.items() if k not in ('data','task_bootstrap')},ensure_ascii=False,indent=2))
