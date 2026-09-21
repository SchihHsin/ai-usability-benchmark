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

## Continuation checkpoint 2026-09-21 11:32

- User explicitly said quota should be restored and asked retry. GLM K-CANN retry 111330 succeeded; all3 Luna collectors resumed. Quota incident persisted in quota-incident.json. Do NOT stay paused on the old429.
- Current valid collected78/156: GLM22, DeepSeek39, Kimi17. GLM L-CUDA timeout retry and Kimi I-CUDA timeout retry underway; both authorized once after restoration (quota attempts do not consume the nonquota retry allowance).
- DeepSeek malformed A-CUDA 095406 was invalidated (only prior plus malformed XML, no real dispatch), then successfully recollected. run-invalidations.json excludes original from analysis; all raw material retained. completion_guard.py rejects this condition. freeze-manifest controller hash update recorded in completion-guard-repair.json; frozen questions, prompt, skill, budgets unchanged.
- Root assessment sessions: 79898 GLM (current snapshot), 45262 DeepSeek (early25 snapshot), 44899 Kimi (new17 snapshot). Earlier37081/68234 done. Restart snapshots on completion until all completed collector units assessed; per-case locks prevent duplicate model calls. Agents still assess after52.
- run recover_assessment_shapes.py before review to rescue unambiguous note/container errors without model calls. JSON-decode failures may still need bounded retries. assess_model.py now discounts recognized quota-only failures from the two nonquota technical-attempt limit after user recovery.
- review_normalization.py conservatively changes unsupported body completeness claims to unknown [4,5], preserving frozen bands. Same-document exact boundary required. 2 unit tests passed. Does not fix uncertain ownership.
- Three Luna agents also review limited batches during collector wait. reviewer-corrections-*.json are PROPOSALS, not automatically approved. Root rejected nearby/different-semantic substitutes. Accept only unchanged claims with exact source assertions; add approved records to reviewed-quote-corrections.json (case-scoped support added). GLM E CPU’s full-sentence repair still needs merging from latest reviewer-corrections-glm.json; some rejected entries were removed by agent. Kimi agent initially failed to locate hash-named files; explicit case IDs sent.
- ownership-references/ contains external ownership metadata ONLY, never model support. ReadTheDocs project API verifies ascend.readthedocs.io repository github.com/ascend/docs. Huawei Cloud blog393282 and author profile only self-signed 昇腾CANN; ownership remains unknown. Do not pretend unknown blog is official.
- Last derived results: 28 units assessed,14 M11 bounded,14 incomplete inputs pending mostly citation/ownership review; do not claim final scores ready. audit_batch.py at76 had no protocol/hash/log issues. source-index at83 ended attempts had253 queries/1265 results; includes retained failed attempts.
- Latest checkpoint1d371fb pushed ended raw evidence/assessments. Latest code55993bb for completeness normalization; push19395 needs final verification. Paper untouched. Need continue through full156, all assessments/review, final audit/report, commit/push. Not done.


## 2026-09-21 12:09 continuation

- DeepSeek collection completed 52/52; GLM26 and Kimi24 valid at snapshot, total102/156. All remaining collection and postassessment processes still running.
- Invalidated Kimi I-CANN 111015: only prior answer + promise to search, zero dispatches, client mislabeled complete. Preserved process/assessments and instructed Kimi worker to recollect after current queue. completion-guard-search-intent-repair.json records guard hash update; model task/prompt/rubric/budgets unchanged.
- Root continues assessment snapshots (Kimi session37201; GLM79898; DeepSeek45262 plus worker full52 snapshot).
- Reviewed quote, repeated-fetch inventory and semantic version corrections remain in reviewed-*-corrections.json. M6 F-CANN GLM=3 from explicit claim-to-official-source review; I-CUDA GLM M4=3 because shared CUDA compatibility does not establish PyTorch/cuDNN ABI compatibility.
- Protocol and formula unchanged. Paper untouched. No final completeness claim.


