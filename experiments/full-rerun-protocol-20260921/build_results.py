from completion_guard import invalid_ids
"""Generate a provenance-linked report without inventing unassessed scores."""
from pathlib import Path
from collections import Counter
import json,html,datetime
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text());rows=[];attempts=[]
from assessment_status import build as assessment_status_build
phase_report=assessment_status_build()
(R/'assessment-status.json').write_text(json.dumps(phase_report,ensure_ascii=False,indent=2)+'\n')
phase_by_run={r['run_id']:r['phases'] for r in phase_report['rows']}
exhausted_file=R/'collection-exhausted.json'
exhausted_record=json.loads(exhausted_file.read_text()) if exhausted_file.exists() else {}
exhausted={(exhausted_record.get('model'),v['task'],v['ecosystem']):v for v in exhausted_record.get('skipped',[])}
for model in p['models']:
 ledger=[json.loads(l) for l in (R/f'ledger-{model}.jsonl').read_text().splitlines()]
 selected={}
 for x in ledger:
  if x.get('completed') and x['run_id'] not in invalid_ids():selected[(x['task'],x['ecosystem'])]=x
 for task in p['development']:
  for eco in p['ecosystems']:
   x=selected.get((task,eco));row={'task':task,'ecosystem':eco,'model':model,'paired_analysis':task!='G','collected':bool(x)}
   if x:
    run=R/'runs'/x['run_id'];versions=json.loads((run/'evaluation.json').read_text())['revisions'];ev=next((v['evaluation'] for v in reversed(versions) if v['evaluation'].get('assessment_files')),None)
    row.update(run_id=x['run_id'],process=str((run/'process.jsonl').relative_to(R)),evaluation=str((run/'evaluation.json').relative_to(R)),assessed=bool(ev))
    row['assessment_phases']=phase_by_run.get(x['run_id'],{})
    if ev:
     row.update(metrics=ev['metrics'],overall=ev.get('overall'),gate=ev.get('execution_gate'),assessment_files=ev['assessment_files'])
     row['gate_passed']=all(g and g.get('passed') for g in row['gate'].values())
     row['quote_issues']=len(ev.get('quote_audit',[]))
   if not x and (model,task,eco) in exhausted:
    row['collection_status']='technical_attempts_exhausted'
    row['collection_failure']=exhausted[(model,task,eco)]
   rows.append(row)
 for x in ledger:
  if not x.get('completed'):attempts.append(x)
summary={'generated':datetime.datetime.now().isoformat(timespec='seconds'),'expected':156,'collected':sum(x['collected'] for x in rows),'assessed':sum(x.get('assessed',False) for x in rows),'gate_passed':sum(x.get('gate_passed',False) for x in rows),'quote_audit_clean':sum(x.get('assessed',False) and x.get('quote_issues')==0 for x in rows),'m11_states':dict(Counter((x.get('overall') or {}).get('status','not_assessed') for x in rows))}
summary['assessment_phase_states']=phase_report['summary']
summary['collection_exhausted']=sum(x.get('collection_status')=='technical_attempts_exhausted' for x in rows)
(R/'results.json').write_text(json.dumps({'summary':summary,'rows':rows,'noncomplete_ledger_records':attempts,'note':'Initial controller status corrections can appear here; see controller-repair.json. Ledger rows are not independent attempts.'},ensure_ascii=False,indent=2)+'\n')
def esc(x):return html.escape(str(x))
def metric(m):
 if not m:return '待评'
 st=m.get('status')
 if st=='not_applicable':return 'N/A'
 if m.get('score') is not None:return f'{m["score"]:.2f}'.rstrip('0').rstrip('.')
 if st=='bounded':return f'{m["lower"]:.2f}–{m["upper"]:.2f}'
 return '待核' if st in ('insufficient_evidence','incomplete_inputs','not_assessed') else esc(st)
