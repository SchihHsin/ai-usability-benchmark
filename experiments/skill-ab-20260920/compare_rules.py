"""Diagnostic cross-scoring; conservative observable cases only, not full evaluation."""
import json,re,hashlib
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).parent

def m11(scores):
    if any(scores.get('M'+str(i)) is None for i in range(1,9)):return None
    x={i:(scores['M'+str(i)]-1)/4 for i in range(1,9)}
    return 100*((x[1]+x[2]+x[3])/3+(x[5]+x[6])/2+x[7])/3*(.7+.3*x[4])*(.9+.1*x[8])

def m2_observed(text):
    t=text.strip();low=t.lower()
    if re.fullmatch(r'```\s*404: Not Found\s*```',t) or t.startswith('Error:'):return 1,'explicit_error_return'
    if re.search(r'(?i)full extraction|api documentation extract|here is .*extract|## Summary|根据文章内容，我为你提取',t):return 3,'explicit_extraction_or_summary'
    if len(t)<350 and all(w in t for w in ['获取效率','正确性','完整性','易理解']):return 2,'title_and_feedback_only'
    return None,'body_completeness_or_representation_needs_review'

def audit():
 out=[]
 for f in sorted((ROOT/'runs').glob('*/process.jsonl')):
  rows=[json.loads(l) for l in f.read_text().splitlines()];req={x['id']:x for x in rows if x['type']=='tool_request'}
  if rows[-1]['type']!='run_end':continue
  docs=[];q=0;first=None;search_counts=[];texts=[];declared=[]
  for row in rows:
   if row['type']=='client_note':
    try:v=json.loads(row['content']['content'])
    except Exception:continue
    for b in v.get('message',{}).get('content',[]) if isinstance(v.get('message',{}).get('content',[]),list) else []:
     if b.get('type')=='text':texts.append((row['seq'],b.get('text','')))
   if row['type']!='tool_result':continue
   request=req[row['request_id']];t=row['response']['content'];assert hashlib.sha256(t.encode()).hexdigest()==row['response']['sha256']
   if request['role']=='search':
    q+=1;hits=re.findall(r'^## (\d+)\. \[(.*?)\]\((https?://[^\n]+)\)',t.replace('\\n','\n'),re.M);search_counts.append(len(hits))
    if first is None:
     for pos,title,url in hits:
      host=urlparse(url).hostname or ''
      if any(host==d or host.endswith('.'+d) for d in ['pytorch.org','nvidia.com','hiascend.com']):first=dict(q=q,r=int(pos),url=url,title=title,event=row['id']);break
   if request['role']=='fetch':
    url=request['arguments'].get('url','');host=urlparse(url).hostname or ''
    official=any(host==d or host.endswith('.'+d) for d in ['pytorch.org','nvidia.com','hiascend.com']) or (host in ['github.com','raw.githubusercontent.com'] and urlparse(url).path.startswith('/pytorch/'))
    if not official:continue
    new,reason=m2_observed(t);old=new if new in [1,2] else None
    docs.append(dict(url=url,event=row['id'],new=new,old=old,basis=reason,quote=t[:450],source_sha256=row['response']['sha256']))
  first_tool=min([r['seq'] for r in rows if r['type']=='tool_request'],default=10**9)
  pre='\n'.join(t for seq,t in texts if seq<first_tool)
  counts={role:sum(r['type']=='tool_dispatch' and req[r['request_id']]['role']==role for r in rows) for role in ['search','fetch']}
  out.append(dict(run=f.parent.name,metadata=rows[0]['metadata']['rubric_version'],process_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),counts=counts,search_result_counts=search_counts,first_official_domain_result=first,prior_full='<prior_answer>' in pre,prior_chars=len(pre),final_chars=len(rows[-1]['answer']['content']),official_fetch_cross_scoring=docs,M11=None))
 return out
if __name__=='__main__':
 assert abs(m11({'M'+str(i):3 for i in range(1,9)})-40.375)<1e-8
 assert m11({'M'+str(i):5 for i in range(1,9)})==100
 assert m11({'M'+str(i):1 for i in range(1,9)})==0
 low={'M'+str(i):1 for i in range(1,9)};low['M7']=5;high=low|{'M1':5,'M2':5,'M3':5}
 assert m11(high)>m11(low)
 x=audit();(ROOT/'comparison.json').write_text(json.dumps(x,ensure_ascii=False,indent=2));print([(a['run'],a['counts'],a['prior_chars']) for a in x])
