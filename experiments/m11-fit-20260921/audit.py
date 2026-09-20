from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent

def norm(t):return re.sub(r'\s+','',t.replace('\\n','\n'))
def match(q,t):
 q=norm(q);t=norm(t)
 if not q:return None
 if q in t:return 'exact_normalised'
 chunks=[x for x in re.split(r'…+|\.{3,}',q) if len(x)>=8]
 if chunks and all(c in t for c in chunks):return 'ellipsis_fragments'
 return 'needs_review'
checks=[]
for file in (ROOT/'assessments').glob('*.json'):
 d=json.loads(file.read_text());p=json.loads((ROOT/'packets'/f"{d['case']}.json").read_text());obs={x['id']:x['response'] for x in p['observations']};obs['prior_answer']=p['prior_answer'];obs['actual_dispatched_counts']=json.dumps(p['counts'])
 if file.stem.endswith('outcome'):
  for x in d['requirements']:
   checks.append({'case':d['case'],'kind':'outcome','item':x['id'],'status':x['status'],'answer_quote_check':match(x['answer_quote'],p['answer']),'source_quote_check':match(x['evidence_quote'],obs.get(x.get('evidence_id'),'')) if x.get('verification')=='source' else 'not_source_verification'})
 else:
  for x in d['metrics']:
   if x.get('score') is not None and x.get('lower')!=x.get('upper'):checks.append({'case':d['case'],'kind':'predictor','item':x['id'],'warning':'score supplied alongside non-point bounds; must adjudicate before fit'})
(ROOT/'quote-audit.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print('Outcome quote checks',len([x for x in checks if x['kind']=='outcome']),'needs review',sum(x.get('answer_quote_check')=='needs_review' or x.get('source_quote_check')=='needs_review' for x in checks))
for x in checks:
 if x['kind']=='predictor':print(x)
