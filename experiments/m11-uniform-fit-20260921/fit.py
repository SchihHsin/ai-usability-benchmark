#!/usr/bin/env python3
"""Uniform-grid fit for the prospectively specified M11 noisy-OR model.

Selection uses development rows only.  ``--validate`` consumes the frozen
selection and evaluates held-out rows without searching or changing it.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
FAMILIES = ("no_factors", "version_only", "cost_only", "both", "original")

def read_rows(path):
    obj = json.loads(Path(path).read_text())
    if not isinstance(obj, list): raise ValueError(f"{path} must contain a JSON array")
    out=[]; cases=set(); case_groups={}
    for r in obj:
        if not isinstance(r,dict) or not all(k in r for k in ("case","group","input_intervals","outcome_interval")):
            raise ValueError("each row needs case, group, input_intervals, outcome_interval")
        xs=np.asarray(r["input_intervals"],dtype=float)
        y=np.asarray(r["outcome_interval"],dtype=float)
        if xs.shape!=(8,2) or y.shape!=(2,) or np.any(xs[:,0]>xs[:,1]) or np.any(y[0]>y[1]): raise ValueError(f"invalid intervals: {r.get('case')}")
        if np.any(xs<1) or np.any(xs>5) or np.any(y<0) or np.any(y>1): raise ValueError(f"interval bounds out of range: {r.get('case')}")
        if not np.all(np.isfinite(xs)) or not np.all(np.isfinite(y)): raise ValueError(f"non-finite bounds: {r.get('case')}")
        if r['case'] in cases: raise ValueError(f"duplicate case: {r['case']}")
        cases.add(r['case']); case_groups[r['case']]=r['group']
        out.append({**r,"input_intervals":xs.tolist(),"outcome_interval":y.tolist()})
    return out

def split_inputs(args):
    dev_path=args.development_data or str(ROOT/'development-data.json')
    dev=read_rows(dev_path)
    if any(r.get('split') not in (None,'development') for r in dev): raise ValueError('development-data contains non-development split')
    if not args.validate: return dev,[],"development-only"
    ho_path=args.heldout_data or str(ROOT/'heldout-data.json')
    ho=read_rows(ho_path)
    if any(r.get('split') not in (None,'heldout','holdout') for r in ho): raise ValueError('heldout-data contains non-heldout split')
    overlap={r['case'] for r in dev}&{r['case'] for r in ho}
    if overlap: raise ValueError(f"case appears in both development and heldout: {sorted(overlap)}")
    dg={r['group'] for r in dev}; hg={r['group'] for r in ho}
    if dg&hg: raise ValueError(f"group appears in both development and heldout: {sorted(dg&hg)}")
    return dev,ho,"separate"

def grid():
    a=np.repeat(np.arange(101)/100,101); b=np.tile(np.arange(101)/100,101); return a,b

def predict(rows,a,b):
    vals=[]
    for r in rows:
        x=np.asarray(r["input_intervals"],float)/5
        kl=1-(1-x[0,0]*x[1,0]*x[2,0])*(1-x[4,0]*x[5,0])*(1-x[6,0]); ku=1-(1-np.prod(x[[0,1,2],1]))*(1-x[4,1]*x[5,1])*(1-x[6,1])
        pl=kl*(1-a*(1-x[3,0]))*(1-b*(1-x[7,0])); pu=ku*(1-a*(1-x[3,1]))*(1-b*(1-x[7,1]))
        vals.append((pl,pu))
    return np.asarray(vals)

def row_loss(rows,a,b):
    p=predict(rows,a,b); l=np.asarray([r["outcome_interval"] for r in rows],float)
    # Worst squared endpoint error over the two uncertain intervals.
    return np.max((p[:,:,None]-l[:,None,:])**2,axis=(1,2))

def interval_distance_loss(rows,a,b):
    """Descriptive alternative: squared gap between predicted and observed intervals."""
    p=predict(rows,a,b); y=np.asarray([r['outcome_interval'] for r in rows],float)
    gap=np.maximum(y[:,0]-p[:,1],0)+np.maximum(p[:,0]-y[:,1],0)
    return gap**2

def group_mean(rows, losses):
    gs=sorted({r["group"] for r in rows})
    return float(np.mean([np.mean([losses[i] for i,r in enumerate(rows) if r["group"]==g]) for g in gs]))

def family_mask(name,a,b):
    if name=="no_factors": return (a==0)&(b==0)
    if name=="version_only": return b==0
    if name=="cost_only": return a==0
    if name=="original": return (a==.3)&(b==.1)
    return np.ones(a.shape,dtype=bool)

def choose(rows,name):
    a,b=grid(); x=np.asarray([r['input_intervals'] for r in rows],float)/5; y=np.asarray([r['outcome_interval'] for r in rows],float)
    kl=1-(1-x[:,0,0]*x[:,1,0]*x[:,2,0])*(1-x[:,4,0]*x[:,5,0])*(1-x[:,6,0]); ku=1-(1-x[:,0,1]*x[:,1,1]*x[:,2,1])*(1-x[:,4,1]*x[:,5,1])*(1-x[:,6,1])
    pl=kl[None,:]*(1-a[:,None]*(1-x[:,3,0][None,:]))*(1-b[:,None]*(1-x[:,7,0][None,:])); pu=ku[None,:]*(1-a[:,None]*(1-x[:,3,1][None,:]))*(1-b[:,None]*(1-x[:,7,1][None,:]))
    losses=np.max(np.stack([(pl-y[:,0][None,:])**2,(pl-y[:,1][None,:])**2,(pu-y[:,0][None,:])**2,(pu-y[:,1][None,:])**2]),axis=0).T
    scores=np.asarray([group_mean(rows,losses[:,j]) for j in range(len(a))]); mask=family_mask(name,a,b); cand=np.where(mask)[0]; best=scores[cand].min(); ties=cand[scores[cand]<=best+1e-12]
    j=min(ties,key=lambda i:(a[i]+b[i],a[i],b[i]))
    return {"a":float(a[j]),"b":float(b[j]),"training_worst_case_mse":float(scores[j]),"exact_grid_minimizers":int(len(ties))}

def select_family(dev):
    groups=sorted({r["group"] for r in dev}); folds={}; cv={}
    for fam in FAMILIES:
        f=[]
        for g in groups:
            tr=[r for r in dev if r["group"]!=g]; te=[r for r in dev if r["group"]==g]
            fit=choose(tr,fam); err=group_mean(te,row_loss(te,fit["a"],fit["b"]))
            f.append({"held_out":g,"a":fit["a"],"b":fit["b"],"test_worst_case_mse":err,"test_cases":[r["case"] for r in te]})
        folds[fam]=f; cv[fam]=float(np.mean([x["test_worst_case_mse"] for x in f]))
    # Fewer fitted parameters, then coefficient sum, then a, then b.
    order={"no_factors":0,"version_only":1,"cost_only":1,"both":2,"original":0}
    def key(f):
        fit=choose(dev,f); return (cv[f],order[f],fit["a"]+fit["b"],fit["a"],fit["b"])
    minimum=min(cv.values()); candidates=[f for f in FAMILIES if cv[f]<=minimum+1e-12]
    selected=min(candidates,key=lambda f:key(f)[1:]); fit=choose(dev,selected)
    models={}
    for f in FAMILIES:
        z=choose(dev,f); models[f]={**z,"cv_worst_case_mse":cv[f],"folds":folds[f],"parameter_count":order[f]}
    return selected,fit,models

def bootstrap(dev, family, seed=20260921,n=1000):
    rng=np.random.default_rng(seed); groups=sorted({r["group"] for r in dev}); a,b=grid()
    # Compute each group's full grid loss once; bootstrap only resamples means.
    gl={g:np.asarray([group_mean([r for r in dev if r['group']==g], row_loss([r for r in dev if r['group']==g],float(x),float(y))) for x,y in zip(a,b)]) for g in groups}
    mask=family_mask(family,a,b); out=[]
    for _ in range(n):
        sample=rng.choice(groups,size=len(groups),replace=True); scores=np.mean([gl[g] for g in sample],axis=0); cand=np.where(mask)[0]; best=scores[cand].min(); ties=cand[scores[cand]<=best+1e-12]; j=min(ties,key=lambda i:(a[i]+b[i],a[i],b[i]))
        out.append({"family":family,"a":float(a[j]),"b":float(b[j])})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",default=str(ROOT/"reviewed-data.json")); ap.add_argument("--development-data"); ap.add_argument("--heldout-data"); ap.add_argument("--validate",action="store_true"); ap.add_argument("--frozen",default=str(ROOT/"frozen-selection.json")); ap.add_argument("--out",default=None); ap.add_argument("--fit-results",default=None,help="Matching frozen fit results for separate sensitivity validation"); args=ap.parse_args()
    dev,held,source=split_inputs(args)
    if args.validate:
        fr=json.loads(Path(args.frozen).read_text()); rows=held
        protocol_hash=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()
        if fr.get('protocol_sha256') != protocol_hash: raise ValueError('frozen selection protocol hash mismatch')
        canonical=json.dumps(dev,ensure_ascii=False,sort_keys=True,separators=(',',':')); ih=hashlib.sha256(canonical.encode()).hexdigest()
        if fr.get('input_sha256') != ih:
            raise ValueError('frozen selection development input hash mismatch')
        if not held: raise ValueError("--validate requires non-empty heldout-data.json")
        fit=fr["fit"]; rf=Path(args.fit_results) if args.fit_results else ROOT/'fit-results.json'; prior=json.loads(rf.read_text()) if rf.exists() else {}
        if prior and prior.get('input_sha256') != ih: raise ValueError('fit-results input hash does not match frozen selection')
        model_fits={k:v for k,v in prior.get('models',{}).items()}; model_fits['original']={'a':.3,'b':.1}
        if fr.get('selected_family') not in model_fits: model_fits[fr['selected_family']]=fit
        errors={k:group_mean(rows,row_loss(rows,v['a'],v['b'])) for k,v in model_fits.items()}
        selected_error=errors[fr['selected_family']]; base_error=errors['original']
        pair=[{'case':r['case'],'group':r['group'],'selected_minus_original':float(x)} for r,x in zip(rows,row_loss(rows,fit['a'],fit['b'])-row_loss(rows,.3,.1))]
        budgets={}
        for bgt in sorted({str(r.get('budget')) for r in rows}):
            rr=[r for r in rows if str(r.get('budget'))==bgt]; budgets[bgt]={'n':len(rr),'selected_mse':group_mean(rr,row_loss(rr,fit['a'],fit['b'])),'original_mse':group_mean(rr,row_loss(rr,.3,.1))}
        rng=np.random.default_rng(20260921); gs=sorted({r['group'] for r in rows}); diffs=[]
        for _ in range(1000):
            sample=rng.choice(gs,size=len(gs),replace=True); diffs.append(float(np.mean([np.mean([x for x,r in zip(row_loss(rows,fit['a'],fit['b'])-row_loss(rows,.3,.1),rows) if r['group']==g]) for g in sample])))
        res={"mode":"validate","frozen_selection":fr,"n":len(rows),"heldout_group_mse":selected_error,"baseline_original_group_mse":base_error,"family_group_mse":errors,"pair_loss":pair,"budget_errors":budgets,"bootstrap_selected_minus_original":{"seed":20260921,"n":1000,"mean":float(np.mean(diffs)),"p05":float(np.quantile(diffs,.05)),"p95":float(np.quantile(diffs,.95))},"rows":[r["case"] for r in rows]}
        Path(args.out or ROOT/"validation-results.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n"); print(json.dumps(res,ensure_ascii=False,indent=2)); return
    selected,fit,models=select_family(dev)
    # Interval-distance sensitivity is descriptive and cannot affect selection.
    interval_distance={f:{"a":models[f]["a"],"b":models[f]["b"],"mse":group_mean(dev,interval_distance_loss(dev,models[f]["a"],models[f]["b"]))} for f in FAMILIES}
    canonical=json.dumps(dev,ensure_ascii=False,sort_keys=True,separators=(",",":")); ih=hashlib.sha256(canonical.encode()).hexdigest()
    frozen={"protocol_version":json.loads((ROOT/"protocol.json").read_text())["protocol_version"],"protocol_sha256":hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),"input_sha256":ih,"source":source,"development_cases":[r["case"] for r in dev],"selected_family":selected,"fit":fit}
    if Path(args.frozen).exists(): raise FileExistsError(f"refusing to overwrite existing frozen selection: {args.frozen}")
    Path(args.frozen).write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+"\n")
    res={"mode":"fit","n_development":len(dev),"n_heldout":len(held),"selected_family":selected,"fit":fit,"models":models,"interval_distance_sensitivity":interval_distance,"task_bootstrap":bootstrap(dev,selected),"input_sha256":ih,"heldout_cases_not_used_in_selection":[r["case"] for r in held]}
    Path(args.out or ROOT/"fit-results.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n"); print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
