"""Read-only live inventory; write a small derived progress report."""
from pathlib import Path
import json,html,datetime
R=Path(__file__).resolve().parent
p=json.loads((R/'protocol.json').read_text());rows=[]
for m in p['models']:
 ledger=R/('ledger-'+m+'.jsonl');latest={}
 if ledger.exists():
  for line in ledger.read_text().splitlines():
   r=json.loads(line);latest[(r['task'],r['ecosystem'])]=r
 complete=sum(r.get('completed',False) for r in latest.values());fail=sum(not r.get('completed',False) for r in latest.values())
 rows.append({'model':m,'completed':complete,'expected':52,'technical_attention':fail})
a=list((R/'assessments/development').glob('*.json'))
result={'updated':datetime.datetime.now().isoformat(timespec='seconds'),'collection':rows,'completed':sum(r['completed'] for r in rows),'expected':156,'assessment_files':len(a),'warning':'Collection completion is not assessment completion; G is a separate migration analogy.'}
(R/'status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
body=''.join(f'<tr><td>{html.escape(r["model"])}</td><td>{r["completed"]}/52</td><td>{r["technical_attention"]}</td></tr>' for r in rows)
(R/'progress.html').write_text('<!doctype html><meta charset="utf-8"><title>全量实验进度</title><style>body{max-width:850px;margin:50px auto;font:17px/1.8 system-ui;color:#24313d}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:12px;text-align:left}</style><h1>全量实验进度</h1><p>'+str(result['completed'])+'/156 次采集完成；后评文件 '+str(len(a))+' 份（不等于有效评分数）。</p><table><tr><th>实际模型</th><th>采集完成</th><th>需检查</th></tr>'+body+'</table><p>G为跨平台迁移类比，单列分析。采集完成不等于评分复核完成。</p><p>更新：'+result['updated']+'</p><p><a href="protocol.json">协议</a> · <a href="tasks.json">26项任务</a> · <a href="validation.json">启动前检查</a></p>')
print(json.dumps(result,ensure_ascii=False))
