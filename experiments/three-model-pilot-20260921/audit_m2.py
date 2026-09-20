"""Conservative document-level evidence review; arithmetic never fills unknowns."""
from pathlib import Path
import json,re,base64,hashlib
from html.parser import HTMLParser
R=Path(__file__).resolve().parent
class Article(HTMLParser):
 def __init__(self):super().__init__();self.on=False;self.depth=0;self.text=[]
 def handle_starttag(self,t,a):
  if t=='article' and 'bd-article' in dict(a).get('class',''):self.on=True;self.depth=1
  elif self.on and t=='article':self.depth+=1
 def handle_endtag(self,t):
  if self.on and t=='article':
   self.depth-=1
   if not self.depth:self.on=False
 def handle_data(self,s):
  if self.on:self.text.append(s)
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
def markdown_text(s):
 s=re.sub(r'\[([^\]]*)\]\(https?://[^\s)]*\)',r'\1',s)
 return s
refs={x['url']:x for x in map(json.loads,(R/'m2-reference-acquisition.jsonl').read_text().splitlines())}
# Reviewed UI-only/wrong-target and explicit tool-summary examples. IDs are URL hashes, not scores from old experiments.
framework={'af63c1f4b01e','d1366366b442','12a97a98e397','9a3ea995e1e7','4efb28d38454','4bfbee5be721','88d91840c670','1e83ea7b41d1','eb1fa63b388a'}
wrong_target={'3b3cf30e1702'}
summary={'b24b12f6da97','7fed73253552','00b7c2147639'}
allcases=[]
for case in json.loads((R/'m2-inventory.json').read_text()):
 docs=[]
 for d in case['documents']:
  a=d['attempts'][-1];t=a['text'];ident=d['document_id'];reason='';ref=refs.get(d['url'],{});proof=None
  if ident in wrong_target or re.search(r'(?:Page [Nn]ot [Ff]ound|File not found|Error fetching|Failed to fetch|HTTP(?: Error)? 40[34])',t[:500]):lo=hi=1;reason='返回错误页或已核对为非目标页面；目标正文未取得'
  elif ident in framework or (len(t)<220 and any(x in t for x in ('获取效率','Findability','文档评分'))):lo=hi=2;reason='返回目标标题及界面标签，没有可识别正文'
  elif ident in summary:lo=hi=3;reason='返回为工具整理的摘要/摘录表示，非可核对的直接正文'
  elif t.startswith('**标题**') and len(t)>220:lo,hi=4,5;reason='有直接正文；同版完整起止尚不能充分核对，保留4—5范围'
  else:lo,hi=3,5;reason='有正文内容，但摘要/直接正文表示或完整性证据未充分确定，保留3—5范围'
  # Only an entire article text match supplies independent full-text support; no percentage cut-off.
  if lo==4 and ref.get('body_base64'):
   h=base64.b64decode(ref['body_base64']).decode('utf-8','replace');p=Article();p.feed(h);raw=''.join(p.text);n=norm(raw);actual=norm(markdown_text(t))
   if n and n in actual:
    lo=hi=5;reason='同URL事后HTTP参照的article全文，经去格式符号规范化后完整连续匹配工具返回；未见缺失'
    proof={'url':d['url'],'acquired_at':ref['time'],'reference_sha256':ref['sha256'],'article_text_sha256':hashlib.sha256(raw.encode()).hexdigest(),'normalized_full_article_match':True,'note':'same URL post-run reference, not immutable remote snapshot'}
  quote=t[:min(240,len(t))]
  if lo>=4:
   meaningful=[line for line in t.splitlines() if len(line.strip())>25 and not line.startswith(('**标题**','**发布时间**','#','[','!','http','Back to'))]
   if meaningful:quote=meaningful[0][:240]
  docs.append({'document_id':ident,'url':d['url'],'attempt_ids':[x['event_id'] for x in d['attempts']],'selected_final_event_id':a['event_id'],'lower':lo,'upper':hi,'score':lo if lo==hi else None,'status':'scored' if lo==hi else 'bounded','reason':reason,'evidence':[{'event_id':a['event_id'],'quote':quote}],'reference_check':{'attempted':bool(ref),'status':ref.get('status'),'error':ref.get('error'),'full_match_proof':proof},'independence_basis':'requested URL without fragment; no undocumented redirect/canonical equivalence assumed'})
 n=len(docs);lo=sum(d['lower'] for d in docs)/n if n else None;hi=sum(d['upper'] for d in docs)/n if n else None
 allcases.append({'run_id':case['run_id'],'documents':docs,'aggregate':{'score':lo if lo==hi and n else None,'lower':lo,'upper':hi,'status':'scored' if lo==hi and n else 'bounded' if n else 'insufficient_evidence','reason':'全部已识别官方目标文档最终获取状态等权平均，未知项以区间计入，未删除；不取最高或最低文档代替任务分数。','document_count':n},'review_scope':'post-run evidence review; exact snippets retained, direct-body completeness unknown unless full article match; source classification by documented official hosts/repositories in m2_inventory.py'})
(R/'m2-document-audit.json').write_text(json.dumps(allcases,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'runs':len(allcases),'documents':sum(len(c['documents']) for c in allcases),'complete_verified':sum(d['score']==5 for c in allcases for d in c['documents'])}))
