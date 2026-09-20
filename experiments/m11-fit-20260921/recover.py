"""Parse both supported CLI envelopes; never retain reasoning payloads."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parent
manifest={e['case']:e for e in json.loads((ROOT/'manifest.json').read_text())}
def clean(x):
 if isinstance(x,list):return [clean(y) for y in x if not(isinstance(y,dict) and y.get('type') in ('reasoning','thinking','redacted_thinking'))]
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k not in ('rawContent','reasoning_content','thinking','signature')}
 return x
for p in sorted((ROOT/'raw').glob('*.stdout.json')):
 target=ROOT/'assessments'/p.name.replace('.stdout.json','.json')
 try:
  outer=clean(json.loads(p.read_text()));p.write_text(json.dumps(outer,ensure_ascii=False,indent=2))
  if target.exists():
   value=json.loads(target.read_text());value['_audit']['response_model']=next((e.get('providerData',{}).get('model') for e in outer if e.get('role')=='assistant'),None) if isinstance(outer,list) else outer.get('model');target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');continue
  result=next((e for e in reversed(outer) if e.get('type')=='result'),{}) if isinstance(outer,list) else outer
  ans=result.get('result','')
  if not ans and isinstance(outer,list):ans='\n'.join(b.get('text','') for e in outer if e.get('role')=='assistant' for b in e.get('content',[]) if b.get('type') in ('output_text','text'))
  ans=re.sub(r'^```(?:json)?\s*|\s*```$','',ans.strip());value=json.loads(ans);value.setdefault('case','-'.join(p.name.split('-')[:2]));e=manifest[value['case']]
  prompt=(ROOT/'raw'/p.name.replace('.stdout.json','.prompt.txt')).read_text();kind=p.name.split('-')[-1].split('.')[0]
  value['_audit']={'model_requested':'glm-5.3','response_model':next((e.get('providerData',{}).get('model') for e in outer if e.get('role')=='assistant'),None) if isinstance(outer,list) else outer.get('model'),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'process_sha256':e['process_sha256'],'packet_sha256':e['packet_sha256'],'kind':kind,'automatic_assessment':True,'duration_ms':result.get('duration_ms'),'client_is_error':result.get('is_error'),'note':'CLI list envelope recovered without a new model call; reasoning payloads excluded.'}
  target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print('Recovered',target.name)
 except Exception as e:print('Cannot recover',p.name,repr(e))
