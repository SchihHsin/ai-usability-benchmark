# M11 uniform fit 结果（2026-09-21）
状态：**采集完成，后评与拟合进行中**

尚无冻结系数；不得从旧实验推断新结果。

## 公式
M = 100 × K × (1 − a × (1 − M4/5)) × (1 − b × (1 − M8/5))；K = 1 − (1 − (M1/5)(M2/5)(M3/5))(1 − (M5/5)(M6/5))(1 − M7/5)。所有 Mi 先按原始 1–5 分除以 5。

历史 baseline：`a=0.30, b=0.10`，仅作对照。候选五族及 LOTO 选择按 protocol.json 执行。

当前没有 `frozen-selection.json`，因此不报告新系数，不读取留出数据，也不把旧实验系数当作本轮结果。

## 研究限制
- 目标是证据支持的答案质量代理，不是硬件成功率或校准概率。
- 预算与任务设计是条件性设计，不是文献证明的最优方案。
- 模型真实 alias 不能保证不可变后端身份；自动评委不是人工金标准。
- 无硬件执行；未知引文不静默记零；旧实验仅作历史链接。

## 文献 ledger
- [Hastie, Tibshirani & Friedman (2009), The Elements of Statistical Learning, 2nd ed.](https://hastie.su.domains/ElemStatLearn/)：Separate coefficient/model selection from assessment; repeat selection within validation; squared-error loss; resampling for stability.
- [OECD/JRC (2008), Handbook on Constructing Composite Indicators](https://publications.jrc.ec.europa.eu/repository/handle/JRC47008)：Composite weighting must expose assumptions and sensitivity; not an authority for particular coefficients.
