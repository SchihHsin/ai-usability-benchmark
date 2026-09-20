"""Build review-only proposal. Does not write Skill, scripts, or installed files."""
from pathlib import Path
import html,json
ROOT=Path(__file__).resolve().parent
H=html.escape
refs={
'IR':('Manning, Raghavan & Schütze (2008). Introduction to Information Retrieval.','https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html','排名检索评价、固定检索深度和相关性判断。已核对公开章节。','不提供本方案的排名五档阈值。'),
'IQ':('Wang & Strong (1996). Beyond Accuracy: What Data Quality Means to Data Consumers. JMIS.','https://doi.org/10.1080/07421222.1996.11518099','信息质量的概念框架；可访问性与情境相关的内容质量分开。题录已核对，当前出版社全文访问受限。','技术版本关系清单及五档是本研究延伸，非原文量表。'),
'RAG':('Es et al. (2024). RAGAs: Automated Evaluation of Retrieval Augmented Generation. EACL Demos.','https://aclanthology.org/2024.eacl-demo.16/','上下文检索、证据忠实性及回答质量分别评价。已核对论文官方摘要。','不把RAGAs自动分数直接当作本研究评分。'),
'FACT':('Min et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP.','https://arxiv.org/abs/2305.14251','拆分原子事实，核对可靠来源的支持情况。已核对摘要。','事实支持不是完整性，也不证明代码执行成功；本研究仅借鉴逐条核验。'),
'SELF':('Kadavath et al. (2022). Language Models (Mostly) Know What They Know. arXiv.','https://arxiv.org/abs/2207.05221','模型自评和实际正确性须区分，自评跨任务校准有局限。已核对摘要；预印本。','不支持将不同模型的自报信心直接当客观知识水平。'),
'COMP':('OECD / European Union / EC-JRC (2008). Handbook on Constructing Composite Indicators: Methodology and User Guide.','https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html','参考综合指标的理论含义、聚合和解释。已核对官方介绍。','不验证本研究旧公式、联合覆盖方案或五档阈值。'),
'BODY':('Kohlschütter, Fankhauser & Nejdl (2010). Boilerplate Detection Using Shallow Text Features. WSDM.','https://doi.org/10.1145/1718487.1718542','区分正文与导航、模板、广告等页面元素；已核对ACM摘要和题录。','本文不照搬该算法；原论文不支持“半数章节”阈值，也不评价语义摘要完整性。'),
'API':('Uddin & Robillard (2015). How API Documentation Fails. IEEE Software.','https://doi.org/10.1109/MS.2014.80','补充API文档问题研究的主题参考。已核对题名、作者、年份；本轮未取得全文。','不能据此声称论文给出了本方案的版本配套检查项或五档；实施前可进一步核对全文。'),
'IIR':('Kelly (2009). Methods for Evaluating Interactive Information Retrieval Systems with Users. Foundations and Trends in Information Retrieval.','https://doi.org/10.1561/1500000012','系统梳理交互式检索评价、数据收集及效度/信度问题。已核对题录与摘要。','人类检索研究迁移到Agent需说明条件，不支持搜索与获取等时或每两次一档。'),
'SCALE':('Boateng et al. (2018). Best Practices for Developing and Validating Scales for Health, Social, and Behavioral Research: A Primer. Frontiers in Public Health.','https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2018.00149/full','明确测量领域、检查内容覆盖，再检查可靠性和效度。已核对全文相关部分。','只借鉴定义和内容检查流程；本框架不是单一心理潜变量量表，不机械套因子分析或内部一致性要求。')}
refs['RUBRIC']=('Reddy & Andrade (2010). A review of rubric use in higher education. Assessment & Evaluation in Higher Education.','https://doi.org/10.1080/02602930902862859','2026-09-20：核对Crossref题录和出版社摘要；参考评分描述的清楚性、适切性与评价者共同解释。','教育评价综述，不提供本研究M3的五档，也不支持用辅助要求定义4分。')
refs['QUESTIONS']=('Sillito, Murphy & De Volder (2006). Questions programmers ask during software evolution tasks. SIGSOFT FSE.','https://doi.org/10.1145/1181775.1181779','2026-09-20：检索并核对Crossref题录；出版社页面遇验证，未取得摘要或全文。','仅留作开发者信息需求候选阅读；未用来制定诊断任务要求或五档。')
D=[]
def add(i,name,change,definition,bands,obs,boundary,rigor,action,ref,own,example):
 D.append(dict(id=i,name=name,change=change,definition=definition,bands=bands,obs=obs,boundary=boundary,rigor=rigor,action=action,refs=ref,own=own,example=example))
