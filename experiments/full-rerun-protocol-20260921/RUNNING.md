# 全量实验进行中

本批次156个计划单元；采集未完成不得宣称全量完成。GLM、DeepSeek、Kimi各52次。3个5.6 Luna子代理分别调度；程序run_model.py按ledger跳过已核验成功项。旧18次试跑未并入本批次。

采集后按模型运行assess_model.py，统一GLM自动后评；后评需继续复核门禁失败，不等同于技术验证。每次两个评价。后评技术失败最多保留两次尝试，不能按评分择优。已有第一份GLM后评超时、第二份outcome ID结构错误，已保留，后续用显式ID schema和900秒超时。

完成采集后prepare_assessment.py按本批次runs生成assessment-input；consolidate_evaluations.py追加evaluation修订，不改process。后续须核对312份评价状态、逐项未完成原因及M11点值/区间。不能调用assess.py --export把门禁失败当拟合有效样本，本批次不拟合系数。

首条GLM/DeepSeek/Kimi采集实际成功但控制器读错evaluation层级，ledger保留原false并追加true修复记录，原始运行未重跑；controller-repair.json和各ledger可追溯。评分规则和协议未因此改变。

status.py生成status.json/progress.html。采集和评分完成数分别报告。git每轮仅提交本实验相关资料，不动论文。

## Continuation checkpoint 2026-09-21 10:54

- 56/156 collected: GLM17, DeepSeek27, Kimi12; all three Luna collectors active.
- Root overlaps early assessment snapshots: sessions 37081(GLM), 45262(DeepSeek), 68234(Kimi). Agents still run assess_model.py after their52 to pick later units; locks prevent duplicates.
- `review_quotes.py` derives corrections from original raw assessments: exact event suffixes/unique exact quote matches, evidence containers, escaped whitespace; reviewed explicit substitutions in `reviewed-quote-corrections.json`, field corrections in `reviewed-field-corrections.json`. No raw assessments are overwritten. An unsupported claim of M2 completeness becomes unknown [4,5], consistent with frozen rules.
- `reviewed-channel-states.json` has audited B-CANN GLM third-party unavailable state, bound to original process hash. All10 search results and7 fetches were checked as official; this describes only material obtained in that run.
- `audit_batch.py` audits all successful logical units: hashes, actual model, dispatched budget, log integrity. At53: no issues. `build_results.py` builds results.html/json with separate collection/assessment/review counts, no fabricated missing scores.
- Derived evaluation revisions include consolidation script hash; original M11 coefficients remain fixed. Paper untouched.
- Latest code commit d61fd82 pushed (session18746 should be checked). Checkpoint84cde1a retained ended evidence; running files were not staged. Keep periodically pushing ended evidence and derived reports.
