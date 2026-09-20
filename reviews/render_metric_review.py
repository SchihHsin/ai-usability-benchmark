"""Reader-first view of existing proposal data; no changes to scoring rules."""
from html import escape as H
import json

def render(metrics,refs,root,reading_log):
    baseline=json.loads((root/'original-metric-baseline.json').read_text())
    originals={d['id']:d for d in baseline['metrics']}
    parts=['<span id="current-diff"></span><h1>11项指标：评分规则修订稿</h1><p>保留原名称、定义和评价目的 · 仅供审阅，尚未写入Skill</p><p>先固定评价对象，再明确五档与证据边界，最后复用已有记录检查分歧。确认后统一写入Skill并开展正式运行。<mark>黄色为本轮修订；M8保留此前方案；M2按本轮实测修订。M10名称为“操作可执行性”；M11采用0—100连续分，不转为1—5档；历史阈值仅供对照。</mark></p>']
    parts.append('<p>概念基线：<a href="file://'+baseline['source']+'#s4">18_metric_definition.html 第4节</a>。原定义逐字保留；旧分档和公式仅用于对照，不替换已确认的修订。</p>')
    nav=''.join(f'<a href="#{d["id"].lower()}">{d["id"]} · {H(d["name"])}</a>' for d in metrics)
    for d in metrics:
        key=d['id'];o=originals[key]
        parts.append(f'<section id="{key.lower()}" class="metric-review"><h2>{key} · {H(d["name"])}</h2><p><b>原名称：</b>{H(o["name"])}</p><p><b>原定义：</b>{H(o["definition"])}</p><p><b>原评价目的：</b>{H(o["purpose"])}</p><h3>拟采用评分规则</h3><table class="score-table"><thead><tr><th>分值</th><th>怎么判定</th></tr></thead><tbody>')
        if key=='M11':parts.append('<tr><th>0–100</th><td><mark>M11＝100 × 三渠道噪声OR合成值K × 版本因子 × 成本因子；详见下方明确公式。展示一位小数，不划分五档。</mark></td></tr>')
        for n,t in enumerate(d['bands'],1):
            t=H(t)
            if key not in {'M8'}:t='<mark>'+t+'</mark>'
            parts.append(f'<tr><th>{n}分</th><td>{t}</td></tr>')
        parts.append('</tbody></table><p><b>判定、证据与边界：</b>'+H(d['action'])+'</p><h3>参考文献及支持范围</h3>')
        for r in d['refs']:
            title,url,scope,limit=refs[r]
            parts.append(f'<p><a href="{H(url)}">{H(title)}</a><br>{H(scope)}<br><b>不能据此推断：</b>{H(limit)}</p>')
        if key=='M11':parts.append((root/'m11-fitting-fragment.html').read_text())
        if key=='M11':parts.append((root/'m11-coefficients-fragment.html').read_text())
        if key=='M1':parts.append((root/'m1-session-literature.html').read_text()+(root/'m1-replay.html').read_text())
        parts.append('<p><b>自定部分：</b>'+H(d['own'])+'</p><details><summary>对照：最初分档与公式</summary><p>'+H(o['rubric'])+'</p><p>'+H(o['formula'])+'</p></details></section>')
    parts.append('<details><summary>Experimental Skill v2: fixes and evaluation responsibilities</summary><pre style="white-space:pre-wrap">'+H((root.parent/'experiments/skill-ab-20260920/new-skill-v2/references/post-evaluation.md').read_text())+'</pre></details>')
    parts.append((root/'skill-ab-report.html').read_text())
    parts.append((root/'m11-pilot-report.html').read_text())
    parts.append('<details><summary>M2/M11参考依据与试跑版本说明</summary><pre style="white-space:pre-wrap">'+H((root/'m2-m11-reference-and-run-scope.md').read_text())+'</pre></details>')
    parts.append((root/'conversation-literature-fragment.html').read_text())
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
