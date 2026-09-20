# M11 uniform fit 结果（2026-09-21）
状态：**系数已冻结，等待留出验证**

## 公式与选择
M = 100 × K × (1 − a × (1 − M4/5)) × (1 − b × (1 − M8/5)); K = 1 − (1 − (M1/5)(M2/5)(M3/5))(1 − (M5/5)(M6/5))(1 − M7/5).

历史 baseline：`a=0.30,b=0.10`；候选五族和 leave-one-development-task-group-out 选择按 `protocol.json` 执行。留出前冻结族与系数，结果不宣称通用最优。

冻结选择：`original`，a=0.3，b=0.1。
开发输入 hash：`7fb7adcfe3ee35b42f98d4185434509b9fc0862005ba2b0316084a9547df2020`。

## 样本与排除
协议预期运行数：48；开发任务：['A', 'C', 'D', 'F', 'I', 'J', 'K', 'P']；留出任务：['B', 'E', 'L', 'Q']。

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

## 候选族 CV
| 族 | a | b | 开发 worst MSE | LOTO CV MSE |
| --- | --- | --- | --- | --- |
| no_factors | 0 | 0 | 0.418369 | 0.418369 |
| version_only | 0.49 | 0 | 0.385408 | 0.403991 |
| cost_only | 0 | 0.26 | 0.364373 | 0.381886 |
| both | 0.21 | 0.22 | 0.362205 | 0.401399 |
| original | 0.3 | 0.1 | 0.368551 | 0.368551 |

## 系数 bootstrap
固定种子、1000 次任务组重采样；P05–P95 是描述性范围，不是置信区间。
| 系数 | 均值 | P05 | P50 | P95 |
| --- | --- | --- | --- | --- |
| a | 0.3 | 0.3 | 0.3 | 0.3 |
| b | 0.1 | 0.1 | 0.1 | 0.1 |

## 限制
- 自动评委不是人工金标准；指标是答案质量代理，不是硬件成功率或校准概率。
- bootstrap 与区间用于描述性稳定性，不能证明通用最优。
- 预算是条件性设计；单一生成模型、每格单次运行，任务难度未必相等。
- worst-case 区间损失取保守的端点最大误差，不建模区间相关性；宽区间可能显著影响系数。
- m2_documents 没有逐文档语义校验，code_inspection 标签来自自动模型判断；精确引文只校验存在性。
- 无硬件执行；未知引文不静默记零；旧实验系数不参与本轮。

## 文献 ledger
- [Hastie, Tibshirani & Friedman (2009), The Elements of Statistical Learning, 2nd ed.](https://hastie.su.domains/ElemStatLearn/)：Separate coefficient/model selection from assessment; repeat selection within validation; squared-error loss; resampling for stability.
- [OECD/JRC (2008), Handbook on Constructing Composite Indicators](https://publications.jrc.ec.europa.eu/repository/handle/JRC47008)：Composite weighting must expose assumptions and sensitivity; not an authority for particular coefficients.
