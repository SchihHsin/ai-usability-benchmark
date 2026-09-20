"""Final mechanical checks; do not equate schema/quote checks with validity."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'frozen-skill'))
from scripts import run_log
h=json.loads((R/'process-hashes.json').read_text());checks=[]
for rel,digest in h.items():
 p=R/rel;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,rel
 check=run_log.check(p.parent);assert not check['issues'],check
 ev=json.loads((p.parent/'evaluation.json').read_text())['revisions'][-1]['evaluation'];ids=[x['id'] for x in ev['metrics']];assert ids==[f'M{i}' for i in range(1,12)],ids
 assert ev.get('assessment_files'),p.parent.name+' pending assessment'
 for m in ev['metrics']:
  if m.get('score') is not None:assert 0<=m['score']<=100 if m['id']=='M11' else 1<=m['score']<=5
 checks.append({'run':p.parent.name,'process_unchanged':True,'log_check':check})
assert len(h)==18
manifest=json.loads((R/'frozen-skill/manifest.json').read_text())
for rel,digest in manifest.items():assert hashlib.sha256((R/'frozen-skill'/rel).read_bytes()).hexdigest()==digest,rel
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  if t=='a' and dict(a).get('href'):self.links.append(dict(a)['href'])
p=Links();p.feed((R/'report.html').read_text());missing=[]
for link in p.links:
 if not link.startswith(('http:','https:','#')) and not (R/link.split('#')[0]).exists():missing.append(link)
assert not missing,missing
(R/'verification.json').write_text(json.dumps({'run_count':len(checks),'checks':checks,'skill_manifest_unchanged':True,'report_local_links_ok':True,'browser_visual_check':False,'note':'Literal/schema checks are not proof of technical correctness or construct validity.'},ensure_ascii=False,indent=2)+'\n')
print('18 runs checked; original process and frozen Skill hashes unchanged; all 11 metric entries and report links present.')