add('M1','官方资料首次搜索可发现性','补全五档；收窄评分范围','在本轮首次搜索返回的前10条结果中，首条相关官方来源出现的位置。后续搜索的发现和恢复另存，不拼接多个列表。',
['前10条未出现相关官方结果','首次相关官方结果位于第6—10位','位于第4—5位','位于第2—3位','位于第1位'],
'固定k=10及首轮每次单查询；保留实际查询、全部返回顺序、发布者、相关性理由和URL。后续首次命中轮次/位置另列。工具正常返回不足10条则按实际列表观察，注明实际条数；列表被客户端截断或日志不全记未知。',
'只评首次搜索呈现；不等于整个生态不可发现。正文取得属于M2，累计调用数属于M8。',
'排名可复算；“相关官方结果”仍需判定。不同模型自行措辞会影响结果，不能据此认定是纯SEO效果。',
'相关性条件执行前固定：明确指向本任务目标或预定需求的官方资料。评来源定位时只用搜索当时可见标题/摘要，不要求正文已取得。先按发布主体识别官方；必要时复核相关性并保留理由。跨模型比较报告查询差异。',
['IR','IIR'],'前10条和1/2—3/4—5/6—10分组是本研究约定；保留原始排名。相比混合轮次与排名，范围更清楚，但“发现难度”解释变窄。','首次列表第4位出现官方结果，M1=3；后来搜索找到第1位，不改首次分数。')
add('M2','官方正文取得程度','保留新版五档；补清覆盖核验','对每篇实际尝试读取的独立官方文档，检查本轮累计取得的正文状态，再等权平均。',
['未取得页面内容','仅页面框架，没有正文','可核对的正文单元覆盖率大于0、不足50%','至少50%但未完整；包括各单元有内容却仍存在单元内截断','有依据确认目标正文全部完整取得'],
'执行前固定正文单位及拆分规则；保存同版本同范围参照正文、唯一单元ID、参照位置与本轮返回位置。摘要/预览、截断及HTML/Markdown独立记录。参照核对在执行后进行，不给执行模型补资料，不计其调用数。',
'操作信息够不够属于M3；版本配套属于M4。第三方镜像不能提高官方M2；重试成本属于M8。',
'覆盖算式可复算，但单位长短和匹配判断会影响结果。摘要不能因提到章节主题就当取得该章节正文。',
'同一批固定段落/章节/分页单位；仅标题不计正文。分母来自完整参照而非模型返回。没有可靠参照的部分正文保留未知；5分必须有完整性依据。保留每篇状态、原始覆盖和未知数，不只报均值。',
['BODY','IQ'],'50%边界、结构单位等权及平均五档为研究约定。结构覆盖不是字数比例或知识价值；文献只直接支持正文与框架的区分。','文档A重试后完整取得=5；B始终框架=2；两篇均值3.5，四舍五入为4。若B未知，则任务均值也未知。')
add('M3','官方内容的任务支撑','保留主体；明确2/3分边界','已取得官方内容对预定任务内容要求的充分支撑。',
['取得相关正文，但无可用于任务的信息','有任务相关说明或部分操作，但未充分支持任何核心环节','充分支持部分核心环节，仍缺关键内容','全部核心环节充分，预定辅助说明仍有缺口','全部预定内容要求充分，未见影响这些要求使用的未解决内容矛盾'],
'执行前列需求ID、核心/辅助、逐项达成条件；逐项标充分/部分/无支持/未知，引用官方实际返回。仅“充分”计满足；冲突影响该项时不能标充分。',
'获取障碍属于M2，版本关系属于M4，最终方案属于M10；不重复扣分。',
'“核心环节”若事后定义会改变分数；资料未取得不等于原网页没有写。',
'把“信息充分”改成可观察条件，如“提供定位命令，并解释应看哪个输出字段”。所有相关正文未取得记不可评价；部分已取得时解释范围。检查清单可复用，但按题目选适用项，不强加需求。',
['IQ','RAG','SCALE'],'五档的核心/辅助边界为本研究设计；本草案明确“已有部分操作、但任何核心环节均未充分支持”也属2分，避免原来只有背景/方向的描述漏掉该情况。没有辅助要求时允许没有4分情形。','已取得安装命令但缺题目要求的编译步骤，若编译为核心环节，则最高是部分核心支持档，而非完整支持。')
version_bands=['没有支持任何所需版本关系的信息','只列版本/组件名称或泛泛建议，未明确任何必需配套关系','已明确部分必需关系，仍有必需关系缺失或未解决冲突','全部必需关系明确，但题目要求的辅助版本说明未齐','全部预定版本要求明确，且未见这些关系中的未解决冲突']
add('M4','来源中的版本与配套支撑','补全五档','实际取得的外部资料是否支持任务必需的适用版本和组件关系；按来源分别标注后检查联合支撑。',version_bands,
'执行前列“组件A—组件B—所需兼容关系/适用范围”清单，标核心/辅助。逐关系保存原文、版本范围及一致/冲突/未知。',
'一般操作支撑属于M3/M6，最终回答怎么说明属于M9。M4只检查实际资料，不以最终回答替代。',
'出现版本号不等于有兼容依据；不同环境下的不同说法不一定矛盾。',
'先对齐适用环境再判冲突；不适用关系从清单中事先排除。没有版本需求标N/A；相关资料全未取得记不可评价；对未能核对真伪的关系注明未知。',
['IQ','API'],'版本关系清单及五档均为任务化设计；API文献目前仅为主题参考，未作为具体规则的直接证据。','写明Toolkit 版本，但未说明与框架扩展的配套，不能仅因有版本号给高分。')
add('M5','已读取的独立第三方内容数量','补全五档；固定计数口径','本轮实际取得相关正文的独立非官方内容单元数N。候选URL数、发布者数另外保存。',
['N=0','N=1','N=2','N=3','N≥4'],
'保存候选及读取URL、正文状态、内容同源组和发布主体。相同内容转载/镜像只算一组；官方原文的第三方镜像单列替代渠道，不算独立第三方创作。独立原创内容即使同一网站也可分别计数。',
'只测数量和冗余，不评价好坏；内容支撑属于M6，调用成本属于M8。',
'独立性不能只靠域名或作者名判断；网页多不代表知识多。',
'按具体内容及出处声明去重；有实质独立案例才单列。未知同源关系保留计数上下界；若上下界落在不同档位则待定，不凭感觉选分。未尝试第三方检索/读取标未观察，不给1分。',
['IR','IQ'],'0/1/2/3/4+是便于审阅的饱和计数档，非文献验证阈值；不把5分解释为资料质量高。','取得4个网址，但其中3个转载同一篇文章，另一篇为独立原创，则N=2、M5=3。')
add('M6','第三方内容的任务支撑','补全五档；可信度单独列证据','已取得的独立第三方内容能支持哪些预定内容要求。证据依据和冲突逐项检查，不按平台名气另加权。',
['取得相关正文，但无可用于任务的信息','有任务相关说明或部分操作，但未充分支持任何核心环节','充分支持部分核心环节，仍缺关键内容','全部核心环节充分，预定辅助说明仍缺失','全部预定内容要求充分，未见影响使用的未解决内容矛盾'],
'使用与M3相同的内容需求清单、达成条件和四类状态；分别保存出处、独立案例、可核验依据与矛盾。未经核对的关键事实不标充分支持。',
'数量属于M5，版本配套属于M4，最终回答属于M10。与官方内容联合补足的效果留给M11。',
'原来“可信度、质量、补充作用”混合成整体分容易失去依据；已读取内容未必独立原创。',
'分数聚焦任务支撑，可信度用“有无具体依据、可否核验、是否冲突”的证据项解释。第三方补了官方哪个缺口单列，不因重复官方信息直接扣分。没有第三方正文可评时记不可评价，不把缺来源误当低质量。',
['IQ','RAG','FACT'],'此项从宽泛质量评分收敛为支撑评分；它与M3相同标准、不同渠道。文献支持细粒度核验，不直接提供五档。','论坛独立案例给出错误复现与解决步骤，逐项对应需求；不因来自论坛自动低分，也不因文章很长自动高分。')
add('M7','检索前模型自报信心','重新定位；仅辅助报告','检索前，模型自报“不使用外部检索，能正确且完整回答本题”的概率p。测自报信心，不声称测真实先验知识。',
['0≤p<0.2','0.2≤p<0.4','0.4≤p<0.6','0.6≤p<0.8','0.8≤p≤1'],
'统一提问、检索前时点及无外部材料上下文；保存p和简短依据，不要求内部思维过程。模型未给有效概率时保留未知，不从语气推测。',
'不进入知识支撑综合评价，也不用它替代M3/M6或回答正确性。高分仅表示自报信心高。',
'概率可分档，但不同模型可能过度自信或保守；统一问法不能解决校准差异。',
'跨模型首先报告原始p和局限；若将来要解释为知识水平，需另收无检索答案并独立评价，以比较信心与正确性。此额外实验未在本轮执行，也不是当前运行的新增强制步骤。',
['SELF'],'等宽概率五档是展示约定；建议仅作辅助表，不能用一致的自评推断评分体系有效。','两模型都报0.9只说明信心相同；不能证明都具备相同知识，也不能因最终检索后答对而认定先验自评准确。')
add('M8','搜索与获取调用成本','保留五档；限定成本含义','C=S+F，S为实际搜索派发数，F为实际获取派发数；实际失败、重试各计一次。',
['C≥9','C=7—8','C=5—6','C=3—4','C=1—2'],
'自动保存请求、派发、返回和预算拒绝。分别报告S、F、重试R、未取得正文U；时间/token/费用可见时另列。',
'不是内容质量或时间成本；正文取得属M2，最终方案属M10。预算拒绝未派发不计调用。',
'调用计数可复算，但搜索与获取代价不同；8与9次跨档不意味着成本突然大幅增加。',
'各模型统一工具接口、批量能力、上限和停止条件；强制预算在派发前执行。显示原始计数及五档，解释成本时并列任务支撑。C=0、异常中断等不自动给高分。',
['IIR'],'C=S+F和两次一档保留为协议约定；Kelly提供评价方法背景，不验证这些系数或阈值。','S=3、F=5，C=8、M8=2；其中2次失败不再额外加权。')
add('M9','最终回答的版本与配套明确性','补全五档','按与M4相同的版本需求清单，检查最终回答是否给出明确且有依据的适用范围和配套关系。',version_bands,
'逐关系定位最终回答原句、所用依据和矛盾；不靠关键词计数。有版本需求但答案未交代，可低分；任务无版本需求标N/A。',
'M4评价来源，M9评价回答。M10只评操作链路和实现内容，版本遗漏不重复扣。',
'复制来源的版本号未必适合用户条件；明确但错误的配套不能算满足。',
'对照同一任务环境和来源证据检查；没有依据确认时标未知。沿用核心/辅助关系清单，减少M4与M9评价要求不一致。',
['IQ','RAG','API'],'五档和关系清单为研究设计；同一清单不代表两个指标重复，因为输入对象不同。','官方配套表齐全而回答没交代配套：M4可高、M9可低，不连带修改M4。')
add('M10','最终操作方案的完整性与一致性','保留五档；补充分档例证','核对最终主方案是否满足任务必要操作环节，接口、参数、代码和步骤是否一致。',
['未形成相关操作方案','只有方向或流程概述，无具体操作','有具体操作，但核心链路缺失或接错','核心链路完整，有可定位并局部修正的实质错误或遗漏','必要步骤完整一致，内容核对未发现实质缺口'],
'执行前明确必要环节和达成条件；逐项定位最终回答。记录错误范围、修正需求、适用条件；实机运行及结果单列。',
'版本配套属于M9；来源质量属于M3/M6。不能仅因没有引用或未运行就自动扣操作分。',
'局部修正与核心缺失的边界需要实例；5分只能是已做内容检查范围内的结论。',
'给常见边界建例证：拼错已确定参数名可属局部；缺少整个注册/编译实现属核心。合理环境占位不扣分。无法核对核心正确性标待定；无操作需求N/A。额外方案错误说明是否影响主方案。',
['RAG','FACT','API'],'五档是研究设计。来源事实有支持不保证可运行，不能将FActScore当执行正确性依据。','核心步骤齐全，仅一处参数名可明确修正，可考虑4；根本缺少实现链路则为3或更低。')
add('M11','跨来源联合任务支撑','建议替代旧综合公式；需重点确认','检查本轮取得的官方、第三方原创及可追溯转载材料，联合起来能否支持预定任务内容要求。基于逐需求证据重新合并，不平均M1—M10。',
['取得相关材料，但联合后仍无可用任务信息','联合材料有任务相关说明或部分操作，但未充分支持任何核心环节','联合支持部分核心环节，仍有关键内容缺失','联合支持全部核心环节，预定辅助说明仍有缺口','联合支持全部预定内容要求，未见影响这些要求的未解决矛盾'],
'复用M3/M6内容需求ID；保留每项支持片段的来源、真实返回和出处链。转载可提供任务支撑但不算独立经验；同一内容重复不增加覆盖。',
'只衡量外部材料的联合内容支撑。可发现性M1、正文状态M2、版本关系M4、成本M8及最终回答M9/M10继续并列；M7自评不进入。',
'这是实质性构念调整，不能继续沿用旧“全面综合AI可用性”解释。需求联合支持仍需核对，不能简单相加各渠道分数。',
'同一需求可由多来源共同满足，必须解释如何拼接；版本冲突留M4，内容矛盾影响相应内容要求。全部材料未取得记不可评价。若不接受收窄综合含义，则保留分项矩阵并暂不输出M11，而不是强算旧公式。',
['COMP','RAG','IQ'],'联合需求覆盖及五档是本研究建议，文献只支持谨慎定义聚合含义；不称为成熟综合量表。该项批准前不写入Skill。','官方支持需求A，第三方支持需求B；两者单独均不完整，联合可支持全部核心要求。无需强求各模型最后分数一样。')

