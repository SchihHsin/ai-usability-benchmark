"""Reproducible legacy-score sensitivity audit. Does not estimate optimal weights."""
from pathlib import Path
import json, itertools, math
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'legacy-inputs.json').read_text())['rows']
def components(scores):
 x=[0 if s=='受阻' else s/5 for s in scores]
 return 1-(1-x[0]*x[1]*x[2])*(1-x[4]*x[5])*(1-x[6]),x[3],x[7]
def calc(row,a,b):
 k,v,c=components(row['scores']);return 100*k*(1-a+a*v)*(1-b+b*c)
def sign(v):return 0 if abs(v)<1e-9 else (1 if v>0 else -1)
def ranks(vals):
 return [1+sum(y>x+1e-9 for y in vals)+(sum(abs(y-x)<1e-9 for y in vals)-1)/2 for x in vals]
def corr(x,y):
 mx=sum(x)/len(x);my=sum(y)/len(y)
 den=math.sqrt(sum((t-mx)**2 for t in x)*sum((t-my)**2 for t in y))
 return sum((a-mx)*(b-my) for a,b in zip(x,y))/den if den else None
base=[calc(r,.3,.1) for r in rows];br=ranks(base)
tasks=sorted(set(r['task'] for r in rows));lookup={(r['task'],r['ecosystem']):i for i,r in enumerate(rows)}
def gaps(vals):return {t:vals[lookup[t,'cuda']]-vals[lookup[t,'cann']] for t in tasks}
bg=gaps(base);grid=[];envelopes={t:[] for t in tasks}
for ai in range(51):
 for bi in range(21):
  a,b=ai/100,bi/100;vals=[calc(r,a,b) for r in rows];g=gaps(vals)
  reversed_tasks=[t for t in tasks if sign(g[t])*sign(bg[t])==-1]
  tied_tasks=[t for t in tasks if sign(g[t])==0 and sign(bg[t])!=0]
  for t in tasks:envelopes[t].append(g[t])
  grid.append({'a':a,'b':b,'mean_cuda_minus_cann':sum(g.values())/len(g),'spearman_vs_baseline':corr(br,ranks(vals)),'reversed_tasks':reversed_tasks,'new_ties':tied_tasks,'max_absolute_score_change':max(abs(v-u) for v,u in zip(vals,base))})
summary={'purpose':'Sensitivity audit, not weight optimisation; ranges and step are disclosed stress-test settings, not literature thresholds.',
 'data_scope':'26 legacy tasks × 2 ecosystems; no current-rubric or independent outcome validation.',
 'fixed_coefficients':{'a':.3,'b':.1,'reason':'Retain previously specified construct and baseline; no outcome-fitted optimum is identifiable. Not selected to preserve an ecosystem ranking.'},
 'grid':{'a':[0,.5,.01],'b':[0,.2,.01],'points':len(grid)},
 'baseline_mean_cuda_minus_cann':sum(bg.values())/len(bg),
 'mean_gap_range':[min(g['mean_cuda_minus_cann'] for g in grid),max(g['mean_cuda_minus_cann'] for g in grid)],
 'minimum_spearman':min(g['spearman_vs_baseline'] for g in grid),
 'grid_points_with_pair_reversal':sum(bool(g['reversed_tasks']) for g in grid),
 'pair_reversal_tasks':sorted(set(t for g in grid for t in g['reversed_tasks'])),
 'grid_points_with_new_ties':sum(bool(g['new_ties']) for g in grid),
 'maximum_score_change':max(g['max_absolute_score_change'] for g in grid),
 'task_gap_ranges':{t:{'baseline':bg[t],'min':min(v),'max':max(v)} for t,v in envelopes.items()},
 'grid_results':grid}
(ROOT/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('grid_results','task_gap_ranges')},ensure_ascii=False,indent=2))
# Arithmetic invariants, independent of legacy observations.
for score in (1,3,5):
 r={'scores':[score]*10};x=score/5
 expected=100*(1-(1-x**3)*(1-x*x)*(1-x))*(.7+.3*x)*(.9+.1*x)
 assert math.isclose(calc(r,.3,.1),expected)
for r in rows:
 assert calc(r,.5,.2)<=calc(r,0,0)+1e-9
 assert 0<=calc(r,.3,.1)<=100