## 2026-09-21 12:35 continuation

- Valid collection 108/156: DeepSeek 52, GLM 27, Kimi 29. Assessment 62; gate passed 56; quote-clean 39. No claim of full completion.
- GLM N-CANN first 600s timeout retained; same-protocol retry 123059 active under Luna controller 80013. Kimi queue remains active; invalid I-CANN must be recollected after queue.
- Root GLM assessment snapshot session 9236 active; Kimi 37201 and DeepSeek full snapshot managed by Luna.
- Approved exact transcription fixes for DeepSeek G-CUDA and K-CANN, plus negative-conflict list correction. Rules/formula unchanged.
- reviewer-kimi-j-inventory.json is an UNAPPROVED proposal: must include third-party event 8, preserve known incomplete states and exact substantive quotes before application.
- All 26 focused tests pass; batch selected collection issues empty. Paper untouched.


## 2026-09-21 12:56 continuation

- Valid collection 118/156 (GLM32, DeepSeek52, Kimi34). New I-CANN Kimi125026 successfully replaces invalid111015; all current technical_attention zero. Queues continue Q/R.
- Assessment72→74; root GLM snapshot9236 and Kimi61977 active, DeepSeek full52 snapshot under Luna.
- Exact quotation repairs, J-CUDA per-dispatch inventory repair accepted by root (not the reviewer proposal); original third-party and truncation states preserved.
- Actual M10 content reviews: GLM A-CUDA tuple.name error reproducible with minimal Python; grade3. DeepSeek H-CUDA deployment lacks buffer/runtime setup; grade3. Several original grade5 judgments requiring environment substitution corrected to original grade4. GLM J-CANN M9 conditional bands→grade4. No rubric/formula changes.
- Independent M11 expanded-polynomial arithmetic check passed all53 then-computable rows; arithmetic-audit.json. Missing source evidence remains missing rather than fabricated.
- Recent pushed commits f83bd9f,fc9af6b,5eecbd3; pending next review checkpoint. Paper untouched.


## 2026-09-21 13:26 continuation

- Collection128/156: GLM38, DeepSeek52, Kimi38, no current technical_attention. GLM/Kimi continue remaining tasks under existing Luna controllers. Kimi I-CANN replacement125026 valid; do not repeat it.
- Root assessor snapshots19523(GLM) and60105(Kimi) active; DeepSeek full snapshot under Luna, with bounded technical retries after first pass.
- Latest report90 assessed,78 structural gates passed,66 quote-clean; pipeline must refresh as assessments finish.
- Root restored exact DeepSeek N-CUDA/O-CANN source and final spans; no rule/score change. 28 focused tests pass.
- paired_summary.py now uses exactly25 tasks excludingG, per-model both-side gate+quote checks, explicit exclusion reasons and source run IDs, cross-endpoint difference bounds. Synthetic denominator/difference/exclusion checks passed. No fitting or inferential claims.
- Latest preceding push e0b861e verified. Paper and installed skill untouched. Continue through156 and postassessment.


## 2026-09-21 13:45 continuation

- Collection136/156 (GLM41, DeepSeek52, Kimi43) last snapshot. GLM U-CUDA, Kimi V sequence active. Keep same Luna collectors; DeepSeek assessor full snapshot/retry still active.
- Root GLM assessor19523 ended, replaced by67275; Kimi60105 active (recent34f predictors and1a4 outcome technical errors require bounded retries when snapshot ends).
- Latest consolidated100 assessed,92 gate pass,85 quote-clean; subsequent exact-span corrections pending next pipeline. No final completion claim.
- Root verified many exact source/final/prior restorations. Reject reviewer substitutions of final for M7 prior and source for answer_quote; decisions recorded reviewer-proposal-decisions-1332.json. Do not auto-apply reviewer proposals.
- GLM P-CANN repository-migration notice explicitly not version conflict removed from unresolved_conflicts; original record retained. M4 unchanged. GLM J/M/O per-return evidence corrected. GLM N/R official search metadata registered with processSHA, not body credit. DeepSeek O per-return quotes restored. Kimi M-CANN erroneous WebFetch1 reference corrected to actual WebSearch1 official PDF URL metadata, not PDF acquisition.
- Latest pushed1c5d786 verified. Further corrections after this commit need push. Installed skill/paper unchanged. Continue156 collection+all possible assessments; no fitting.


