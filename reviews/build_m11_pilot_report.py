from pathlib import Path
import json,hashlib,re
from html import escape as H
ROOT=Path(__file__).parent
P=Path('/Users/hsin/Documents/Coding/opknow/experiments/multimodel/m11-pilot-20260920')
out=[]
for f in sorted((P/'runs').glob('*/process.jsonl')):
 rows=[json.loads(l) for l in f.read_text().splitlines()];req={r['id']:r for r in rows if r['type']=='tool_request'}
 counts={k:sum(r['type']=='tool_dispatch' and req[r['request_id']]['role']==k for r in rows) for k in ['search','fetch']}
 end=next(r for r in rows if r['type']=='run_end');answer=end['answer']['content'];assert hashlib.sha256(answer.encode()).hexdigest()==end['answer']['sha256']
 prior=[];ledger=[]
 for r in rows:
  if r['type']!='client_note':continue
  try:v=json.loads(r['content']['content'])
  except Exception:continue
  if 'budget_ledger' in v:ledger=[json.loads(x) for x in v['budget_ledger'].splitlines()]
  for b in v.get('message',{}).get('content',[]) if isinstance(v.get('message',{}).get('content',[]),list) else []:
   if b.get('type')=='text' and '<prior_answer>' in b.get('text',''):prior.append(dict(event=r['id'],text=b['text']))
 results=[r for r in rows if r['type']=='tool_result'];errors=[];counts_results=[]
 for r in results:
  text=r['response']['content'];assert hashlib.sha256(text.encode()).hexdigest()==r['response']['sha256']
  if '404: Not Found' in text or text.startswith('Error:'):errors.append(r['id'])
  if req[r['request_id']]['role']=='search':counts_results.append(len(re.findall(r'^## \d+\.',text.replace('\\n','\n'),re.M)))
 out.append(dict(run=f.parent.name,counts=counts,answer_chars=len(answer),prior_recorded=bool(prior),budget_ledger_events=len(ledger),tool_content_error_events=errors,search_result_counts=counts_results,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),M11=None,M11_reason='新版分项未完成有据评分；M2完整参照缺失，M6/M7尚需独立核验，禁止补分'))
# Local diagnostics above do not alter either original two-file record; public report contains summaries only.
(ROOT/'m11-pilot-summary.json').write_text(json.dumps({'scale':'0–100, no bands','status':'collection_complete_scoring_incomplete','model':'deepseek-v4.1-flash (CLI alias, not immutable snapshot)','runs':out},ensure_ascii=False,indent=2))
body='<section id="m11-pilot"><h2>小实验：3任务 × 2生态 × 1模型</h2><p>DeepSeek V4.1 Flash，WorkBuddy独立会话，A模型转换、D自定义算子、I版本配套。6次真实运行完成，4次搜索/8次获取上限，逐轮保存预算账本、工具返回、检索前回答及最终答案。M11现改为百分制，原已冻结采集协议不重写；尺度变更不影响已采集内容。</p><table><tr><th>运行</th><th>搜索/获取</th><th>最终答案字符数</th><th>检索前回答/预算账本</th></tr>'
for x in out:body+=f'<tr><td>{H(x["run"])}</td><td>{x["counts"]["search"]}/{x["counts"]["fetch"]}</td><td>{x["answer_chars"]}</td><td>{x["prior_recorded"]} / {x["budget_ledger_events"]}条</td></tr>'
body+='''</table><h3>实际暴露的待修正问题</h3><ol>
<li><b>M2分母：</b>CUDA D的cpp_extension返回自称“API Documentation Extract”，本身不是同版全文参照。不能凭工具称“完整提取”判5分；暂保留待定，不能用长短猜50%。若继续采用覆盖比例，正式协议需明确参照取得方法。</li>
<li><b>工具成功不等于内容成功：</b>CUDA D有两次返回“404: Not Found”；CANN D有正文仅包含“获取效率、正确性、完整性、易理解”的官方读取。应检查实际返回，不只看外层ok，也不能据此推断页面技术架构。</li>
<li><b>来源与工具补写：</b>CANN D有“根据文章内容，我为你提取……”式代码返回，CUDA亦有摘要型返回。需引用为Agent实际收到的材料，不能当作原网页逐字全文；不能把工具补写当成官方原文。</li>
<li><b>最终答案字段：</b>实际记录在run_end.answer；此前规范误写answer事件，现已修正。完整答案和检索前答案已保存，运行成功与内容核查分开。</li>
<li><b>M11公式本身：</b>M1—M8全3分，按原式得到67.5/100；M7为5时，三渠道合成K恒等于1，使M1/M2/M3/M5/M6不再影响K。这是原式的完全补偿假设，需明确是否符合研究目的，百分制不会自动消除该性质。</li>
</ol><p><b>当前不能宣称：</b>这不是评分效度验证，分项尚未完成独立证据核查，6个M11均为待定而非0分。不能把收集完成写成评分完成，也不能用原自评填新版M7。未开展硬件执行验证或独立双人评分。</p><p>原始过程保留在本机实验目录；公开摘要只列检查结果和定位信息。无需再重复这6次采集，后续从既有返回完成内容核查，必要时补充只读参照。</p></section>'''
(ROOT/'m11-pilot-report.html').write_text(body)
print(json.dumps(out,ensure_ascii=False,indent=2))
