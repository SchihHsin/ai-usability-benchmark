"""Build a transparent pilot summary from actual run and assessment artifacts."""
from pathlib import Path
import json,html,collections
from prepare_assessment import unpack
R=Path(__file__).resolve().parent
def esc(x):return html.escape(str(x))
rows=[];summary=[]
for d in sorted((R/'runs').iterdir()):
 if not d.is_dir():continue
 events=[json.loads(x) for x in (d/'process.jsonl').read_text().splitlines()];meta=events[0]['metadata'];ev=json.loads((d/'evaluation.json').read_text());rev=ev['revisions'][-1]['evaluation'] if ev.get('revisions') else {};metrics={x['id']:x for x in rev.get('metrics',[])}
 end=next((x for x in events if x['type']=='run_end'),None);answer=unpack(end.get('answer',{})) if end else ''
 record={'run_id':d.name,'task':meta['task_id'],'ecosystem':meta['ecosystem'],'model':meta['model_id'],'completed':end is not None,'metrics':{k:{z:v.get(z) for z in ('score','status','lower','upper','reason')} for k,v in metrics.items()},'quote_issues':rev.get('quote_audit',[]),'issues':rev.get('issues',[])};summary.append(record)
 cells=[]
 for i in range(1,12):
  m=metrics.get('M'+str(i),{});v=m.get('score');cells.append('<td title="'+esc(m.get('reason',m.get('status','pending')))+'">'+(esc(round(v,2)) if v is not None else esc(m.get('status','pending')) )+'</td>')
 rows.append('<tr><td>'+esc(meta['task_id']+' / '+meta['ecosystem'])+'</td><td>'+esc(meta['model_id'])+'</td>'+''.join(cells)+'<td><a href="runs/'+esc(d.name)+'/evaluation.json">评价</a> / <a href="runs/'+esc(d.name)+'/process.jsonl">过程</a></td></tr>')
 rows.append('<tr><td colspan="14"><details><summary>最终输出与逐项评分依据：'+esc(d.name)+'</summary><pre>'+esc(answer)+'</pre>'+''.join('<p><b>'+esc(k)+'</b> '+esc(v.get('reason',''))+'</p>' for k,v in metrics.items())+'</details></td></tr>')
(R/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
conclusion=(R/'conclusion.md').read_text() if (R/'conclusion.md').exists() else '运行中，尚无最终结论。'
body='<h1>三模型 × 三任务试跑</h1><p>GLM-5.3 / DeepSeek V4.1 Flash / Kimi K3.2；模型转换、版本配套、错误诊断，各含CANN/CUDA两侧，共18次。试验副本采用已确认M4，其他档位不变；M11为百分制，系数0.30/0.10。</p><pre>'+esc(conclusion)+'</pre><p>空分保留状态及原因，不补零。自动后评为GLM，不是人工金标准；未执行硬件代码，模型别名不保证后台不可变版本。</p><div class="scroll"><table><tr><th>任务 / 生态</th><th>执行模型</th>'+''.join('<th>M'+str(i)+'</th>' for i in range(1,12))+'<th>原始材料</th></tr>'+''.join(rows)+'</table></div><p><a href="source-index.json">全部搜索网址及获取索引</a> · <a href="collection-audit.json">采集审计</a> · <a href="protocol.json">冻结协议</a> · <a href="frozen-skill/references/rules.md">实际使用规则</a></p>'
(R/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>三模型三任务试跑</title><style>body{font:15px/1.7 system-ui;color:#233047;margin:32px}table{border-collapse:collapse;min-width:1300px}td,th{border:1px solid #dce1e8;padding:9px;text-align:left;vertical-align:top}th{background:#eef3fa}.scroll{overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:16px}details pre{max-height:500px;overflow:auto}a{color:#1766ae}</style>'+body+'</html>')
print(json.dumps({'runs':len(summary),'complete':sum(x['completed'] for x in summary),'scored_metrics':sum(len(x['metrics']) for x in summary)}))
