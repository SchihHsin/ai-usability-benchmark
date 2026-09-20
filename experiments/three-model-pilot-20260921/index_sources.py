"""Index all visible numbered search results, preserving exact text and offsets."""
from pathlib import Path
import json,re,hashlib
from urllib.parse import urlsplit
from prepare_assessment import unpack
R=Path(__file__).resolve().parent
all_runs=[]
for p in sorted((R/'runs').glob('*/process.jsonl')):
 rows=[json.loads(x) for x in p.read_text().splitlines()];req={x['id']:x for x in rows if x['type']=='tool_request'};queries=[];fetches=[]
 for x in rows:
  if x['type']!='tool_result':continue
  q=req[x['request_id']];txt=unpack(x['response'])
  if q['role']=='search':
   heads=list(re.finditer(r'^## (\d+)\. \[([^\n]*)\]\((https?://[^\n]*)\)\s*$',txt,re.M));results=[]
   for i,h in enumerate(heads):
    end=heads[i+1].start() if i+1<len(heads) else len(txt);block=txt[h.end():end];u=re.search(r'^\*\*URL:\*\*\s*(\S+)',block,re.M);url=u.group(1) if u else h.group(3)
    results.append({'query_index':1,'list_position':int(h.group(1)),'title':h.group(2),'url_raw':url,'domain':urlsplit(url).netloc,'snippet':block.split('**URL:**')[0].strip().rstrip('-').strip(),'date_visible':None,'citation_id':None,'engine_rank':None,'source_start':h.start(),'source_end':end,'raw_block':txt[h.start():end]})
   queries.append({'event_id':x['id'],'request_id':q['id'],'query':q.get('arguments',{}),'search_results':results,'returned_count':len(results) if heads else None,'list_complete':True if heads else None,'missing_fields':['engine_rank','citation_id','structured_date'],'parse_status':'numbered_tool_results' if heads else 'unparsed_or_tool_error','raw_sha256':x['response']['sha256']})
  elif q['role']=='fetch':
   url=q.get('arguments',{}).get('url');origins=[{'event_id':z['event_id'],'list_position':y['list_position']} for z in queries for y in z['search_results'] if y['url_raw']==url]
   fetches.append({'request_id':q['id'],'event_id':x['id'],'url':url,'arguments':q.get('arguments',{}),'matching_prior_search_results':origins,'origin_status':'exact_url_match' if origins else 'not_established_by_exact_search_match','representation':'model-visible tool text; raw source media type not independently exposed','raw_sha256':x['response']['sha256']})
 all_runs.append({'run_id':p.parent.name,'process_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'queries':queries,'fetches':fetches})
(R/'source-index.json').write_text(json.dumps({'note':'No guessed engine ranks or technical delivery causes; snippets retain dates inline. Unparsed results remain in original process log. Links matched by exact URL do not prove model intent.','runs':all_runs},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'runs':len(all_runs),'queries':sum(len(x['queries']) for x in all_runs),'indexed_results':sum(len(q['search_results']) for x in all_runs for q in x['queries'])}))
