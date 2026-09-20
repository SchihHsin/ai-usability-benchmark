"""Reader-first view of existing proposal data; no changes to scoring rules."""
from html import escape as H
import json

def render(metrics,refs,root,reading_log):
    baseline=json.loads((root/'original-metric-baseline.json').read_text())
    originals={d['id']:d for d in baseline['metrics']}
    new={'M1','M4','M5','M6','M7','M9','M11'}
    changed={'M3':{2,3,4}}
    note={
      'M1':'新增五档：只评价首次搜索前10条中的官方结果排名。',
      'M2':'沿用已确认的正文覆盖五档与独立文档平均。',
      'M3':'主要修改2—4分，4分不再依赖辅助要求，而以局部实质缺口区分。',
      'M4':'新增五档：按任务需要的版本关系评价，而非只看有无版本号。',
      'M5':'新增五档，计数对象明确为已取得的独立第三方内容。',
      'M6':'新增五档，评分聚焦第三方任务支撑；独立性与依据另列。',
      'M7':'主要变更：仅表示检索前自报信心，不再解释为真实知识水平。',
      'M8':'沿用S+F的调用次数与五档区间。',
      'M9':'新增五档：以最终回答中的版本关系为对象。',
      'M10':'沿用五档；补清局部错误与核心链路缺失的判定边界。',
      'M11':'主要变更：建议评价跨来源联合内容支撑，不再合成其他指标。'}
    parts=['<span id="current-diff"></span><h1>逐项审阅：评分标准与依据</h1><p>整套待确认稿 · 2026-09-20 · 尚未写入Skill</p><p><mark>浅黄色＝相较活动Skill新增的分档或主要定义变更</mark>。其余沿用；文献支持的方法与我们自行设定的阈值分别说明。</p>']
    parts.append('<p><mark>原名称、定义与评价目的统一以 <a href="file://'+baseline['source']+'#s4">18_metric_definition.html · 第4节</a>为基线。下方逐项原文保留；旧评分方案暂存折叠区，须核对是否保持原评价对象后再采用。原有分档和公式也需要检查，不因来源早就视为已验证。</mark></p>')
    nav=''.join(f'<a href="#{d["id"].lower()}"><b>{d["id"]}</b> {H(originals[d["id"]]["name"])}</a>' for d in metrics)
    for d in metrics:
        key=d['id'];fresh=key in new
        original=originals[key]
        parts.append(f'<section id="{key.lower()}" class="metric-review"><h2>{key} · {H(original["name"])}</h2><p><b>原定义：</b>{H(original["definition"])}</p><p><b>原评价目的（原文“为什么单独”）：</b>{H(original["purpose"])}</p>')
        parts.append('<p><b>原评分标准（原文留存）：</b>'+H(original['rubric'] or '综合公式映射，见下方原公式。')+'</p><details><summary>原公式与计算说明</summary><p>'+H(original['formula'])+'</p></details>')
        parts.append('<p class="change-note"><mark>本次校正：保留上述评价对象；后续只修订分档、证据和判定边界。旧稿中改变评价对象的定义不采用。</mark></p><details><summary>此前评分修订稿与文献（待按原定义核对，非定稿）</summary>')
        if key=='M4':
            parts.append('<h3>M4 · 此前讨论</h3>'+ (root/'m4-original-review.html').read_text() + '</details></section>')
            continue
        definition=H(d['definition'])
        if fresh:definition='<mark>'+definition+'</mark>'
        parts.append(f'<h3>此前拟议名称：{H(d["name"])}</h3><p>{definition}</p><p class="change-note">{H(note[key])}</p><table class="score-table"><thead><tr><th>分值</th><th>怎么判定</th></tr></thead><tbody>')
        for n,text in enumerate(d['bands'],1):
            content=H(text)
            if fresh or n in changed.get(key,set()):content='<mark>'+content+'</mark>'
            parts.append(f'<tr><th scope="row">{n}分</th><td>{content}</td></tr>')
        parts.append('</tbody></table><h3>评分依据</h3>')
        for r in d['refs']:
            title,url,scope,limit=refs[r]
            parts.append(f'<p><a href="{H(url)}" target="_blank" rel="noopener">{H(title)}</a><br><span class="source-scope">{H(scope)}</span><br><span class="source-limit">适用边界：{H(limit)}</span></p>')
        parts.append(f'<p><b>本研究自行设定的部分：</b>{H(d["own"])}</p>')
        if key=='M2':parts.append('<p><b>多文档合成：</b>各独立官方文档等权平均，保留原始均值并四舍五入为档位；重试不重复计分。存在未知文档时不删除后平均。</p>')
        if key=='M8':parts.append('<p><b>原始值：</b>C=S+F。失败重试按实际调用计一次，未派发不计；C=0或异常中断不自动给高分。</p>')
        parts.append(f'<details><summary>展开：具体例子、证据要求与指标边界</summary><p><b>例子：</b>{H(d["example"])}</p><p><b>证据：</b>{H(d["obs"])}</p><p><b>边界：</b>{H(d["boundary"])}</p><p><b>判定办法：</b>{H(d["action"])}</p><p><b>仍有的局限：</b>{H(d["rigor"])}</p></details></details></section>')
    parts.append('<div id="supporting-materials"><h2>补充材料</h2><p>评分审阅主体在上方；过程材料保留在这里，按需展开。</p>')
    parts.append('<details><summary>文献查阅与采用过程</summary>'+''.join(reading_log)+'</details>')
    for file,label in [('m3-evidence-2026-09-20.html','此前M3讨论与原始例子（历史方案）'),('six-run-review-fragment.html','六轮材料检查与实际返回'),('two-hour-plan-fragment.html','执行计划和耗时估算')]:
        p=root/file
        if p.exists():parts.append('<details><summary>'+label+'</summary>'+p.read_text()+'</details>')
    # historical evidence links retain bibliography anchors, while citations in main body go directly to sources
    parts.append('<details><summary>完整文献索引</summary><div id="references">')
    for k,(title,url,scope,limit) in refs.items():parts.append(f'<div id="ref-{k}"><h3><a href="{H(url)}">{H(title)}</a></h3><p>{H(scope)} {H(limit)}</p></div>')
    parts.append('</div></details></div>')
    nav+='<a href="#supporting-materials">补充材料（折叠）</a>'
    css='''mark{background:#fff0ad;color:inherit;padding:2px 3px;border-radius:3px;box-decoration-break:clone;-webkit-box-decoration-break:clone}.metric-review{max-width:1100px}.score-table{table-layout:fixed;font-size:16px}.score-table th:nth-child(1){width:82px}.score-table th:nth-child(2){width:auto}.score-table td{line-height:1.85}.change-note{font-size:14px;color:#6c5a29}.source-scope{font-size:14px}.source-limit{font-size:13px;color:#667486}details{padding:12px 0}details[open]>summary{margin-bottom:14px}main{max-width:1480px}#supporting-materials table{table-layout:auto;display:block;overflow:auto}#supporting-materials table th:nth-child(n){width:auto}@media(max-width:1000px){.score-table{min-width:0}.score-table td{overflow-wrap:anywhere}}'''
    return parts,nav,css
