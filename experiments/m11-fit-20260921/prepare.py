from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parent
sources=list(Path('/Users/hsin/Documents/Coding/opknow/experiments/multimodel/m11-pilot-20260920/runs').glob('*/process.jsonl'))+list((ROOT.parent/'skill-ab-20260920/runs').glob('*/process.jsonl'))
manifest=[]
for p in sorted(sources,key=lambda p:p.parent.name):
 events=[json.loads(l) for l in p.read_text().splitlines()];meta=events[0]['metadata'];rid=p.parent.name
 ident='case-'+hashlib.sha256(rid.encode()).hexdigest()[:8]
 req={e['id']:e for e in events if e['type']=='tool_request'}
 first=min(e['seq'] for e in events if e['type']=='tool_request');prior=[];obs=[]
 for e in events:
  if e['type']=='client_note' and e['seq']<first:
   try:blob=json.loads(e['content']['content'])
   except:continue
   content=blob.get('message',{}).get('content',[])
   if isinstance(content,list):
    prior.extend(b['text'] for b in content if b.get('type')=='text')
  if e['type']=='tool_result':
   q=req[e['request_id']]
   obs.append({'id':e['id'],'role':q['role'],'request':q['arguments'],'status':e.get('status'),'response':e['response']['content'],'sha256':e['response']['sha256']})
 answer=events[-1]['answer']['content']
 match=re.search(r'<answer>(.*?)</answer>',answer,re.S)
 if match:answer=match.group(1)
 packet={'case':ident,'task':events[0]['question']['content'],'prior_answer':'\n'.join(prior),'observations':obs,'answer':answer,'counts':{role:sum(e['type']=='tool_dispatch' and req[e['request_id']]['role']==role for e in events) for role in ['search','fetch']}}
 (ROOT/'packets').mkdir(exist_ok=True);(ROOT/'packets'/f'{ident}.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2))
 manifest.append({'case':ident,'run':rid,'task_group':meta['task_id'],'ecosystem':meta['ecosystem'],'protocol':meta['protocol_version'],'counts':packet['counts'],'process_path':str(p),'process_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'packet_sha256':hashlib.sha256((ROOT/'packets'/f'{ident}.json').read_bytes()).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(ROOT/'.gitignore').write_text('packets/\nraw/\n__pycache__/\n')
print([(x['case'],x['task_group'],x['ecosystem']) for x in manifest])
