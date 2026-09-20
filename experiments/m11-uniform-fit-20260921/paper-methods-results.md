# M11 uniform fit 结果（2026-09-21）
状态：**留出验证完成**

## 公式与选择
M = 100 × K × (1 − a × (1 − M4/5)) × (1 − b × (1 − M8/5)); K = 1 − (1 − (M1/5)(M2/5)(M3/5))(1 − (M5/5)(M6/5))(1 − M7/5).

历史 baseline：`a=0.30,b=0.10`，仅作预先指定对照；本轮暂不支持用新拟合系数替换 baseline，也不表示 baseline 已被证明最优。候选五族和 leave-one-development-task-group-out 选择按 `protocol.json` 执行。留出前冻结族与系数，结果不宣称通用最优。

冻结选择：`original`，a=0.3，b=0.1。
开发输入 hash：`7fb7adcfe3ee35b42f98d4185434509b9fc0862005ba2b0316084a9547df2020`。

## 样本与排除
开发纳入 24/32 个候选样本；自动统计预算分布：纳入 {'restricted': 8, 'standard': 16}，排除 {'restricted': 8}。协议预期运行数：48；开发任务：['A', 'C', 'D', 'F', 'I', 'J', 'K', 'P']；留出任务：['B', 'E', 'L', 'Q']。
区间结构：outcome 点值 2/24，M2 点值 1/24，M7 为 [1,5] 7/24。复核后的 32 个样本共 192 条需求：supported=62、unverified=111、absent=19；其中 72 条由 supported 因引文审计转为 unverified。

| case | group | split | budget |
| --- | --- | --- | --- |
| case-7020c4600b57 | A | development | restricted |
| case-d357ca657c2f | A | development | standard |
| case-1bc9b4af97fb | A | development | restricted |
| case-3596d093fa41 | A | development | standard |
| case-0ff4c840c89b | C | development | standard |
| case-c7a4eeeb8cef | C | development | standard |
| case-4317367445af | D | development | standard |
| case-7bc2eae074d7 | D | development | restricted |
| case-f9a13529118e | D | development | standard |
| case-3e89964f75db | F | development | restricted |
| case-9726a2c06b3f | F | development | standard |
| case-d628482f695e | F | development | standard |
| case-e17d72f9ec8a | I | development | restricted |
| case-9bb24619e25f | I | development | standard |
| case-e83c2d3aa486 | I | development | standard |
| case-35f37badcfd5 | J | development | standard |
| case-90224adebad4 | J | development | standard |
| case-0f36b0694c72 | K | development | restricted |
| case-447a4d1139d6 | K | development | standard |
| case-a1d70a4acefa | K | development | restricted |
| case-80bd48bbc430 | K | development | standard |
| case-f86b678c1d62 | P | development | standard |
| case-9ee139c52911 | P | development | restricted |
| case-43254654de53 | P | development | standard |

明确排除（不进入拟合）：
| case | reason |
| --- | --- |
| case-b507aef8ee04 | M3: blocked |
| case-7b489763aa06 | M3: blocked; M4: blocked; M6: not_applicable; M8: invalid/missing interval |
| case-4b2cf0898b2a | M3: blocked |
| case-eff823477053 | M2: blocked; M3: blocked; M4: blocked; M8: invalid/missing interval |
| case-403282c82ab0 | M3: blocked |
| case-20c1dc7707f4 | M2: not_applicable; M3: blocked; M4: blocked |
| case-8b122bc23756 | M3: blocked |
| case-32950a89e193 | M6: not_applicable |

冻结后读取的留出样本：
| case | group | split | budget |
| --- | --- | --- | --- |
| case-ed4335afc072 | B | heldout | standard |
| case-ec24264e4cbc | B | heldout | restricted |
| case-35a72490a498 | B | heldout | standard |
| case-1958f606d697 | E | heldout | standard |
| case-1470e353c845 | E | heldout | restricted |
| case-53234cebdcc4 | E | heldout | standard |
| case-4abf0d492899 | L | heldout | standard |
| case-ba69e2996f89 | L | heldout | restricted |
| case-165868710a50 | L | heldout | standard |
| case-13ecd0db85c6 | Q | heldout | standard |
| case-16d90287a7e6 | Q | heldout | restricted |
| case-9e638101e26b | Q | heldout | standard |

## 候选族 CV
| 族 | a | b | 开发 worst MSE | LOTO CV MSE |
| --- | --- | --- | --- | --- |
| no_factors | 0 | 0 | 0.418369 | 0.418369 |
| version_only | 0.49 | 0 | 0.385408 | 0.403991 |
| cost_only | 0 | 0.26 | 0.364373 | 0.381886 |
| both | 0.21 | 0.22 | 0.362205 | 0.401399 |
| original | 0.3 | 0.1 | 0.368551 | 0.368551 |

## 系数 bootstrap
固定种子、1000 次任务组重采样；P05–P95 是描述性范围，不是置信区间。若 selected_family=original，a=0.30、b=0.10 的零宽度来自固定候选约束，不是稳定性证据。
| 系数 | 均值 | P05 | P50 | P95 |
| --- | --- | --- | --- | --- |
| a | 0.3 | 0.3 | 0.3 | 0.3 |
| b | 0.1 | 0.1 | 0.1 | 0.1 |

## 留出比较
| 项目 | 值 |
| --- | --- |
| n | 12 |
| selected MSE | 0.584562 |
| original MSE | 0.584562 |
| selected−baseline mean | 0 |
| 描述性 P05–P95（非置信区间） | 0.0 — 0.0 |