from refine_original_metrics import amend
D=amend(D)

def citations(keys):return '<br>'.join(f'<a href="#ref-{k}">{H(refs[k][0])}</a>' for k in keys)
def bands(d):return '<ol>'+''.join(f'<li><b>{n}分：</b>{H(v)}</li>' for n,v in enumerate(d['bands'],1))+'</ol>'
css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:25px}body{margin:0;background:#f4f6f9;color:#243248;font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}aside{position:fixed;width:245px;top:0;bottom:0;overflow:auto;background:#fff;border-right:1px solid #e3e7ef;padding:26px 15px}aside strong{display:block;padding:0 12px 16px;font-size:18px}a{color:#235aa1;text-decoration:none;overflow-wrap:anywhere}a:hover{text-decoration:underline}aside a{display:block;border-radius:8px;padding:8px 12px;font-size:12px;color:#48596d}aside a.active,aside a:hover{background:#eaf0fa;color:#21589d;text-decoration:none}main{margin-left:245px;padding:40px 30px 80px;max-width:1800px}h1{font-size:31px;line-height:1.4}h2{font-size:23px;margin-top:30px;color:#173e69}h3{font-size:17px}.notice{background:#fff3d9;border:1px solid #ecd5a4;border-radius:12px;padding:18px 22px}.tag{display:inline-block;border-radius:6px;background:#eaf0fa;padding:3px 9px;font-size:12px;color:#254e84}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;table-layout:fixed;background:#fff;font-size:13px;margin:18px 0}th,td{border:1px solid #dfe6ef;text-align:left;vertical-align:top;padding:14px}th{background:#eaf0f8}th:nth-child(1){width:17%}th:nth-child(2){width:31%}th:nth-child(3){width:29%}th:nth-child(4){width:23%}ol{list-style:none;padding:0;margin:0}li{margin-bottom:7px}section{background:#fff;border:1px solid #e0e6ef;border-radius:14px;padding:20px 26px;margin:25px 0}section h2{margin-top:4px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:25px}.refs p{font-size:13px}button{padding:8px 12px;background:white;border:1px solid #d8e1ee;border-radius:6px;cursor:pointer}.formula{padding:16px;background:#f3f6fc;font-size:18px}summary{cursor:pointer;color:#235aa1}p{margin:12px 0}@media(max-width:1000px){main{padding:25px 16px}table{min-width:970px}.cols{grid-template-columns:1fr}}@media(max-width:750px){aside{position:static;width:auto;max-height:240px}main{margin:0}h1{font-size:25px}}@media print{aside,button{display:none}main{margin:0;padding:0}body{font-size:11px;background:white}table{font-size:9px;min-width:0}h2,h3{break-after:avoid}.tablewrap{overflow:visible}}'''
nav='<a href="#overview">总览与五档</a><a href="#method">共同评分协议</a>'+''.join(f'<a href="#{d["id"].lower()}"><b>{d["id"]}</b> {H(d["name"])}</a>' for d in D)+'<a href="#validation">怎样加强严谨性</a><a href="#references">文献与核对范围</a>'
parts=['<h1>11项指标：评分规则与严谨性修订方案</h1>','<p>整套审阅版 · 2026-09-20 · proposal-2</p>', '<div class="notice"><b>本轮仅供确认，尚未写入Skill。</b><br>当前安装版仍是此前的v2-coverage-2026-09-15。本页提出整套修订：补齐M1/M4/M5/M6/M9五档，明确M7仅为自报信心，并建议将M11改为跨来源联合任务支撑。没有重跑实验、改旧分数或更新论文。</div>', '<p>严谨性按“定义与边界、分档依据、证据可追溯、判断可重复、结论适用范围”逐项说明，不再用笼统的高中低评级。下列全部规则均作为本次整体待确认方案；标注“保留”的项目沿用已有方案。</p>', '<h2 id="overview">总览：每个分数怎么定、依据是什么</h2><p>五档用于统一展示，不意味着指标之间可直接相加，或相邻档位差距相等。文献支持范围和研究自行设定的阈值分别列出。</p><div class="tablewrap"><table><thead><tr><th>指标与定义</th><th>拟定评分标准</th><th>严谨性：已有依据、问题与改进</th><th>参考文献与支持边界</th></tr></thead><tbody>']
for d in D:
 parts.append(f'<tr><td><a href="#{d["id"].lower()}"><b>{d["id"]} · {H(d["name"])}</b></a><p>{H(d["definition"])}</p><span class="tag">{H(d["change"])}</span></td><td>{bands(d)}</td><td><b>尚存问题：</b>{H(d["rigor"])}<p><b>改进办法：</b>{H(d["action"])}</p></td><td>{citations(d["refs"])}<p><b>边界与研究约定：</b>{H(d["own"])}</p></td></tr>')
parts+=['</tbody></table></div>', '<section id="method"><h2>共同评分协议</h2><p><b>任务要求先固定。</b> 两生态按共同开发意图、起始条件和产出要求配对，保留两问句及差异。每项要求有ID、适用范围、所属指标和“达到什么才算满足”的条件；不因某个模型的答案增删要求。问题相似不自动证明难度完全相同。</p><p><b>观测、证据、评分分开。</b> 观测保存工具实际返回与最终答案；评价引用原文并解释满足/部分/不满足/未知；程序处理计数与聚合。对内容评分依次判断：没有可用信息→1；只有方向或未成形的片段→2；已有可用关键片段但需补建或重选路径→3；所有必需内容路径已形成、仅局部实质缺口→4；全部预定要求充分且无实质缺口→5。M4/M9使用版本关系清单，M10使用自身链路标准。</p><p><b>不知道不填低分。</b> 区分未观察、不可评价、不适用和未知。只要未知会改变所属档位，就保留待定；不删除未知项来抬高均值。4分不依赖辅助要求存在；必须指出局部缺口及为何无需补建关键路径。</p><p><b>保留遇阻与恢复。</b> 同样遇到页面框架，即使某模型后来找到替代材料，也同时报告共同障碍和不同恢复路径。没有访问相关资料的模型标未观察，不写成没有问题。</p><p><b>五档与原始数据同时保存。</b> M1保留实际排名、M2保留文档状态和覆盖、M5保留原始数量、M7保留原始概率、M8保留实际调用。内容指标保留逐需求矩阵。全部仍放在process.jsonl与evaluation.json两个交付文件内。</p><p><b>跨模型比较的对象。</b> 先比较同模型内两生态，再检查多个模型发现的共同问题、反例及恢复路径。既不以分数完全相同为目标，也不以结论一致单独证明评分体系有效。</p></section>']
for d in D:
 parts += [f'<section id="{d["id"].lower()}"><h2>{d["id"]} · {H(d["name"])}</h2><span class="tag">待整体确认 · {H(d["change"])}</span><p>{H(d["definition"])}</p><div class="cols"><div><h3>1—5分标准</h3>{bands(d)}</div><div><h3>原始材料与判断依据</h3><p>{H(d["obs"])}</p><h3>与其他指标的分工</h3><p>{H(d["boundary"])}</p></div></div><h3>严谨性问题与改进</h3><p>{H(d["rigor"])}</p><p>{H(d["action"])}</p><h3>具体例子</h3><p>{H(d["example"])}</p><h3>文献及适用边界</h3><p>{citations(d["refs"])}</p><p>{H(d["own"])}</p>']
 if d['id']=='M2':parts+=['<div class="formula"><math display="block"><msub><mover><mi>x</mi><mo>¯</mo></mover><mi>M2</mi></msub><mo>=</mo><mfrac><mn>1</mn><mi>n</mi></mfrac><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msub><mi>s</mi><mi>i</mi></msub><mo>，</mo><mi>M2</mi><mo>=</mo><mo>⌊</mo><msub><mover><mi>x</mi><mo>¯</mo></mover><mi>M2</mi></msub><mo>+</mo><mn>0.5</mn><mo>⌋</mo></math></div><p>n为独立官方文档数；重试/分页合并。任一文档分值未知则不计算任务均值，同时报告可评分文档数及全部文档数。结构覆盖分子是已取得正文内容的单元数，不是仅出现标题的单元数。</p>']
 parts+=['</section>']
parts+=['<section id="validation"><h2>怎样进一步加强严谨性</h2><p><b>第一步：先检查内容效度。</b> 用代表性任务核对每项要求是否必要、是否遗漏、是否跨指标重复。借鉴Boateng等的领域定义与内容审查方法，避免把自动计数指标误当单一心理量表。</p><p><b>第二步：检查评分可重复性。</b> 从已有证据选取包含边界和未知的材料，隐去执行模型身份，由两位评价者独立评同一材料。报告样本量、逐项精确一致率、分档混淆和未知比例；需要时使用有序评分的加权一致性统计。未执行前不宣称已验证。</p><p><b>第三步：按分歧修规则。</b> 区分分歧来自任务要求、来源归属、原文映射还是分档。补写具体边界例子，在另一批材料检查，不能只把原来分歧讨论到一致便当独立验证。</p><p><b>第四步：保留原始结果解释。</b> M1、M5、M8的区间仍是协议选择，不把跨档当自然突变；M2结构覆盖不当知识充分性。正式分析以任务证据、原始数值和逐需求支持为基础，五档辅助比较。</p><p><b>第五步：控制结论范围。</b> M7仅解释自报信心；M10未经运行不声称运行成功；M11若批准，仅解释外部材料联合内容支撑。不同模型共同发现一个障碍支持该观察的稳定性，不自动证明网站技术原因或整个评分框架有效。</p><p>这些是后续实施建议，不是已经完成的实验，也不把新试跑或额外人评擅自设为本次编辑的前置条件。</p></section>', '<section id="references" class="refs"><h2>参考文献与实际核对范围</h2><p>直接测量方法、概念背景和主题参考的用途不同。未取得全文的文献不被用来声称某条具体分档已有实证支持。</p>']
for k,(title,url,support,limit) in refs.items():parts+=[f'<div id="ref-{k}"><h3>[{k}] <a href="{H(url)}" target="_blank" rel="noopener">{H(title)}</a></h3><p><b>已核对及可借鉴：</b>{H(support)}<br><b>不能据此声称：</b>{H(limit)}</p></div>']
parts+=['</section><section id="decisions"><h2>本轮重点确认的变化</h2><p>① M1只按首次搜索排名评分；② M5固定为已读取的独立第三方内容数量；③ M6聚焦任务支撑，可信度依据另列；④ M7明确为辅助自报信心；⑤ M11建议替代旧公式，改为跨来源联合任务支撑。这些涉及定义或范围变化，确认后需统一更新协议、模板、校验、Skill及后续论文说明，旧实验保留原版本。</p></section>']
js='''const links=[...document.querySelectorAll('aside a')];const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting)links.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id));},{rootMargin:'0px 0px -65% 0px'});document.querySelectorAll('section[id],h2[id]').forEach(e=>observer.observe(e));'''
extra=ROOT/'m3-evidence-2026-09-20.html'
if extra.exists():
    parts.append('<details><summary>展开此前M3讨论与原始例子（历史方案，当前以proposal-2为准）</summary>'+extra.read_text()+'</details>')
    nav='<a href="#m3-evidence">M3：文献与实际证据（新增）</a>'+nav
log=['<section id="reading-log"><h2>研究过程中的文献留存</h2><p>保留已采用、部分采用和仅检索到的文献。核对范围与用途分别说明；题录、摘要和全文不混称“读过全文”。后续调整规则继续补充此处，不因方案被撤回而删除相关文献。</p><p><b>2026-09-20的方法修订：</b>M3用“核心齐全、辅助缺失”定义4分，导致无辅助要求的任务缺档。此定义已被指出需要修订；不能把缺档合理化为任务问题。原方案保留供追溯，新的统一五档见proposal-2。没有任何下列文献被核实为支持该4分定义。proposal-2已取消这一依赖，改为局部实质缺口，仍是待确认的研究量规。</p><div class="tablewrap"><table><thead><tr><th>文献与查阅时间</th><th>实际核对范围</th><th>用于哪个判断</th><th>采用状态与限制</th></tr></thead><tbody>']
uses={'IR':'M1排名与固定检索深度；M5检索统计。','IQ':'获取、内容充分性与情境适用性分开。','RAG':'M3/M6来源内容与M10最终回答分开。','FACT':'逐条核验事实支持，不等同操作完整。','SELF':'M7自报信心不等于真实知识。','COMP':'M11聚合含义和补偿关系须明确。','BODY':'M2正文与页面框架区分。','API':'开发者文档问题的候选参考。','IIR':'M1/M8交互检索评价背景。','SCALE':'先定义评价对象，再检查内容覆盖与评分可靠性。','RUBRIC':'M3分档措辞须清楚适切，需检查共同解释。','QUESTIONS':'拟查开发者任务中的信息需求；尚未用于定义评分。'}
for key,(title,url,scope,limit) in refs.items():
    date='2026-09-20' if key in {'RUBRIC','QUESTIONS'} else '2026-09-15'
    status='候选，未作为分档依据' if key in {'API','QUESTIONS'} else '借鉴概念或方法，未直接套用分档'
    log.append(f'<tr><td><a href="{H(url)}">{H(title)}</a><p>{date}</p></td><td>{H(scope)}</td><td>{H(uses[key])}</td><td><b>{status}</b><p>{H(limit)}</p></td></tr>')
log.append('</tbody></table></div><h3>留存的摘要原句示例</h3><blockquote>clarity and appropriateness of language is a central concern.</blockquote><p>出自Reddy &amp; Andrade摘要，针对量规效度研究的概括。它支持检查描述语是否清楚、适合评价对象，不能推出某个具体档位应如何命名。此处留存短摘录、原文链接和用途；未保存或未取得的全文不声称已归档。</p></section>')
parts.append(''.join(log))
nav='<a href="#reading-log">文献留存与采用过程</a>'+nav
plan=ROOT/'two-hour-plan-fragment.html'
if plan.exists():
    parts.insert(4,plan.read_text())
    nav='<a href="#two-hour-plan">两小时交付与今日重跑</a>'+nav
css += '#two-hour-plan table{table-layout:auto}#two-hour-plan th:nth-child(n){width:auto}#two-hour-plan th:first-child{min-width:95px}#two-hour-plan table{display:block;overflow:auto}'
audit=ROOT/'six-run-review-fragment.html'
if audit.exists():
    parts.insert(5,audit.read_text())
    nav='<a href="#six-run-review">六轮材料核对与耗时</a>'+nav
from check_proposal_boundaries import cases,band
checks='<section id="current-diff"><h2>本次集中确认：相比活动Skill改了什么</h2><p>活动Skill目前只有M2/M3/M8/M10分档已确认，其他指标未正式评分。本页为完整待确认方案，历史文献与旧讨论保留在可展开区域。</p><ul><li><b>M1：</b>新增首次搜索前10条的排名五档；首次工具错误记未知，不将后续列表拼接。</li><li><b>M2：</b>保留已确认的覆盖五档和文档等权，补清参照缺失不得猜分。</li><li><b>M3/M6：</b>统一按任务支撑路径与缺口影响区分五档，取消辅助要求作为4分前提；M6来源独立性另存。</li><li><b>M4/M9：</b>同一版本关系需求，分别评价来源和回答；4分为既定配套选择的局部范围缺口。</li><li><b>M5：</b>新增实际取得独立第三方内容的0/1/2/3/4+五档；镜像不重复算独立原创。</li><li><b>M7：</b>改为检索前自报概率及五档，仅辅助说明，不作为真实知识或综合分。</li><li><b>M8：</b>保留S+F与现有区间，实际次数与等级同时呈现。</li><li><b>M10：</b>保留主要分档，要求说明3/4分的结构性或局部修正依据。</li><li><b>M11：</b>建议改为外部材料的联合任务支撑，不再合成M1—M10；这是范围变化，必须确认后才实施。</li></ul><h3>五档判定路径检查</h3><p>以下是说明规则的构造例子，不是真实模型运行得分。代码仅检查从已判定的条件到档位的映射，条件是否成立仍需原文核对。</p><ul>'
for name,kw,want in cases:
    assert band(**kw)==want
    checks+='<li>'+H(name)+' → '+('待定/不可评价' if want is None else str(want)+'分')+'</li>'
checks+='</ul><p>最后的局部/结构性判断仍是评价者的证据判断；本次未声称已完成独立评价者一致性或效度验证。正式执行前仍需冻结全部任务需求。今日重跑取决于这版确认及执行器更新。</p></section>'
parts.insert(6,checks)
nav='<a href="#current-diff">集中修改点与五档检查</a>'+nav
from render_metric_review import render
parts,nav,reader_css=render(D,refs,ROOT,log)
css+=reader_css
page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>11项指标严谨性修订 · 待确认方案</title><style>'+css+'</style></head><body><aside><strong>指标严谨性修订</strong>'+nav+'<button onclick="print()">打印 / 保存PDF</button></aside><main>'+''.join(parts)+'</main><script>'+js+'</script></body></html>'
(ROOT/'scoring-rules-and-literature-2026-09-15.html').write_text(page)
(ROOT/'scoring-proposal-2026-09-15.json').write_text(json.dumps({'status':'review_only_original_constructs_refined_rules','baseline':'original-metric-baseline.json','metrics':D,'references':refs},ensure_ascii=False,indent=2))
print('Built review-only HTML and proposal data; Skill unchanged.')
