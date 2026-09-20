#!/usr/bin/env python3
"""Render M11 artifacts without adding analysis or inventing missing results."""
from pathlib import Path
import html, json
ROOT = Path(__file__).resolve().parent

def load(name, default=None):
    p=ROOT/name
    if not p.exists(): return default
    try: return json.loads(p.read_text())
    except (OSError,json.JSONDecodeError): return default

def e(v): return html.escape('' if v is None else str(v))
def val(v):
    if v is None: return '—'
    if isinstance(v,float): return f'{v:.6g}'
    return str(v)
def table(headers, rows):
    return '<table><thead><tr>'+''.join(f'<th>{e(x)}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{e(val(x))}</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'
def md_table(headers, rows):
    return '\n'.join(['| '+' | '.join(map(str,headers))+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(val(x).replace('|','\\|') for x in r)+' |' for r in rows])
def section(title,body): return f'<h2>{e(title)}</h2>{body}'

protocol=load('protocol.json',{}) or {}; audit=load('collection-audit.json',{}) or {}
dev=load('development-data.json',[]) or []; excluded=load('development-data-exclusions.json',[]) or []
dev_input=load('assessment-input/development.json',[]) or []
reviewed_outcomes=[]
for _p in (ROOT/'reviewed'/'development').glob('*-outcome.json'):
    try: reviewed_outcomes.append(json.loads(_p.read_text()))
    except (OSError,json.JSONDecodeError): pass
req_counts={}
for _x in reviewed_outcomes:
    for _q in _x.get('requirements',[]): req_counts[_q.get('status','unknown')]=req_counts.get(_q.get('status','unknown'),0)+1
raw_supported=sum(1 for _x in reviewed_outcomes for _q in _x.get('requirements',[]) if _q.get('raw_status')=='supported')
reviewed_total=len(reviewed_outcomes); requirement_total=sum(req_counts.values())
outcome_point=sum(1 for _r in dev if _r.get('outcome_interval',[None,None])[0]==_r.get('outcome_interval',[None,None])[1])
m2_point=sum(1 for _r in dev if _r.get('input_intervals',[[None,None]]*8)[1][0]==_r.get('input_intervals',[[None,None]]*8)[1][1])
m7_full=sum(1 for _r in dev if _r.get('input_intervals',[[None,None]]*8)[6]==[1,5])
case_budget={x.get('case'): x.get('budget') for x in dev_input}
ex_budget={b: sum(1 for x in excluded if case_budget.get(x.get('case'))==b) for b in sorted({case_budget.get(x.get('case')) for x in excluded if case_budget.get(x.get('case'))})}
in_budget={b: sum(1 for x in dev if case_budget.get(x.get('case'))==b) for b in sorted({case_budget.get(x.get('case')) for x in dev if case_budget.get(x.get('case'))})}
included_total=len(dev); candidate_total=len(dev)+len(excluded)
frozen=load('frozen-selection.json'); held=load('heldout-data.json',[]) if frozen is not None else []
results=load('fit-results.json'); sensitivity=load('sensitivity/fit-results.json'); sensitivity_validation=load('sensitivity/validation-results.json'); validation=load('validation-results.json'); literature=load('literature.json',{}) or {}
summary=audit.get('summary',{}); complete=summary.get('complete',0)
status='留出验证完成' if validation else '系数已冻结，等待留出验证' if frozen is not None else '采集完成，等待拟合' if complete else '采集中/尚未拟合'
fit=(frozen or {}).get('fit',{})
model='M = 100 × K × (1 − a × (1 − M4/5)) × (1 − b × (1 − M8/5)); K = 1 − (1 − (M1/5)(M2/5)(M3/5))(1 − (M5/5)(M6/5))(1 − M7/5).'
parts=[f"<h1>M11 uniform fit · 2026-09-21</h1><p class='status'>状态：<strong>{e(status)}</strong></p>"]
parts.append("<p class='notice'><strong>实验已完成，但没有确定出稳定优于原系数的新系数。</strong>当前保留 a=0.30、b=0.10 作为工作基线；正式 Skill 未改。<a href='conclusion.md'>最终结论、公式与依据</a></p>" if validation and sensitivity_validation else '')
parts.append(f"<p>{e('冻结选择：'+str(fit) if frozen is not None else '尚无冻结系数；不得从旧实验推断新结果。')}</p>")
parts.append(section('公式、协议与候选族',f'<p>{e(model)} 所有 Mi 先按原始 1–5 分除以 5。</p><p>历史 baseline 为 <code>a=0.30,b=0.10</code>，仅作预先指定对照；本轮结果暂不支持用新拟合系数替换 baseline，也不表示 baseline 已被证明最优。候选五族为 no_factors、version_only、cost_only、both、original；a、b 使用 0.01 网格，按开发任务组等权的 worst-case squared endpoint error，并以 leave-one-development-task-group-out CV 选择。留出数据不参与选择；结果不宣称通用最优。</p>'))
if frozen is not None:
    parts.append(table(['字段','值'],[['selected_family',frozen.get('selected_family')],['a',fit.get('a')],['b',fit.get('b')],['development input SHA256',frozen.get('input_sha256')],['protocol SHA256',frozen.get('protocol_sha256')],['development cases',', '.join(frozen.get('development_cases',[]))]]))
else: parts.append("<p class='notice'>冻结文件不存在，当前不报告新系数。</p>")
parts.append(section('样本、留出边界与排除',f"<p>开发纳入 {included_total}/{candidate_total} 个候选样本；自动统计预算分布：纳入 {e(in_budget)}，排除 {e(ex_budget)}。协议预期 {e(protocol.get('expected_runs','—'))} 次运行；开发任务：{e(protocol.get('development',[]))}；留出任务：{e(protocol.get('heldout',[]))}。任务组内保留生态与预算条件，未知引文不静默记为零。</p><p>开发集区间结构：outcome_interval 为点值 {outcome_point}/{included_total}，M2 为点值 {m2_point}/{included_total}，M7 为 [1,5] {m7_full}/{included_total}。复核后的 {reviewed_total} 个样本共 {requirement_total} 条需求：supported={req_counts.get('supported',0)}、unverified={req_counts.get('unverified',0)}、absent={req_counts.get('absent',0)}；其中 {raw_supported} 条由 supported 因引文审计转为 unverified。</p>"))
parts.append(table(['开发 case','group','split','budget'],[[r.get('case'),r.get('group'),r.get('split','development'),r.get('budget')] for r in dev]) if dev else '<p>development-data.json 尚不存在。</p>')
if excluded: parts.append('<details><summary>明确排除的开发样本（不会进入拟合）</summary>'+table(['case','reason'],[[x.get('case'),x.get('reason')] for x in excluded])+'</details>')
held_excluded=load('heldout-data-exclusions.json',[]) if frozen is not None else []
if held_excluded: parts.append(section('留出排除记录',table(['case','reason'],[[x.get('case'),x.get('reason')] for x in held_excluded])))
if frozen is not None: parts.append('<details><summary>留出样本（冻结后读取）</summary>'+(table(['case','group','split','budget'],[[r.get('case'),r.get('group'),r.get('split','heldout'),r.get('budget')] for r in held]) if held else '<p>heldout-data.json 尚不存在或为空。</p>')+'</details>')
else: parts.append("<p class='notice'>冻结选择前不读取或评价 heldout-data.json。</p>")
if results:
    models=results.get('models',{}); rows=[[k,v.get('a'),v.get('b'),v.get('parameter_count'),v.get('training_worst_case_mse'),v.get('cv_worst_case_mse'),len(v.get('folds',[]))] for k,v in models.items()]
    parts.append(section('候选族 CV 与冻结拟合',table(['族','a','b','参数数','开发 worst MSE','LOTO CV MSE','fold 数'],rows)))
    for fam,v in models.items():
        folds=v.get('folds',[])
        if folds: parts.append(f'<details><summary>{e(fam)}：逐任务组留出 fold</summary>'+table(['held-out group','a','b','test worst MSE','cases'],[[x.get('held_out'),x.get('a'),x.get('b'),x.get('test_worst_case_mse'),', '.join(x.get('test_cases',[]))] for x in folds])+'</details>')
    boot=results.get('task_bootstrap',[])
    if boot:
        av=[x.get('a') for x in boot if x.get('a') is not None]; bv=[x.get('b') for x in boot if x.get('b') is not None]
        q=lambda z,p: sorted(z)[min(len(z)-1,max(0,int(round((len(z)-1)*p))))] if z else None
        parts.append(section('系数 task-group bootstrap','<p>固定种子、1000 次任务组重采样；这是描述性稳定性范围，不是置信区间，也不是通用最优性证明。</p>'+('<p class=\"notice\">selected_family=original 是预先固定的历史候选，程序对每次 bootstrap 都返回 a=0.30、b=0.10；这个零宽度分布是候选约束造成的，不能当作系数稳定性证据。</p>' if results.get('selected_family')=='original' else '')+table(['系数','均值','P05','P50','P95','重复数'],[['a',sum(av)/len(av) if av else None,q(av,.05),q(av,.5),q(av,.95),len(av)],['b',sum(bv)/len(bv) if bv else None,q(bv,.05),q(bv,.5),q(bv,.95),len(bv)]])))
    sens=results.get('interval_distance_sensitivity',{})
    if sens: parts.append(section('替代损失敏感性（描述性）',table(['族','a','b','interval-distance MSE'],[[k,v.get('a'),v.get('b'),v.get('mse')] for k,v in sens.items()])))
else: parts.append(section('候选族 CV、bootstrap 与敏感性',"<p class='notice'>fit-results.json 尚不存在：保持“尚未拟合”，不补造候选系数、fold 或 bootstrap 数值。</p>"))
if sensitivity:
    sm=sensitivity.get('models',{}); primary_original=sm.get('original',{}); ss=sm.get('cost_only',{})
    parts.append(section('独立后设敏感性（answer-id 审计修正）',f"<p>这是独立的后设敏感性重跑，输入为修正 answer_event_id 的 eligible 开发记录；它不是原预设 primary，也不改变原 primary 结果或选择协议。结果只用于显示引用 ID 审计敏感性，不能据此宣称 M4 不重要、也不能提前做最终采纳判断。</p>"+table(['分析','族','a','b','CV worst MSE'],[['sensitivity rerun original baseline', 'original', primary_original.get('a'), primary_original.get('b'), primary_original.get('cv_worst_case_mse')],['sensitivity','cost_only',ss.get('a'),ss.get('b'),ss.get('cv_worst_case_mse')]])))
if sensitivity_validation:
    sv=sensitivity_validation; sb=sv['bootstrap_selected_minus_original']
    parts.append(section('Answer-ID sensitivity: held-out validation',table(['Item','Value'],[['n',sv['n']],['selected MSE',sv['heldout_group_mse']],['original MSE',sv['baseline_original_group_mse']],['selected-original P05',sb['p05']],['selected-original P95',sb['p95']]])))
if validation:
    b=validation.get('bootstrap_selected_minus_original',{}); parts.append(section('冻结后的留出比较',table(['项目','值'],[['留出 n',validation.get('n')],['selected family group MSE',validation.get('heldout_group_mse')],['original baseline group MSE',validation.get('baseline_original_group_mse')],['selected − baseline bootstrap mean',b.get('mean')],['描述性 P05–P95 范围（非置信区间）',f"{b.get('p05')} — {b.get('p95')}"],['留出 cases',', '.join(validation.get('rows',[]))]])))
    if validation.get('family_group_mse'): parts.append(table(['冻结前已存在的族/基线','held-out group MSE'],[[k,v] for k,v in validation['family_group_mse'].items()]))
    if validation.get('budget_errors'): parts.append(table(['budget','n','selected MSE','original MSE'],[[k,v.get('n'),v.get('selected_mse'),v.get('original_mse')] for k,v in validation['budget_errors'].items()]))
elif frozen is not None: parts.append(section('留出比较','<p>已冻结选择，但尚未生成 validation-results.json；不提前评价留出结果。</p>'))
parts.append(section('采集核查',table(['项目','结果'],[[k,v] for k,v in summary.items()]) if summary else '<p>collection-audit.json 尚不存在。</p>'))
refs=''.join(f"<li><a href='{e(x.get('url',''))}'>{e(x.get('source'))}</a>：{e(x.get('supports',''))}</li>" for x in literature.get('method_references',[]))
parts.append(section('限制与来源',f'<ul>{refs}</ul><ul><li>自动评委是证据支持的答案质量代理，不是人工金标准；无硬件执行，也不提供概率校准。</li><li>区间和 bootstrap 范围用于描述性稳定性，不是置信区间；系数是本批条件下的冻结结果，不宣称通用最优。</li><li>预算是预先指定的条件性设计，不是文献证明的最优预算；单一生成模型、每格单次运行，任务难度未必相等。</li><li>worst-case 区间损失取保守的端点最大误差，不建模区间相关性；宽区间可能显著影响系数。</li><li>m2_documents 没有逐文档语义校验，code_inspection 标签来自自动模型判断；精确引文只校验存在性。</li><li>真实 alias 不保证不可变后端身份；旧实验仅作历史链接，上一轮拟合系数不参与本轮选择。</li></ul>'))
parts.append("<p><a href='collection-audit.json'>完整审计</a> · <a href='search-index.json'>搜索索引</a> · <a href='process-hashes.json'>原始记录哈希</a> · <a href='paper-methods-results.md'>论文方法与结果材料</a></p>")
css="body{font:16px/1.65 system-ui;max-width:1150px;margin:32px auto;padding:0 22px;color:#243047}h1{font-size:30px}.status{padding:12px;background:#eef4ff;border-left:4px solid #3574d3}.notice{background:#fff3d8;padding:12px}table{border-collapse:collapse;width:100%;margin:12px 0}th,td{border:1px solid #d6dce6;padding:7px;text-align:left;vertical-align:top}th{background:#f2f5f9}a{color:#1769aa}code{background:#f1f3f6;padding:2px 4px}details{margin:10px 0}"
(ROOT/'report.html').write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>M11 uniform fit</title><style>"+css+'</style>'+''.join(parts)+'</html>')
md=['# M11 uniform fit 结果（2026-09-21）',f'状态：**{status}**','','## 公式与选择',model,'','历史 baseline：`a=0.30,b=0.10`，仅作预先指定对照；本轮暂不支持用新拟合系数替换 baseline，也不表示 baseline 已被证明最优。候选五族和 leave-one-development-task-group-out 选择按 `protocol.json` 执行。留出前冻结族与系数，结果不宣称通用最优。']
if frozen is None: md += ['', '当前没有 `frozen-selection.json`，因此不报告新系数，也不读取留出数据。']
else: md += ['',f"冻结选择：`{frozen.get('selected_family')}`，a={val(fit.get('a'))}，b={val(fit.get('b'))}。",f"开发输入 hash：`{frozen.get('input_sha256')}`。"]
md += ['','## 样本与排除',f"开发纳入 {included_total}/{candidate_total} 个候选样本；自动统计预算分布：纳入 {in_budget}，排除 {ex_budget}。协议预期运行数：{val(protocol.get('expected_runs'))}；开发任务：{val(protocol.get('development'))}；留出任务：{val(protocol.get('heldout'))}。",f"区间结构：outcome 点值 {outcome_point}/{included_total}，M2 点值 {m2_point}/{included_total}，M7 为 [1,5] {m7_full}/{included_total}。复核后的 {reviewed_total} 个样本共 {requirement_total} 条需求：supported={req_counts.get('supported',0)}、unverified={req_counts.get('unverified',0)}、absent={req_counts.get('absent',0)}；其中 {raw_supported} 条由 supported 因引文审计转为 unverified。"]
if dev: md += ['' ,md_table(['case','group','split','budget'],[[r.get('case'),r.get('group'),r.get('split','development'),r.get('budget')] for r in dev])]
if excluded: md += ['','明确排除（不进入拟合）：',md_table(['case','reason'],[[x.get('case'),x.get('reason')] for x in excluded])]
if frozen is not None and held: md += ['','冻结后读取的留出样本：',md_table(['case','group','split','budget'],[[r.get('case'),r.get('group'),r.get('split','heldout'),r.get('budget')] for r in held])]
if results:
    md += ['','## 候选族 CV',md_table(['族','a','b','开发 worst MSE','LOTO CV MSE'],[[k,v.get('a'),v.get('b'),v.get('training_worst_case_mse'),v.get('cv_worst_case_mse')] for k,v in results.get('models',{}).items()])]
    boot=results.get('task_bootstrap',[]); md += ['','## 系数 bootstrap','固定种子、1000 次任务组重采样；P05–P95 是描述性范围，不是置信区间。若 selected_family=original，a=0.30、b=0.10 的零宽度来自固定候选约束，不是稳定性证据。',md_table(['系数','均值','P05','P50','P95'],[['a',(sum(x['a'] for x in boot)/len(boot) if boot else None),(sorted(x['a'] for x in boot)[int(.05*(len(boot)-1))] if boot else None),(sorted(x['a'] for x in boot)[len(boot)//2] if boot else None),(sorted(x['a'] for x in boot)[int(.95*(len(boot)-1))] if boot else None)],['b',(sum(x['b'] for x in boot)/len(boot) if boot else None),(sorted(x['b'] for x in boot)[int(.05*(len(boot)-1))] if boot else None),(sorted(x['b'] for x in boot)[len(boot)//2] if boot else None),(sorted(x['b'] for x in boot)[int(.95*(len(boot)-1))] if boot else None)]])]
else: md += ['','## 拟合结果','`fit-results.json` 尚不存在，候选族、fold 和 bootstrap 保持“尚未拟合”。']
if validation:
    b=validation.get('bootstrap_selected_minus_original',{}); md += ['','## 留出比较',md_table(['项目','值'],[['n',validation.get('n')],['selected MSE',validation.get('heldout_group_mse')],['original MSE',validation.get('baseline_original_group_mse')],['selected−baseline mean',b.get('mean')],['描述性 P05–P95（非置信区间）',f"{b.get('p05')} — {b.get('p95')}"]])]
if sensitivity:
    sm=sensitivity.get('models',{}).get('cost_only',{}); po=sensitivity.get('models',{}).get('original',{})
    md += ['', '## 独立后设敏感性', f"answer_event_id 的 exact-final / event-ID 审计修正后，独立重跑选择 {sensitivity.get('selected_family')}（a={val(sensitivity.get('fit',{}).get('a'))}, b={val(sensitivity.get('fit',{}).get('b'))}），其 CV worst MSE={val(sm.get('cv_worst_case_mse'))}；同一敏感性输入下 original baseline 的 CV worst MSE={val(po.get('cv_worst_case_mse'))}。该分析不是原预设 primary，不用于宣称 M4 不重要，也不提前作最终采纳判断。"]
md += ['','## 方法与结果叙述',f'本研究对每个自动生成答案执行后评：六项预先定义的任务需求分别记录支持、缺失、矛盾或未核验状态，再按 supported/6 至 (supported+unverified)/6 合成答案质量区间，保留可辩护的上下界（开发集仅 {outcome_point}/{included_total} 个 outcome 为点值，M2 仅 {m2_point}/{included_total} 个点值，M7 有 {m7_full}/{included_total} 个 [1,5] 区间）；以任务组为留出单位，生态与预算条件留在组内。开发集纳入 {included_total}/{candidate_total} 个候选样本，排除原因逐条保留；选择只在开发集进行，冻结后才可评估留出集。候选族通过 leave-one-development-task-group-out CV 比较，损失为区间端点的保守 worst-case 平方误差；task-group bootstrap 只作描述性稳定性。自动后评是证据支持的答案质量代理，不是人工金标准。']
md += ['','## 限制','- 自动评委不是人工金标准；指标是答案质量代理，不是硬件成功率或校准概率。','- bootstrap 与区间用于描述性稳定性，不能证明通用最优。','- 预算是条件性设计；单一生成模型、每格单次运行，任务难度未必相等。','- worst-case 区间损失取保守的端点最大误差，不建模区间相关性；宽区间可能显著影响系数。','- m2_documents 没有逐文档语义校验，code_inspection 标签来自自动模型判断；精确引文只校验存在性。','- 无硬件执行；未知引文不静默记零；上一轮拟合系数不参与本轮。','','## 文献 ledger']
for x in literature.get('method_references',[]): md.append(f"- [{x.get('source')}]({x.get('url','')})：{x.get('supports','')}")
(ROOT/'paper-methods-results.md').write_text('\n'.join(md)+'\n')
print(f'generated {ROOT/"report.html"} and {ROOT/"paper-methods-results.md"}')

if sensitivity_validation:
    sv=sensitivity_validation; sb=sv['bootstrap_selected_minus_original']
    with (ROOT/'paper-methods-results.md').open('a') as f:
        f.write('\n## Answer-ID sensitivity: held-out validation\n'+md_table(['Item','Value'],[['n',sv['n']],['selected MSE',sv['heldout_group_mse']],['original MSE',sv['baseline_original_group_mse']],['selected-original P05',sb['p05']],['selected-original P95',sb['p95']]])+'\n')

if (ROOT/'conclusion.md').exists():
    with (ROOT/'paper-methods-results.md').open('a') as f: f.write('\n'+(ROOT/'conclusion.md').read_text()+'\n')
md_path=ROOT/'paper-methods-results.md'
md_path.write_text(md_path.read_text().rstrip()+'\n')
