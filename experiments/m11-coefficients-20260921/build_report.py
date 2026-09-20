from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results.json').read_text())
local=[x for x in r['grid_results'] if .2<=x['a']<=.4 and .05<=x['b']<=.15]
rows=''.join(f'<tr><td>{t}</td><td>{r["task_gap_ranges"][t]["baseline"]:.2f}</td><td>{r["task_gap_ranges"][t]["min"]:.2f} ～ {r["task_gap_ranges"][t]["max"]:.2f}</td></tr>' for t in r['pair_reversal_tasks'])
html=f'''<section id="m11-coefficient-decision"><h2>M11公式与系数定稿 · 2026-09-21</h2>
<p><mark>本轮固定版本权重a=0.30、成本权重b=0.10；保留既有公式，不删除因子、不重新拟合权重。它们是固定报告设置，不能称为经数据证明的最优系数。</mark></p>
<p>xi=Mi/5；OFF=x1×x2×x3；SEC=x5×x6；OWN=x7；K=1−(1−OFF)(1−SEC)(1−OWN)。</p>
<p><strong>M11=100×K×(0.7+0.3×M4/5)×(0.9+0.1×M8/5)</strong></p>
<p>M11为连续综合指数，不是正确概率；M9/M10独立报告。M4由5降到1，版本因子由1降至0.76；M8由5降到1，成本因子由1降至0.92。两项均最低时，合计因子0.6992，即相对K折减30.08%。这解释系数含义，不证明该幅度最优。</p>
<h3>实际做了什么</h3><p>冻结旧版score_metrics.py生成的26个任务×两生态共52组历史分项，a遍历0—0.50、b遍历0—0.20，均以0.01步长检查，共{r['grid']['points']}组。范围是透明披露的压力检查设置，不是文献推荐范围；网格占比不是发生概率。历史M2、M7、M8与新规则不同，受阻沿用历史映射，仅作旧数据复算，未改旧记录。</p>
<table><tr><th>检查项</th><th>结果</th><th>可以解释为</th></tr>
<tr><td>CUDA−CANN任务平均差</td><td>原式{r['baseline_mean_cuda_minus_cann']:.2f}分；全网格{r['mean_gap_range'][0]:.2f}～{r['mean_gap_range'][1]:.2f}分</td><td>这批旧数据的总体方向未反转，差距大小随权重变化</td></tr>
<tr><td>单任务生态排序</td><td>{r['grid_points_with_pair_reversal']}组权重至少出现一次反转，涉及G、L、N、Q、T</td><td>不能声称全部任务对权重稳健</td></tr>
<tr><td>52组分数的排序相关</td><td>相对原式的Spearman最低{r['minimum_spearman']:.3f}</td><td>细粒度排序会受权重影响</td></tr>
<tr><td>单个分数最大变化</td><td>{r['maximum_score_change']:.2f}分</td><td>绝对分值不能当作权重无关事实</td></tr>
<tr><td>补充近邻检查</td><td>a=0.20—0.40，b=0.05—0.15，共{len(local)}组；任务N仍可反转，最低相关{min(x['spearman_vs_baseline'] for x in local):.3f}</td><td>这是额外诊断范围，不能用其较稳定的结果替换主检查</td></tr></table>
<h3>发生反转的任务</h3><table><tr><th>历史任务ID</th><th>原式差值</th><th>全网格差值范围（CUDA−CANN）</th></tr>{rows}</table>
<h3>为什么没有给出一个“拟合最优值”</h3><p>现有4次完整Skill A/B采集尚无完整的新规则M1—M8分数，也没有独立答案质量标签或外部效用目标。历史分数不是外部真值；不能拿原M11、自评分数或期望生态排名作为优化目标。敏感性分析检验依赖程度，不识别最优权重。本轮选择保留原权重，是避免无依据改变已确认的构念；不是因为这组权重能维持某侧优势。</p>
<h3>文献依据及核验范围</h3><p>OECD/JRC (2008), <i>Handbook on Constructing Composite Indicators: Methodology and User Guide</i>，用于综合指标构建、权重与敏感性分析的方法框架。<a href="https://doi.org/10.1787/9789264043466-en">DOI</a> · <a href="https://publications.jrc.ec.europa.eu/repository/handle/JRC47008">JRC官方书目及摘要</a>。本轮核验了JRC官方书目与摘要；OECD全文请求403，未新增全文阅读或逐页引文。该文献不证明0.30/0.10最优，也不规定本次网格范围。</p>
<p>噪声OR采用此前已确认的渠道兜底结构。没有从本次权重检查推导渠道独立性，也没有把Mi/5解释为真实概率。本轮未新核验Pearl著作正文，故不增补未经核对的原文或页码。</p>
<h3>可直接写入方法的说明</h3><p>“本研究使用预先固定的版本修正权重0.30和检索成本修正权重0.10，计算0—100知识支撑综合指数。系数不作为经验估计或正确概率参数。在历史分项上开展权重敏感性分析，披露总体差异范围及发生方向变化的任务；该分析不替代新版量规验证。综合结果与分项共同呈现，权重敏感任务不作无条件优劣判断。”</p>
<p>复算材料：experiments/m11-coefficients-20260921/legacy-inputs.json、analyze.py、results.json。原始来源路径和SHA256保存在输入快照；运行python3 analyze.py可复算。所有内容均为系数检查，未启动或声称完成新的模型实验。</p></section>'''
(ROOT/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>M11系数检查</title><style>body{font:16px/1.8 system-ui;max-width:1080px;margin:40px auto;padding:0 24px;color:#223}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:10px;text-align:left}mark{background:#fff0ad}a{color:#2464a5}</style>'+html+'</html>')
(ROOT.parents[1]/'reviews/m11-coefficients-fragment.html').write_text(html)