## 独立后设敏感性
answer_event_id 的 exact-final / event-ID 审计修正后，独立重跑选择 cost_only（a=0, b=0.18），其 CV worst MSE=0.169922；同一敏感性输入下 original baseline 的 CV worst MSE=0.171248。该分析不是原预设 primary，不用于宣称 M4 不重要，也不提前作最终采纳判断。

## 方法与结果叙述
本研究对每个自动生成答案执行后评：六项预先定义的任务需求分别记录支持、缺失、矛盾或未核验状态，再按 supported/6 至 (supported+unverified)/6 合成答案质量区间，保留可辩护的上下界（开发集仅 2/24 个 outcome 为点值，M2 仅 1/24 个点值，M7 有 7/24 个 [1,5] 区间）；以任务组为留出单位，生态与预算条件留在组内。开发集纳入 24/32 个候选样本，排除原因逐条保留；选择只在开发集进行，冻结后才可评估留出集。候选族通过 leave-one-development-task-group-out CV 比较，损失为区间端点的保守 worst-case 平方误差；task-group bootstrap 只作描述性稳定性。自动后评是证据支持的答案质量代理，不是人工金标准。

## 限制
- 自动评委不是人工金标准；指标是答案质量代理，不是硬件成功率或校准概率。
- bootstrap 与区间用于描述性稳定性，不能证明通用最优。
- 预算是条件性设计；单一生成模型、每格单次运行，任务难度未必相等。
- worst-case 区间损失取保守的端点最大误差，不建模区间相关性；宽区间可能显著影响系数。
- m2_documents 没有逐文档语义校验，code_inspection 标签来自自动模型判断；精确引文只校验存在性。
- 无硬件执行；未知引文不静默记零；上一轮拟合系数不参与本轮。

## 文献 ledger
- [Hastie, Tibshirani & Friedman (2009), The Elements of Statistical Learning, 2nd ed.](https://hastie.su.domains/ElemStatLearn/)：Separate coefficient/model selection from assessment; repeat selection within validation; squared-error loss; resampling for stability.
- [OECD/JRC (2008), Handbook on Constructing Composite Indicators](https://publications.jrc.ec.europa.eu/repository/handle/JRC47008)：Composite weighting must expose assumptions and sensitivity; not an authority for particular coefficients.

## Answer-ID sensitivity: held-out validation
| Item | Value |
| --- | --- |
| n | 12 |
| selected MSE | 0.383193 |
| original MSE | 0.390623 |
| selected-original P05 | -0.040442 |
| selected-original P95 | 0.0265582 |

# 本轮结论与使用决定

48 次任务运行和 96 个独立后评上下文均已完成。开发集纳入 24/32 份，留出集纳入 12/16 份；12 份排除记录全部来自受限预算条件，原因是公式必需输入受阻、不适用或没有可评分的调用成本。因此，结果不能代表全部受限运行。

**本轮没有确定出稳定优于原系数的新系数。当前保留 a=0.30、b=0.10 作为工作基线，不将其称为经验证的最优权重。正式 Skill 未改。**

令 xi=Mi/5，当前工作公式为：

`K = 1 − (1 − x1×x2×x3)(1 − x5×x6)(1 − x7)`

`M11 = 100 × K × (0.70 + 0.30×x4) × (0.90 + 0.10×x8)`

M11 保持 0–100 分的连续综合指标。输入只有区间时输出区间；必要输入不适用或未定义时不补造点分。该分数不是正确率概率。

## 实际结果

1. 预定主分析中，双系数自由拟合为 a=0.21、b=0.22；其开发集留一任务误差为 0.401399，高于原系数的 0.368551，因而未被选中。主分析冻结选择为原系数。留出误差为 0.584562；与原系数差值为零是同一公式自比较，并不能证明有效。其他预存候选在留出集误差较低，不能据此回头改选，也说明开发集排序没有稳定延续。
2. 随后发现答案引用编号的机械误差。仅当引文逐字存在于最终答案中时修正 answer_event_id，保留原编号、原判断和主分析；不改任何指标输入、来源引文或答案文本。该后设敏感性分析在读取留出结果前独立冻结，选出 a=0、b=0.18。它在同一修正数据上的开发集 CV 误差为 0.169922，原系数为 0.171248。
3. 修正后的留出比较为新候选 0.383193、原系数 0.390623，改善约 1.9%；但按任务组重采样的“新候选减原系数”误差差值 P05–P95 为 −0.040442 至 +0.026558，跨过零。标准预算下新候选较好（0.340620 对 0.366721），受限预算下反而较差（0.468337 对 0.438426）。只有四个留出任务组，这些范围是描述性的，不是显著性检验或可靠置信区间。

不能把敏感性分析中的 a=0 解读为版本不重要，也不能用一次较小的平均误差改善删除版本因素。当前证据支持的决定是：不把本轮拟合值写入正式 Skill，不据此宣称评分体系或系数已经验证。

## 依据与论文使用边界

Hastie、Tibshirani 与 Friedman（2009）支持将模型选择与留出评估分离，以及使用交叉验证和重采样；OECD/JRC（2008）支持披露综合指标的权重假设与敏感性。它们均不规定这里任何具体系数、样本量或预算，也不直接证明本轮区间最大误差目标合理。

论文可以报告本次探索性拟合与留出比较及其失败边界，不能写成“已找到最优权重”或“已验证综合置信度”。若下一步仍以稳定估计权重为目标，优先补独立核验的答案质量标签与可判定输入，再开展新的预先冻结分析；继续增加相同自动后评流水线的运行数量未必能解决当前问题。

文献及实际阅读范围见 `literature.json`，本对话文献总账见 `../../reviews/conversation-literature.json`。所有原始任务过程、后评失败尝试、派生修正和冻结选择均保留。