## 2026-09-21 14:04 continuation

- Collected139/156 last build. GLM U-CUDA133705 and134726 both technical failures (missing tool returns); no third retry. collection-exhausted.json marks this one unit uncollected. GLM Luna now runs run_remaining_glm.py (same runner/args/order/freeze29-hash checks; skips only completed and exhaustedU-CUDA) throughV-Z. Do not resume original run_model.py glm or it would reattemptU.
- Kimi W-CANN134810 prior_only_no_final_answer failed, retry135205 succeeded; W-CUDA135548 succeeded. Kimi46/52 advancingX-Z.
- Root Kimi60105 ended, restarted50539. GLM67275 active. DeepSeek agent full snapshot/technical retries still active; followup sent when agent prematurely finalized.
- Latest report103 assessed,94 gates,101 quote-clean. New review work after build pending. M6 DeepSeekD/F changed from inappropriateN/A to originalgrade3 based on actual third-party snippets+official support; unknown claims preserved, notes in review-notes-deepseek-df-m6.json. No channel auto-zero.
- recover_assessment_shapes.py now handles unscored M3_note as well as -note, preserves supplementary notes; checked actual recoveredcase34f. No model call/grade changes.
- Root restored remaining exact source/final quotations; F-CANN Kimi answer_quote still not found as exact passage, don't fabricate.
- audit_arithmetic.py independent polynomial check87 computable rows, issues=[]; repeat after final results. paired_summary.py excludes exhausted cell with explicit reason, reports only eligible pairs, no statistical inference. results.html now explicitly marks exhausted cell and links failure record.
- Latest pushedc20db75 verified; later changes await next push. Frozen29 hashes verified unchanged. Paper/installedSkill unchanged. Continue all other collect/assess units; explicitly report genuine exhausted failures, never claim156 success.


## 2026-09-21 14:22 continuation

- Collection146/156; assessed114; gates102; quote-clean109. GLM wrapper continuing after successful V-CUDA retry; exhausted U-CUDA remains uncollected. Kimi last cell active.
- Root assessment snapshots67275/50539 and supplementary25551 remain active; DeepSeek full pass under Luna. Same frozen protocol and bounded technical attempts.
- Root restored9 exact same-event source/prior/final quotations in GLM U-CANN, DeepSeek M-CUDA/R-CANN/S-CANN; no scores/rules changed.
- 31 focused tests pass; selected collection audit issues=[]; independent expanded-polynomial M11 check94 rows issues=[].
- Continue remaining collection/assessment and evidence checks. Paper and installed skill untouched.


## 2026-09-21 14:37 continuation

- Collection148/156 (GLM44, DeepSeek52, Kimi52). GLM remaining wrapper active; frozen U-CUDA exhausted, W-CUDA retry status under Luna.
- Assessed127; gates116; quote-clean124; independent M11 arithmetic105 computable rows no differences. Root GLM snapshot95413 replaced completed67275; Kimi50539, supplementary25551, DeepSeek agent process continue.
- Added assessment_status.py and report links distinguishing pending versus exhausted phases; no null converted to score.
- Recovered a398 predictors by removing single extraneous trailing brace, b3df predictors by escaping exactly two quotes around [...] in M2 reason. Raw failures/hash provenance preserved. No model calls or score changes in recovery.
- F-CANN Kimi requirement corrected to unverified with exact final gaps (global rank/multi-node launch), M10 stays3. Rejected reviewer-kimi-final-quote-proposals.json: final_exact claims did not match actual final; not authoritative.
- A-CUDA DeepSeek M4=3 under existing anchor: complete version relation still missing; raw4 inconsistent with own checklist. Exact quotes/official snippet provenance repaired; unknown ownership remains unknown.
- Paper/installed skill untouched. Continue all possible phases and evidence review before final report.


