from pathlib import Path
import json,datetime,hashlib,html,statistics,re
R=Path(__file__).resolve().parent
P=Path('/Users/hsin/Documents/Coding/opknow/experiments/multimodel/e-validation-body-state-20260914')
H=html.escape
out=[];audit=[];durations={}
for f in sorted(P.glob('runs/*/process.jsonl')):
 rows=[json.loads(l) for l in f.read_text().splitlines()];byid={r['id']:r for r in rows};req={r['id']:r for r in rows if r['type']=='tool_request'}
 result=[r for r in rows if r['type']=='tool_result'];counts={role:sum(r['type']=='tool_dispatch' and req.get(r.get('request_id'),{}).get('role')==role for r in rows) for role in ['search','fetch']}
 minutes=(datetime.datetime.fromisoformat(rows[-1]['recorded_at'])-datetime.datetime.fromisoformat(rows[0]['recorded_at'])).total_seconds()/60
 model=rows[0]['metadata']['model_id'];durations.setdefault(model,[]).append(minutes)
 ev=json.loads(f.with_name('evaluation.json').read_text())['revisions'][-1]['evaluation'];sources=ev.get('sources',[])
 frame=[x for x in sources if x.get('source_class')=='official_documentation' and x.get('return_kind')=='frame_only']
 first=next(r for r in result if req[r['request_id']]['role']=='search')
 first_text=first['response']['content'];first_failed=first['tool_status']=='error' or first_text.startswith('Error:')
 for r in result:
  v=r['response'];assert hashlib.sha256(v['content'].encode()).hexdigest()==v['sha256']
 C=sum(counts.values());band=max(1,5-(C-1)//2) if C else None
 entry=dict(run_id=f.parent.name,minutes=round(minutes,2),counts=counts,M8_observed_band=band,official_frame_events=[e for x in frame for e in x.get('event_refs',[])],first_search_failed=first_failed,source_count=len(sources),material_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),scope='旧运行的材料完整性与规则边界检查，不是新协议正式评分')
 audit.append(entry)
 out.append(f'<tr><td><a href="#{H(f.parent.name)}">{H(f.parent.name)}</a></td><td>{minutes:.2f}分钟</td><td>{counts["search"]} / {counts["fetch"]}<br>C={C}，调用档{band}</td><td>{"首次搜索失败：M1不能记1分" if first_failed else "首次搜索列表存在：仍需相关性判定"}<br>已有官方框架观测{len(frame)}次；来源条目{len(sources)}个（非独立计数）</td></tr>')
# actual source responses provide all evidence, but no fake content scores
body='<section id="six-run-review"><h2>六轮旧材料：完成了哪些核对</h2><p>已逐轮核对日志、派发计数、实际返回哈希、来源索引及版本兼容问题。内容项尚未完成整轮人工评分；下面不是新模型正式结果，也不把自动文件检查说成评分有效性验证。</p><div class="tablewrap"><table><thead><tr><th>运行</th><th>实际耗时</th><th>搜索 / 获取</th><th>可核对事实</th></tr></thead><tbody>'+''.join(out)+'</tbody></table></div>'
body+='<h3>对新规则的直接约束</h3><ul><li>M1：GLM CANN首次搜索超时，属于工具故障，不等于没有官方资料。新规则明确记未知，后续恢复单列。</li><li>M2：存在官方框架返回；其他材料不少缺完整参照。不能因返回长或能回答就给5分，当前不强造覆盖总分。</li><li>M3/M6/M10/M11：全文和答案可用，但必须按统一细化需求核对；旧运行评分仍待定，新细化判据只能标为事后示范。</li><li>M4/M9：旧任务未冻结独立版本关系清单，不能追补后声称当时已有。新正式任务须先确定适用性。</li><li>M5：第三方转载与独立原创须分开；已保存的来源条目数不等于新N。</li><li>M7：旧轮为1—5自评，不换算成新概率分档。</li><li>M8：六轮均可按派发统计；Kimi CANN为9次获取，超出旧8次约束。这轮保留诊断价值，不当作新硬预算下合规正式样本。</li></ul>'
body+='<h3>可展开的证据索引</h3><p>以下保留每轮全部已索引获取来源的实际返回，便于核对；来源分类来自旧评价，未经核实的发布主体明确保留原标签，不能只按域名认定内容归属。</p>'
for f in sorted(P.glob('runs/*/process.jsonl')):
 rows=[json.loads(l) for l in f.read_text().splitlines()];byid={r['id']:r for r in rows};ev=json.loads(f.with_name('evaluation.json').read_text())['revisions'][-1]['evaluation']
 body+=f'<details id="{f.parent.name}"><summary>{H(f.parent.name)}：全部来源返回</summary><p><a href="{f.as_uri()}">原始过程文件</a> · <a href="{f.with_name("evaluation.json").as_uri()}">原评价文件</a></p>'
 for src in ev.get('sources',[]):
  body+=f'<p><a href="{H(src["url"])}">{H(src["url"])}</a><br>原分类：{H(src.get("source_class","unknown"))}；原观测：{H(src.get("return_kind","unknown"))}</p>'
  for eid in src.get('event_refs',[]):
   r=byid.get(eid)
   if r and 'response' in r:
    text=r['response']['content'].replace('\\n','\n');body+=f'<details><summary>{H(eid)} · 实际返回全文</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:500px;overflow:auto">{H(text)}</pre></details>'
 body+='</details>'
body+='</section>'
(R/'six-run-review-fragment.html').write_text(body)
(R/'six-run-material-audit-2026-09-20.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
# read-only extract task questions; do not import legacy execution script
src=Path('/Users/hsin/Documents/Coding/opknow/md/18_指标定义与计算方法.md');text=src.read_text();part=text.split('## 2 ·')[1].split('## 3 ·')[0]
pat=re.compile(r'^([A-Z])\n([^\n]+)\nCUDA\n(.*?)\nCANN\n(.*?)(?=\n[A-Z]\n|\n\n上方)',re.M|re.S)
tasks=[]
for m in pat.finditer(part):tasks.append(dict(id=m[1],label=m[2],cuda=m[3].strip(),cann=m[4].strip(),paired=m[1]!='G',note='G CUDA问ROCm迁移，建议不纳入两生态配对' if m[1]=='G' else '待执行前完成任务需求清单；原问句保留'))
assert len(tasks)==26
(R/'task-manifest-review-2026-09-20.json').write_text(json.dumps(dict(status='planning_only_not_executed',source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),tasks=tasks,recommended_runs=153),ensure_ascii=False,indent=2))
print(json.dumps({'runs_checked':len(audit),'mean_minutes':statistics.mean([x['minutes'] for x in audit]),'model_means':{k:statistics.mean(v) for k,v in durations.items()},'tasks':len(tasks)},ensure_ascii=False))
