from pathlib import Path
import json,html,collections,math
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'fit-results.json').read_text());h=html.escape
best=r['models']['both'];a,b=best['a'],best['b'];folds=best['folds'];boots=r['task_bootstrap']
rows=''.join(f'<tr><td>{h(name)}</td><td>{m["a"]:.2f}</td><td>{m["b"]:.2f}</td><td>{m["training_worst_case_mse"]:.4f}</td><td>{m["cv_worst_case_mse"]:.4f}</td></tr>' for name,m in r['models'].items())
fr=''.join(f'<tr><td>{f["held_out"]}</td><td>{f["a"]:.2f}</td><td>{f["b"]:.2f}</td><td>{f["test_worst_case_mse"]:.4f}</td></tr>' for f in folds)
table=''
for d in r['data']:
 lo,hi=d['outcome_interval'];table+=f'<tr><td>{d["case"]}</td><td>{d["group"]}</td><td>{lo*100:.1f}—{hi*100:.1f}%</td><td>{d["input_intervals"][3][0]*5:g}—{d["input_intervals"][3][1]*5:g}</td><td>{d["input_intervals"][7][0]*5:g}</td></tr>'
auto=list((ROOT/'assessments').glob('*.json'));changes=json.loads((ROOT/'adjudication-log.json').read_text());unverified=sum(x['after']=='unverified' for x in changes if isinstance(x['after'],str));cost=sorted({d['input_intervals'][7][0]*5 for d in r['data']})
fragment=f'''<section id="m11-fitting"><h2>M11实际拟合结果 · 2026-09-21</h2>
<p><mark>已完成实际区间拟合、留一任务组验证和因子消融。全样本候选：a={a:.2f}，b={b:.2f}。候选未获足够稳定的验证支持，不自动写入正式Skill，也不声称是最合适的最终系数。</mark></p>
<p>拟合族：M11=100K[1−a(1−M4/5)][1−b(1−M8/5)]。本次全样本区间损失最小的候选为 <strong>100K×({1-a:.2f}+{a:.2f}M4/5)×({1-b:.2f}+{b:.2f}M8/5)</strong>。K及Mi/5保持既有结构，未同时拟合它们。</p>
<h3>本次是真拟合，拟合的是什么</h3><p>已有10份答案，3个任务组A（转换部署）、D（自定义算子）、I（版本配套）。通过WorkBuddy请求并记录GLM-5.3别名，分别评价来源分项和最终答案，共保存{len(auto)}份评价。来源评价不看最终答案；答案评价不看M1—M11、先验回答或权重，但技术内容仍暴露生态。两个评价上下文由同一自动评价模型完成，不是人工金标准，也不是完全独立评价者。</p>
<p>目标是6项任务要求中“答案已提供且有证据支持”的比例；未核实项形成上下界，不按错误处理。未运行硬件代码。外部目标是证据完备性代理，不是实测成功率或包含成本偏好的效用。模型给分/引文仍有错误，复核发现{unverified}项支持判断的引文需继续核验，已降为未知；另按明确内容缺口纠正部分D任务评价。所有原评价与复核记录分别保存。</p>
<p>当前可用{r['n']}份，覆盖{len(r['groups'])}个任务组。具备完整确定输入及确定目标、可进行普通点值拟合的记录数为{r['point_fit']['n'] if r['point_fit'] else 0}。因此本次实施的是<strong>保留不确定性的区间拟合</strong>，不是偷偷用区间中点代替分数。排除记录：{h(json.dumps(r['excluded'],ensure_ascii=False))}。</p>
<h3>拟合与验证结果</h3><p>a、b均在0—1范围以0.01步长搜索，共10,201组。输入和目标均为区间时，优化目标为每条记录可能出现的最坏平方误差，任务组等权。此损失函数是本次保守分析选择，不是文献规定的唯一损失；它可能优先折减不确定性较大的样本，不能据此赋予系数因果含义。</p>
<table><tr><th>候选结构</th><th>a</th><th>b</th><th>训练区间最坏MSE</th><th>留任务组区间最坏MSE</th></tr>{rows}</table>
<p>误差以0—1尺度计算，越小越好；不是实际正确率。no_factors=不加因子；version_only=只拟合版本；cost_only=只拟合成本；both=两者均拟合；original=原0.30/0.10。验证按任务分组，同一任务两生态及重复不跨训练/留出组。该表用于探索性比较，未另设最终独立测试集，不能将选择后的最佳表格误差当成无偏最终泛化成绩。</p>
<h3>两系数模型每次留下不同任务后的结果</h3><table><tr><th>留出的任务</th><th>训练得到a</th><th>训练得到b</th><th>留出误差</th></tr>{fr}</table>
<p>对3个任务组进行全部27种有放回重采样，a范围{min(x['a'] for x in boots):.2f}—{max(x['a'] for x in boots):.2f}，b范围{min(x['b'] for x in boots):.2f}—{max(x['b'] for x in boots):.2f}。这是小样本稳定性诊断，不是可靠置信区间。</p>
<p>若只要求预测区间与目标区间重叠（另一种区间损失），有{r['optimistic_interval_fit']['exact_grid_minimizers']}组网格系数同为最小值；a范围{r['optimistic_interval_fit']['a_range']}，b范围{r['optimistic_interval_fit']['b_range']}。这说明最优值还依赖怎样处理评价不确定性，不能把全样本一个极小值称为唯一真值。</p>
<h3>数据为什么不足以定稿</h3><p>M8只覆盖{h(str(cost))}档，成本变化窄，b容易充当整体缩放因子；A、I各只有两份原始答案，D有更多重复，故按任务等权处理，但独立任务数仍只有3。旧协议、完整Skill旧版和新版混用，模型执行都为DeepSeek系列同一配置标签；没有跨模型/任务泛化证据。来源评分与答案评价还共用同批工具可见返回，并非独立核验的原始网页真值，可能共享错误。</p>
<table><tr><th>匿名记录</th><th>任务组</th><th>答案证据覆盖区间</th><th>M4区间</th><th>M8</th></tr>{table}</table>
<h3>结论与公式状态</h3><p><strong>本轮已经得到可复算的拟合候选，但未得到足以替换正式规则的最优系数。</strong>不把候选写成已验证公式，也不把原0.30/0.10说成拟合获胜。正式规则仍保留先前版本仅用于连续性；本轮未更新正式Skill。要把候选升级为正式系数，优先补齐这10份材料的原文核验与需求级裁定，并补充M8中高档及更多独立任务；不是再次无依据调一组数值。</p>
<h3>文献与依据</h3><p>Hastie、Tibshirani、Friedman（2009），<i>The Elements of Statistical Learning</i>，第7章纸面页219、222—223、241、243、245—247、249：平方误差、模型选择与评价的区别、交叉验证及bootstrap。本轮取得作者公开PDF并核对这些部分，文件SHA256、短摘录和页码存literature-reading.json。<a href="https://hastie.su.domains/ElemStatLearn/">作者公开书籍页</a>。任务分组和区间最坏损失是本次设计，不冒称书中规定。</p>
<p>OECD/JRC（2008）提供综合指标方法框架；FActScore（Min等，2023）启发逐项事实核对，但不证明我们的六项要求、自动评委或代码运行效度。本对话全部17项引用及已撤回用途见下方<a href="#conversation-literature">文献总账</a>。</p>
<p>可复算材料：experiments/m11-fit-20260921/ 下的protocol.json、manifest.json、assessments/、reviewed/、adjudication-log.json、fit.py及fit-results.json。原运行过程不改写；原始含上下文的评价请求与客户端输出保留本地，不随公开摘要上传。</p></section>'''
(ROOT/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>M11拟合结果</title><style>body{font:16px/1.8 system-ui;max-width:1150px;margin:40px auto;padding:0 24px;color:#243047}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:10px;text-align:left}mark{background:#fff0ad}a{color:#245ea0}</style>'+fragment+(ROOT.parents[1]/'reviews/conversation-literature-fragment.html').read_text()+'</html>')
(ROOT.parents[1]/'reviews/m11-fitting-fragment.html').write_text(fragment)
print('Built actual-fit report')
