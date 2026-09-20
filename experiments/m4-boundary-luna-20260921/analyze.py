# -*- coding: utf-8 -*-
"""Compare frozen M4 ratings without changing any judge's scores."""
from pathlib import Path
import json,hashlib,html,collections,datetime
R=Path(__file__).resolve().parent
def load(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protocol=load('protocol.json');cases=load('input.json');expect=load('expectations-not-for-raters.json')
assert sha(R/'input.json')==protocol['input_sha256']
for version,digest in protocol['rubric_sha256'].items():assert sha(R/('skill-'+version)/'SKILL.md')==digest
ids=[c['case_id'] for c in cases];byid={c['case_id']:c for c in cases};runs={};quote_issues=[];checks=[]
for run in ['old-a','new-a','new-b']:
 d=load('runs/'+run+'/evaluation.json');ratings=d['ratings'];assert [x['case_id'] for x in ratings]==ids,(run,'case/order mismatch')
 assert len(ratings)==len(ids)
 for x in ratings:
  assert x['score'] is None or (type(x['score']) is int and 1<=x['score']<=5)
  assert x['status'] in ['scored','uncertain','blocked','not_applicable'],(run,x)
  if x['status']=='scored':assert x['score'] is not None
  texts={s['source_id']:s['text'] for s in byid[x['case_id']]['sources']}
  if x['score'] is not None and not x.get('evidence'):quote_issues.append({'run':run,'case_id':x['case_id'],'issue':'missing evidence'})
  for e in x.get('evidence',[]):
   sid=e.get('source_id');q=e.get('quote');ok=sid in texts and isinstance(q,str) and bool(q.strip()) and q in texts[sid]
   if not ok:quote_issues.append({'run':run,'case_id':x['case_id'],'issue':'quote not exact in referenced text','evidence':e})
   else:checks.append({'run':run,'case_id':x['case_id'],'source_id':sid,'start':texts[sid].index(q),'end':texts[sid].index(q)+len(q)})
 runs[run]={x['case_id']:x for x in ratings}
def signature(x):return (x['score'],x['status'],x.get('lower'),x.get('upper'))
pair=[cid for cid in ids if runs['new-a'][cid]['score'] is not None and runs['new-b'][cid]['score'] is not None]
agreement={'numeric_comparable':len(pair),'exact_numeric_agreement':sum(runs['new-a'][c]['score']==runs['new-b'][c]['score'] for c in pair),'full_status_and_bounds_agreement':sum(signature(runs['new-a'][c])==signature(runs['new-b'][c]) for c in ids),'total_cases':len(ids),'disagreements':[{'case_id':c,'new_a':runs['new-a'][c],'new_b':runs['new-b'][c]} for c in ids if signature(runs['new-a'][c])!=signature(runs['new-b'][c])]}
invariance=[]
for relation in expect['invariance_checks']:
 a,b=relation['cases']
 for run,ratings in runs.items():
  x,y=ratings[a],ratings[b];invariance.append({'run':run,'type':relation['type'],'cases':[a,b],'scores':[x['score'],y['score']],'equal':x['score'] is not None and x['score']==y['score'],'uncertain':x['score'] is None or y['score'] is None})
diagnostics=[]
for run,ratings in runs.items():
 for c in cases:
  if c['kind']!='synthetic':continue
  x=ratings[c['case_id']];e=expect['expected'][c['case_id']]
  diagnostics.append({'run':run,'case_id':c['case_id'],'investigator_expectation':e['score'],'observed_score':x['score'],'expected_status':e['status'],'observed_status':x['status'],'match':x['score']==e['score'] and x['status']==e['status'],'interpretation':'comparison to designed diagnostic expectation, not accuracy against independent gold'})
summary={'protocol':protocol['id'],'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_requested':'gpt-5.6-luna','model_identity_basis':'collaboration.spawn_agent model argument, not model self-report; immutable backend version not exposed','case_count':len(cases),'ratings_count':len(cases)*len(runs),'new_rule_repeat_agreement':agreement,'quote_issues':quote_issues,'checked_literal_quotes':len(checks),'invariance_checks':invariance,'synthetic_diagnostics':diagnostics,'formal_skill_changed':False,'rubric_or_scores_changed_after_dispatch':False,'limitations':protocol['limits']}
(R/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(R/'quote-audit.json').write_text(json.dumps({'matches':checks,'issues':quote_issues,'original_scores_unchanged':True},ensure_ascii=False,indent=2)+'\n')
def esc(x):return html.escape(str(x))
def display(x):return str(x['score']) if x['score'] is not None else x['status']+' '+str([x.get('lower'),x.get('upper')])
rows=[]
for c in cases:
 cid=c['case_id'];rr=[runs[k][cid] for k in ['old-a','new-a','new-b']]
 rows.append('<tr><td>'+esc(cid)+'<br>'+esc(c['kind'])+'</td><td>'+esc(c['question'])+'</td>'+''.join('<td>'+esc(display(x))+'</td>' for x in rr)+'<td>'+esc(rr[1]['reason'])+'<br><small>'+esc(rr[2]['reason'])+'</small></td></tr>')
headers=['案例','评价任务','旧规则','新规则A','新规则B','两次新评分理由']
table='<table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
details=[]
for c in cases:
 cid=c['case_id'];details.append('<details><summary>'+esc(cid)+'：证据与歧义记录</summary>'+''.join('<p>'+esc(s['source_id'])+' '+('<a href="'+esc(s['url'])+'">来源</a>' if 'url' in s else '合成测试材料')+'</p><pre>'+esc(s['text'])+'</pre>' for s in c['sources'])+''.join('<p>'+esc(k)+': '+esc(runs[k][cid].get('ambiguity',''))+'</p>' for k in runs)+'</details>')
rule_rows=[['1','无版本信息','无版本信息'],['2','有版本，无法确定选择','有版本信息，但无明确选择依据'],['3','能缩小范围，仍不能确定','部分选择条件明确，仍有关键条件缺失'],['4','需要跨页面对照','需自行合并官方约束，才能确定适用版本'],['5','同一页面内即可确定','官方已明确说明条件与适用版本的对应关系']]
rules='<table><tr><th>分值</th><th>旧规则</th><th>新规则</th></tr>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rule_rows)+'</table>'
note=(R/'conclusion.md').read_text() if (R/'conclusion.md').exists() else '结果已生成，结论尚未整理。'
content='<h1>M4 五档规则小实验</h1><p>实际请求模型：GPT-5.6 Luna；16例 × 3个独立评分上下文。新规则两次评分、旧规则一次。12例为合成边界测试，4例为官方资料阅读包。不是16次端到端任务执行，也不是跨生态效度验证。</p><h2>结论</h2><pre>'+esc(note)+'</pre><h2>新旧档位</h2>'+rules+'<h2>结果</h2><p>新规则可比较点分 '+str(len(pair))+' 例，其中完全一致 '+str(agreement['exact_numeric_agreement'])+' 例；逐字引文问题 '+str(len(quote_issues))+' 条。相同模型的重复一致不等于独立专家验证。</p>'+table+'<h2>证据</h2>'+''.join(details)+'<h2>边界</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in protocol['limits'])+'</ul><p><a href="protocol.json">冻结协议</a> · <a href="results.json">完整结果</a> · <a href="quote-audit.json">引文核查</a> · <a href="source-selection.json">历史材料选择依据</a> · <a href="../m11-uniform-fit-20260921/literature.json">已有方法文献及边界</a></p>'
(R/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>M4 Luna 实验</title><style>body{max-width:1200px;margin:32px auto;padding:0 24px;color:#233047;font:16px/1.65 system-ui}table{border-collapse:collapse;width:100%}th,td{border:1px solid #dce1e8;padding:10px;text-align:left;vertical-align:top}th{background:#edf3fb}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fb;padding:16px}small{color:#5c687a}details{margin:12px 0}a{color:#1766ae}</style>'+content+'</html>')
print(json.dumps({'agreement':agreement,'quote_issues':len(quote_issues),'invariance':invariance},ensure_ascii=False))