## 2026-09-21 14:50 continuation

- Collection150/156 (GLM46, DeepSeek52, Kimi52). W-CUDA unique retry143422 succeeded; X-CUDA144239 complete. U-CUDA exhausted only. GLM continuesX-CANN/Y/Z.
- Root GLM snapshot77349 ended, restarting newest completed input. Kimi50539 ended and replaced28502 (PID27722); supplementary25551 still running. DeepSeek agent original process still active. No duplicate collectors.
- Phase report276 completed,21 pending,1 exhausted (DeepSeekR-CUDA predictors both900s timeouts/no saved output). S-CANN GLM recovered schema: main requirement plus redundant version subrequirement sharing same id/status; second preserved as supplementary note, not double counted. All raw judgments retained.
- S-CANN GLM M10 enforced4 (explicit user-environment substitutions) under frozen anchor. T-CANN GLM missing official dispatch inventory restored from exact title/widget return. T-CUDA DeepSeek target chapter absent/other Architecture Overview returned: preserve original assessor1 with received-body-of-different-page metadata, no fabricated target body.
- Root exact-quote corrections continue; rejected Kimi proposal now explicitly tagged rejected_do_not_apply. No paper/installed-skill edits. Frozen29 hashes unchanged and31 focused tests pass. Latest pushc45f140 verified.


## 2026-09-21 17:34 continuation

- Collection closed:155/156 valid (GLM51, DeepSeek52, Kimi52). U-CUDA GLM exhausted two technical attempts; no third attempt. All collected runs ended.
- Assessment308 phases complete, one GLM Z-CUDA predictor in progress (root session99058), one DeepSeek R-CUDA predictor exhausted two900s attempts. Final GLM Z-CANN assessed.
- Restored exact final/source Markdown quotations for final X/Z cases; raw assessor outputs retained. Ownership unknowns remain unresolved.31 focused tests pass. No changes to paper, installed skill, frozen rules or coefficients.


## 2026-09-21 17:35 execution closed

- No pending requests remain: collection155/156 valid; GLM U-CUDA exhausted two technical attempts. Assessment309/310 collected-case phases complete; DeepSeek R-CUDA predictors exhausted two900s timeouts.154 cases have both assessment phases.
- 154 complete assessments have no unmatched evidence quotations;146 pass structural gates. Eight retain unresolved source-ownership / M4 conflict / missing official-document gates. Passing gates is not semantic validation.
- M11:27 point results,105 evidence-bounded results,22 incomplete-input results,2 without complete assessment. Bounds are not confidence intervals or calibrated probabilities. No imputation.
- Independent arithmetic verified132 computable cases without differences;29 frozen hashes unchanged;31 focused tests passed. Results and paired-summary include exclusions and original evidence links.
- Collection and post-assessment retry allowances are exhausted only for the two documented cells above; no third retries. Paper and installed Skill untouched.


## 2026-09-21 targeted closeout authorization

- User authorizes at most two additional technical attempts per named cell: GLM U-CUDA collection, Kimi U-CUDA collection, DeepSeek R-CUDA predictors. First valid result wins; no full rerun.
- Kimi U-CUDA133844 invalidated: only prior plus unexecuted search intent; zero dispatch/no independent final. Raw run and assessments retained but excluded from selection and derived summaries.
- Frozen completion_guard retained byte-identical; explicit completion_guard_closeout overlay fixes missed intent variant. Selection now applies guard and retains first valid ledger record. All29 frozen hashes unchanged.
- Full M10 anchor-consistency audit and I-version/source-ownership evidence review underway; no new rubric/formula/coefficient changes.
