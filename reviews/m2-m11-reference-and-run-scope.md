# M2/M11参考与六次试跑版本说明

## M2
Kohlschütter, C., Fankhauser, P., & Nejdl, W. (2010). Boilerplate Detection using Shallow Text Features. DOI: https://doi.org/10.1145/1718487.1718542
已查阅范围：此前核对题录及摘要，未完整阅读全文。用途：区分页面模板与正文。不能支持：摘要3分、截断正文4分等具体排序或阈值。这五档为研究操作化约定，尚未用新规则完成实测评分。

## M11
OECD/European Union/Joint Research Centre (2008). Handbook on Constructing Composite Indicators: Methodology and User Guide. DOI: https://doi.org/10.1787/9789264043466-en
已查阅范围：此前官方简介；本轮官网访问403，未新增全文核验。用途：综合指标的归一化、权重、聚合和敏感性审查框架。不能支持：本研究具体三渠道划分、等权必然最优或历史0.7/0.3、0.9/0.1权重有效。等权平均会改变原噪声OR“任一渠道兜底”的聚合含义，需明确报告。

## 实验用的版本
六次真实运行位于opknow/experiments/multimodel/m11-pilot-20260920。执行器复制了当时安装的Skill作为日志和预算脚本快照；该Skill当时的默认评分仍为v2-coverage-2026-09-15，并非刚修订的M2/M11。

模型实际收到任务原文、检索前完整回答要求、最多4次搜索/8次获取、官方与第三方核查、最终答案与停止原因等精简指令。执行器没有将完整Skill文本注入模型。不得称为完整新版Skill端到端验证。

采集开始时的frozen-review-rubric.json仅供控制端留档，未交模型评分；此后M11从分档改为百分制、M2改为返回形态、M11改为等权渠道聚合，均未追改旧快照。

因此：六次采集完成，最新规则评分尚未完成，M11仍为空。原始返回和最终答案可以用于后评，但若缺少新规则要求的证据则保留待定。不得把材料可复用等同于新版规则已验证。当前不自动追加六次运行。


## 2026-09-21 系数检查补充
本轮JRC官方书目 https://publications.jrc.ec.europa.eu/repository/handle/JRC47008 返回200，核对书名、作者、年份、摘要；OECD PDF返回403，另一候选PDF路径404，未宣称本轮阅读全文或取得新页码引文。
已恢复原噪声OR公式与Mi/5归一化，固定版本权重0.30、成本权重0.10；旧均值方案仅作为历史。对26个旧任务、两生态共52组历史评分进行1,071组权重检查，非新版实测、非最优拟合。总体方向一致但5个任务可反转；完整可复算材料见experiments/m11-coefficients-20260921。
