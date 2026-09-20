"""Post-run public HTTP references; never injected into generator context or counted as its fetches."""
from pathlib import Path
import json,base64,hashlib,datetime,urllib.request,concurrent.futures
R=Path(__file__).resolve().parent
inventory=json.loads((R/'m2-inventory.json').read_text());urls=sorted({d['url'] for c in inventory for d in c['documents']})
out=R/'m2-reference-acquisition.jsonl';seen={json.loads(x)['url'] for x in out.read_text().splitlines()} if out.exists() else set()
def get(url):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; evidence-reference-check)'}),timeout=18) as r:
   b=r.read();return {'url':url,'time':start,'status':r.status,'final_url':r.url,'content_type':r.headers.get('Content-Type'),'sha256':hashlib.sha256(b).hexdigest(),'body_base64':base64.b64encode(b).decode(),'purpose':'post-run reference check; not model-visible evidence'}
 except Exception as e:return {'url':url,'time':start,'error':str(e),'purpose':'post-run reference check; not model-visible evidence'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 with out.open('a') as f:
  for x in pool.map(get,[u for u in urls if u not in seen]):f.write(json.dumps(x,ensure_ascii=False)+'\n');f.flush()
print(json.dumps({'known_urls':len(urls),'new_reference_requests':len([u for u in urls if u not in seen])}))
