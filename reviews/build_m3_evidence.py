from pathlib import Path
import json,html
R=Path(__file__).resolve().parent
P=Path('/Users/hsin/Documents/Coding/opknow/experiments/multimodel/e-validation-body-state-20260914')
H=html.escape
task=json.loads((P/'task.json').read_text())
def pick(pattern,event):
 f=next(P.glob(pattern+'/process.jsonl'));rows=[json.loads(l) for l in f.read_text().splitlines()];r=next(r for r in rows if r['id']==event);return f,r
f,a=pick('runs/E-glm-cann*','call_42cc613845894a688d2ab9f0.result')
g,b=pick('runs/E-kimi-cann*','WebFetch_2_a4c60faa.result')
# Full response is embedded for inspection; no new scoring is written to experiment data.
def block(path,r,label):
 text=r['response']['content']
 text=text.replace(chr(92)+chr(110),chr(10))
 return f'<h3>{H(label)}</h3><p>文件：<a href="{path.as_uri()}">{H(path.parent.name)}/process.jsonl</a><br>事件：<code>{H(r["id"])}</code><br>保存的返回哈希：<code>{H(r["response"].get("sha256","未提供"))}</code></p><details><summary>展开此次实际返回全文</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:520px;overflow:auto;background:#f4f6fa;padding:16px">{H(text)}</pre></details>'
s='<section id="m3-evidence"><h2>M3专项：文献、原题与实际证据</h2><span class="tag">2026-09-20补充 · 仅审阅，未修改Skill或实验评分</span>'
s+='<p><b>建议：</b>保留“按任务要求逐项检查”的方向；把每项达成条件写具体，避免凭整篇印象打分。文献支持清楚的判据和内容效度检查，不直接提供这道错误诊断题的五档答案。</p>'
s+='<h3>文献具体解决什么</h3><p><a href="https://doi.org/10.1080/02602930902862859">Reddy & Andrade（2010），A review of rubric use in higher education</a>：已核对出版社摘要，其中指出评分量规的效度研究尤其关注措辞的清楚与适切性，评价者可靠性研究显示量规可促进共同解释。我们据此把“充分”展开为可核对条件；该综述来自教育评价，不能直接验证开发者生态评分。</p><p><a href="#ref-SCALE">Boateng等（2018）</a>：借鉴先界定领域、再检查内容覆盖的顺序；<a href="#ref-RAG">RAGAs</a>：借鉴来源上下文与最终回答分开评价。二者不支持临时添加题目之外的辅助要求。</p>'
s+='<h3>原题与已有要求：不是现在重新编题</h3><blockquote>'+H(task['questions']['cann'])+'</blockquote><p>以下来自既有task.json；本次不修改。CUDA对应问题聚焦device-side assert，CANN问题更宽，不能声称难度严格相等。</p><ul>'
for q in task['requirements']:s+='<li><b>'+H(q['id'])+'（核心）：</b>'+H(q['description'])+'</li>'
s+='</ul><h3>把“满足”写成可检查条件（本次建议，尚未用于正式改分）</h3><ul><li><b>R1：</b>能说明错误码本身不足以确定根因，明确下一步应收集或查看的现场信息及作用。</li><li><b>R2：</b>给出至少一条适用于题目范围的具体定位路径，包含操作步骤及输出判读；不强制必须是命令，也不以某个特定工具名为唯一正确路线。</li><li><b>R3：</b>把观测结果与下一步排查或原因验证联系起来，不能仅列“检查环境”等无条件清单。</li></ul><p>这些条件是对原要求的展开，不是文献原句。必须在新一轮执行前冻结；当前只能用于规则演示，不冒充旧实验当时已有的更细判据。</p>'
s+=block(f,a,'例1：仅返回页面框架')
s+='<p><b>如何判断：</b>此返回未取得诊断正文，是M2的获取现象。不能仅据此给该网页M3=1，也不能认定整个GLM任务不可评价，因为该任务还读取了其他资料。任务M3须检查全部已取得官方内容。</p>'
s+=block(g,b,'例2：取得日志字段和排查说明')
quote='**fault kernel_name/fault kernel info ext：**表示报错kernel名字，可用于查看报错算子。'
assert quote in b['response']['content']
s+='<blockquote>'+H(quote)+'</blockquote><p>返回还说明异步执行可能包含多个算子错误，需从首报错算子开始排查。这比泛泛建议提供了具体可用信息，可作为R2的部分支持。单凭这段还不能确认完整定位路径、R1与R3都已满足，更不能直接给整轮M3一个分数。</p>'
s+='<div class="notice"><b>2026-09-20更新：</b>下方按辅助要求划分4分的办法已不作为最终建议。它在无辅助要求的任务中产生缺档，需要重新设计统一五档；此处保留原分析供追溯，未写入Skill。</div><h3>此前五档分析（待修订）</h3><p>1分＝有相关正文却无可用信息；2分＝有可用信息，但尚无任何核心要求得到充分支持；3分＝部分核心要求充分；5分＝三项核心要求都充分且没有影响使用的未解决内容矛盾。该任务没有辅助要求，因此4分没有对应情形，保持五档通用规则但不强行用满。</p><p><b>这次尚不发布任务总分：</b>这里只核对两个返回以说明边界，没有完成两轮全部官方材料的逐需求核对。后续完成整轮证据清单后才评分；未知与未满足分别保存。</p></section>'
(R/'m3-evidence-2026-09-20.html').write_text(s)
