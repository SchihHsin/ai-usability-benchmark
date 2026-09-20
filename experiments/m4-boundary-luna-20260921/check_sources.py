"""Reproduce fresh-source text extraction and check retained bodies and offsets."""
from pathlib import Path
from html.parser import HTMLParser
import json,base64,hashlib
R=Path(__file__).resolve().parent
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style','svg'):self.skip+=1
        if t in ('p','li','tr','h1','h2','h3','h4'):self.parts.append('\n')
    def handle_endtag(self,t):
        if t in ('script','style','svg'):self.skip=max(0,self.skip-1)
        if t in ('td','th'):self.parts.append(' | ')
        if t in ('p','li','tr','h1','h2','h3','h4'):self.parts.append('\n')
    def handle_data(self,d):
        if not self.skip:self.parts.append(d)
for line in (R/'source-acquisition.jsonl').read_text().splitlines():
    event=json.loads(line);name=event['event_id'].removeprefix('fetch-')
    body=base64.b64decode(event['body_base64']);assert hashlib.sha256(body).hexdigest()==event['body_sha256'];assert body==(R/(name+'.html')).read_bytes()
    p=Parser();p.feed(body.decode('utf-8'));s='\n'.join(x.strip() for x in ''.join(p.parts).splitlines() if x.strip());assert s==(R/(name+'.txt')).read_text()
for c in json.loads((R/'input.json').read_text()):
    for src in c['sources']:
        if 'text_start' not in src:continue
        name=src['source_id'].removeprefix('fetch-');p=R/(name+'.txt');assert hashlib.sha256(p.read_bytes()).hexdigest()==src['full_extracted_text_sha256'];s=p.read_text();assert src['text']==s[src['text_start']:src['text_end']]
print('Fresh HTTP bodies, deterministic extraction, and exact section offsets verified.')
