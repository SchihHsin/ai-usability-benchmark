"""Extract every official-target fetch for review, retaining failures and retries."""
from pathlib import Path
from urllib.parse import urlsplit,urldefrag
import json,hashlib
from prepare_assessment import unpack
R=Path(__file__).resolve().parent

def official(u):
 p=urlsplit(u or '');h=p.hostname or '';path=p.path.lower()
 if h=='hiascend.com' or h.endswith('.hiascend.com') or h=='nvidia.com' or h.endswith('.nvidia.com') or h=='pytorch.org' or h.endswith('.pytorch.org'):return True
 if h in ('github.com','raw.githubusercontent.com') and path.split('/')[1:2] in [['ascend'],['nvidia'],['pytorch']]:return True
 if h=='gitee.com' and path.split('/')[1:2] in [['ascend']]:return True
 return False

cases=[]
for p in sorted((R/'runs').glob('*/process.jsonl')):
 rows=[json.loads(x) for x in p.read_text().splitlines()]
 if rows[-1]['type']!='run_end':continue
 req={x['id']:x for x in rows if x['type']=='tool_request'};docs={}
 for e in rows:
  if e['type']!='tool_result':continue
  q=req[e['request_id']];url=q.get('arguments',{}).get('url','')
  if q['role']!='fetch' or not official(url) or e.get('status',e.get('tool_status'))=='not_dispatched':continue
  key=urldefrag(url)[0];docs.setdefault(key,[]).append({'event_id':e['id'],'request_id':q['id'],'url':url,'request':q.get('arguments',{}),'text':unpack(e['response']),'sha256':e['response']['sha256']})
 cases.append({'run_id':p.parent.name,'documents':[{'document_id':hashlib.sha256(url.encode()).hexdigest()[:12],'url':url,'attempts':attempts} for url,attempts in docs.items()]})
(R/'m2-inventory.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'runs':len(cases),'documents':sum(len(x['documents']) for x in cases)}))
