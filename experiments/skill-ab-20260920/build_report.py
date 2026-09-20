from pathlib import Path
import json,hashlib
from html import escape as H
R=Path(__file__).parent;data=json.loads((R/'comparison.json').read_text());manifest=json.loads((R/'snapshot-hashes.json').read_text())
for variant,files in manifest.items():
 for name,digest in files.items():assert hashlib.sha256((R/variant/name).read_bytes()).hexdigest()==digest,(variant,name)
body='<section id="skill-ab"><h2>完整新旧Skill对照验证</h2><p>D自定义算子任务，DeepSeek V4.1 Flash，旧/新各两生态，共4次全新会话。完整Skill及活动参考文件实际注入，原安装版未替换。新副本的规则包含M2返回形态、M7检索前完整回答、M10操作可执行性、M11百分制新公式。副本哈希已复核。</p><table><tr><th>运行</th><th>搜索/获取</th><th>检索前完整答案</th><th>M8</th></tr>'
for x in data:
 c=sum(x['counts'].values());score=max(1,5-(c-1)//2)
 body+=f'<tr><td>{H(x["run"])}</td><td>{x["counts"]["search"]}/{x["counts"]["fetch"]}</td><td>{"有" if x["prior_full"] else "仅旧版自评与准备说明"}</td><td>{score}</td></tr>'
body+='''</table><h3>已经验证到的差异</h3><ul><li>两次新版都在工具前给出完整prior_answer；旧版只有自评/准备说明，不能转换成新版M7分数。</li><li>同一份明确框架返回，新旧规则都判M2=2；本轮共有7个可明确判定的框架返回。旧版CUDA的一份显式Extract返回，新版M2可判3，旧版因缺少覆盖分母保持未知。只是文档级片段对照，不是整个任务M2分数。</li><li>旧版CUDA最终答案手写了process/evaluation以及自定义证据编号，并声称未接入记录器，与客户端事实不一致；不采信这套自报日志。两次新版没有手写另一套完整日志。</li><li>新版CANN明确保存“官方返回框架→替代资料→仍缺实现/注册说明”的结果，仍存在从框架推断SPA原因的越界表述。新版CUDA还声称沙箱无GPU，客户端未提供硬件检查依据；只能说协议未允许本地执行。</li></ul><h3>尚未通过的部分</h3><p>直接正文的完整性并非总可核对，新版M2仍有未知；先验回答正确性、来源可信度及最终代码还没有完成独立内容核验。因此所有M11保持null，不能补分声称新版综合分已验证。M8已按实际调用计算并写入各运行evaluation修订。单任务单次对照不能证明新版更准或更省成本。</p><h3>明确的修订位置</h3><ol><li>后处理只接受客户端原始事件，拒绝将模型自报编号当原始证据。</li><li>正文完整性必须有对应依据；未知保留，不能以模型说完整代替核对。</li><li>不根据框架返回推断SPA，不凭未执行推断无GPU；原因与可见现象分开。</li></ol><p>这次仅建立实验副本并验证，未替换正式Skill。完整原始记录留本机runs目录；公开文件为副本、冻结哈希、执行器与脱离原始答案的诊断摘要。</p></section>'''
(R/'report.html').write_text(body)
(Path('/Users/hsin/Documents/Coding/ai-usability-benchmark/reviews')/'skill-ab-report.html').write_text(body)
print('4次对照报告生成，冻结副本哈希一致。')