body=[]
for row in rows:
 ms={m['id']:m for m in row.get('metrics',[])}
 cells=''.join('<td>'+metric(ms.get(f'M{i}'))+'</td>' for i in range(1,12))
 state='重试上限已达，未完成' if row.get('collection_status')=='technical_attempts_exhausted' else '待采集' if not row['collected'] else '后评技术尝试已用尽' if not row.get('assessed') and any(p['status']=='technical_attempts_exhausted' for p in row.get('assessment_phases',{}).values()) else '待后评' if not row.get('assessed') else '需复核' if not row.get('gate_passed') or row.get('quote_issues') else '结构校验通过'
 links=f'<a href="{esc(row["process"])}">过程</a> · <a href="{esc(row["evaluation"])}">评分</a>' if row['collected'] else ('<a href="collection-exhausted.json">失败记录</a>' if row.get('collection_status')=='technical_attempts_exhausted' else '')
 body.append(f'<tr><td>{esc(row["model"])}</td><td>{row["task"]}{"（单列）" if row["task"]=="G" else ""}</td><td>{row["ecosystem"]}</td>{cells}<td>{state}</td><td>{links}</td></tr>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>156次全量实验结果与证据</title><style>body{font:15px/1.65 system-ui;margin:30px;color:#24313d;background:#fafbfc}h1{font-size:28px}.box{padding:18px;background:white;border:1px solid #ddd;border-radius:12px;margin:16px 0}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px;white-space:nowrap}td,th{padding:9px;border:1px solid #ddd;text-align:left}th{background:#edf2f5;position:sticky;top:0}a{color:#235eb1}code{white-space:normal}</style><h1>156次全量实验结果与证据</h1>'''
page+=f'<div class="box">采集 <b>{summary["collected"]}/156</b>；已后评 <b>{summary["assessed"]}/156</b>；分档结构校验通过 {summary["gate_passed"]}；指标引文审计无未匹配项 {summary["quote_audit_clean"]}。<br>更新时间：{summary["generated"]}。采集、后评、证据复核分别计数，结构校验通过不等于技术正确性已充分验证。</div>'
page+='<div class="box"><b>范围与固定条件</b><p>26项任务 × 2侧 × 3个实际模型。G涉及ROCm迁移，保留记录并从25组CANN/CUDA配对统计中排除。统一最多4次检索、8次获取；保存全部搜索结果、被拒请求及最终输出。Luna负责调度；被测模型为GLM‑5.3、DeepSeek V4.1 Flash和Kimi kimi-k3-2。后评统一使用GLM‑5.3。</p><p>M11 = 100 × [1−(1−x₁x₂x₃)(1−x₅x₆)(1−x₇)] × (0.7+0.3x₄) × (0.9+0.1x₈)，xᵢ=Mᵢ/5。沿用原系数。核验不可用渠道贡献0；版本不适用时版本因子1；证据只能定区间时传播端点；尚未核实的输入不编造点值。</p><p>这是综合指数，不是正确概率；区间不是统计置信区间。没有硬件执行验证；模型别名可能更新，搜索提供方并未独立锁定；同一自动后评模型存在偏差风险。本页不改写论文。</p><a href="protocol.json">冻结协议</a> · <a href="tasks.json">原题与适用范围</a> · <a href="frozen-skill/references/rules.md">评分规则</a> · <a href="source-index.json">全部检索网址</a> · <a href="review-audit.json">复核记录</a> · <a href="results.json">结构化结果</a></div>'
page+=f'<div class="box">采集技术重试已用尽：{summary["collection_exhausted"]} 项。此类记录保持未完成，不填补评分。<br><a href="paired-summary.json">按模型配对汇总（含排除原因）</a> · <a href="arithmetic-audit.json">独立算术核验</a> · <a href="assessment-status.json">后评完成及技术失败记录</a></div>'
page+='<div class="scroll"><table><tr><th>实际模型</th><th>任务</th><th>生态</th>'+''.join(f'<th>M{i}</th>' for i in range(1,12))+'<th>状态</th><th>证据</th></tr>'+''.join(body)+'</table></div></html>'
(R/'results.html').write_text(page)
print(json.dumps(summary,ensure_ascii=False))
