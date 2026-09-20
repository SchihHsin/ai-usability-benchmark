#!/usr/bin/env python3
"""Build the transparent M11 batch report from local artifacts only."""
from pathlib import Path
import html, json

ROOT=Path(__file__).resolve().parent
def load(name, default=None):
    p=ROOT/name
    if not p.exists(): return default
    try: return json.loads(p.read_text())
    except Exception: return default
def esc(x): return html.escape(str(x))
def table(headers, rows):
    return '<table><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</table>'

protocol=load('protocol.json',{}); order=load('order.json',{}); frozen=load('frozen-selection.json'); validation=load('validation-results.json')
audit=load('collection-audit.json',{}) or {}
dev=load('development-data.json',[]) or []
has_frozen=frozen is not None
# Held-out content is intentionally not read until a frozen selection exists.
held=load('heldout-data.json',[]) if has_frozen else []
literature=load('literature.json',{}) or {}
status='已冻结并可验证' if has_frozen else '采集中/尚未拟合'
fit_text='尚无冻结系数；不得从旧实验推断新结果。' if not has_frozen else f"冻结族={frozen.get('selected_family')}，a={frozen.get('fit',{}).get('a')}，b={frozen.get('fit',{}).get('b')}。"
model='M = 100 × K × (1 − a × (1 − M4/5)) × (1 − b × (1 − M8/5))；K = 1 − (1 − (M1/5)(M2/5)(M3/5))(1 − (M5/5)(M6/5))(1 − M7/5)。所有 Mi 先按原始 1–5 分除以 5。'
sections=[]
sections.append(f'<h1>M11 uniform fit · 2026-09-21</h1><p class="status">状态：<strong>{status}</strong></p><p>{esc(fit_text)}</p>')
sections.append('<h2>预注册公式与候选</h2><p>'+esc(model)+'</p><p>历史 baseline 为 a=0.30、b=0.10，仅作对照。本轮候选五族：no_factors、version_only、cost_only、both、original；a、b 按 0.01 网格搜索，组等权，按任务组 leave-one-task-out 选择。上一轮拟合系数不作为初始化或选择依据。</p>')
if has_frozen:
    sections.append(table(['字段','值'],[['selected_family',frozen.get('selected_family')],['a',frozen.get('fit',{}).get('a')],['b',frozen.get('fit',{}).get('b')],['development input SHA256',frozen.get('input_sha256')],['protocol SHA256',frozen.get('protocol_sha256')]]))
else: sections.append('<p class="notice">冻结文件不存在，开发集与留出集均不输出拟合系数或留出结论。</p>')
sections.append('<h2>开发设计与数据边界</h2><p>协议预期 48 次运行：8 个开发任务、4 个留出任务，每任务包含两个生态与两种预算条件。任务组等权，生态与预算行留在同一任务组内。目标是证据支持的答案质量代理，不是硬件成功率、性能或校准概率。</p>')
if dev: sections.append(table(['case','group','split'],[[r.get('case'),r.get('group'),r.get('split','development')] for r in dev]))
else: sections.append('<p>development-data.json 尚不存在。</p>')
if has_frozen and validation:
    vr=[['n',validation.get('n')],['冻结选择 MSE',validation.get('heldout_group_mse')],['原始 baseline MSE',validation.get('baseline_original_group_mse')],['bootstrap selected−baseline 90%区间',f"{validation.get('bootstrap_selected_minus_original',{}).get('p05')} — {validation.get('bootstrap_selected_minus_original',{}).get('p95')}"],['cases',', '.join(validation.get('rows',[]))]]
    sections.append('<h2>留出比较</h2>'+table(['指标','值'],vr))
elif has_frozen: sections.append('<h2>留出比较</h2><p>已冻结选择，但尚未生成 validation-results.json。</p>')
else: sections.append('<h2>留出比较</h2><p>冻结选择前不读取或评价 heldout-data.json。</p>')
sections.append('<h2>稳定性与敏感性</h2><p>报告应列出每个候选族的训练损失、每个留一任务组 fold、固定种子 1000 次任务 bootstrap，以及区间距离损失敏感性。若 fit-results.json 不存在，这些字段保持“尚未拟合”，不补造数值。</p>')
results=load('fit-results.json')
if results:
    rows=[]
    for k,v in results.get('models',{}).items(): rows.append([k,v.get('a'),v.get('b'),v.get('training_worst_case_mse'),v.get('cv_worst_case_mse')])
    sections.append(table(['族','a','b','开发 worst MSE','LOTO MSE'],rows))
else: sections.append('<p class="notice">fit-results.json 尚不存在：候选系数、fold 稳定性与 bootstrap 结果尚未产生。</p>')
sections.append('<h2>来源与限制</h2><ul><li>来源文献：'+''.join(f'<li><a href="{html.escape(x.get("url",""))}">{esc(x.get("source"))}</a></li>' for x in literature.get('method_references',[]))+'</ul><p>文献支持交叉验证、平方误差、bootstrap 与综合指标敏感性披露，不支持本轮具体预算、样本量、系数或概率解释。模型使用真实请求别名与客户端返回标识，但别名不保证不可变后端身份。未知引文与排除比例应从 collection-audit.json（若存在）报告；本批不把未知静默记为零。无硬件验证，自动评委不是人工金标准，也不提供概率校准。</p><p>旧实验仅作为<a href="../m11-fit-20260921/build_report.py">历史链接</a>，旧系数不作为本轮结果。</p>')
if audit: sections.append('<p>collection-audit 摘要：'+esc(json.dumps(audit,ensure_ascii=False))+'</p>')
css='body{font:16px/1.7 system-ui;max-width:1100px;margin:32px auto;padding:0 22px;color:#243047}h1{font-size:30px}.status{padding:12px;background:#eef4ff;border-left:4px solid #3574d3}.notice{background:#fff3d8;padding:12px}table{border-collapse:collapse;width:100%;margin:12px 0}th,td{border:1px solid #d6dce6;padding:7px;text-align:left}th{background:#f2f5f9}a{color:#1769aa}'
html_out='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>M11 uniform fit</title><style>'+css+'</style>'+''.join(sections)+'</html>'
(ROOT/'report.html').write_text(html_out)
md=['# M11 uniform fit 结果（2026-09-21）',f'状态：**{status}**', '', fit_text, '', '## 公式', model, '', '历史 baseline：`a=0.30, b=0.10`，仅作对照。候选五族及 LOTO 选择按 protocol.json 执行。']
if not has_frozen: md += ['', '当前没有 `frozen-selection.json`，因此不报告新系数，不读取留出数据，也不把旧实验系数当作本轮结果。']
else: md += ['', f"冻结选择：`{frozen.get('selected_family')}`，a={frozen.get('fit',{}).get('a')}，b={frozen.get('fit',{}).get('b')}。", f"开发输入 hash：`{frozen.get('input_sha256')}`"]
md += ['', '## 研究限制', '- 目标是证据支持的答案质量代理，不是硬件成功率或校准概率。', '- 预算与任务设计是条件性设计，不是文献证明的最优方案。', '- 模型真实 alias 不能保证不可变后端身份；自动评委不是人工金标准。', '- 无硬件执行；未知引文不静默记零；旧实验仅作历史链接。', '', '## 文献 ledger']
for x in literature.get('method_references',[]): md.append(f"- [{x.get('source')}]({x.get('url','')})：{x.get('supports','')}")
(ROOT/'paper-methods-results.md').write_text('\n'.join(md)+'\n')
print(f'generated {ROOT/"report.html"} and {ROOT/"paper-methods-results.md"}')
