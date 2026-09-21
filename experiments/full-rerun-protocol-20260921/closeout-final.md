# full-rerun-protocol-20260921 收尾核对

更新时间：2026-09-21T23:02:41。本报告对应本次提交；精确原始记录、字段修订及依据见 closeout-final.json / closeout-approved-changes.json。

## 完成状态

| 层级 | 结果 | 含义 |
|---|---|---|
| 有效采集 | 156/156 | 经完成性检查，排除只有检索前回答的运行 |
| 后评分完成 | 156/156 | predictors、outcome 均有结果；不等于每项可定分 |
| 单元结构门禁 | 149/156 | 其余保留来源归属等证据问题，不宣称全部通过 |
| 引文核验 | 156/156 | 引文在实际保存的返回或最终回答中存在 |
| 内容复核 | M10 3/4/5 共 149 单元，I任务及已识别问题完成 | 限本次指定范围；未上卡执行、未验证所有技术断言 |

批次记录完整性检查无错误；35项本地回归测试通过；29个冻结文件哈希一致。

## 补齐与作废

- 原 Kimi U-CUDA T133844 无工具派发、无独立最终回答，已作废并排除。原始记录和旧后评分全部保留。完成性修复在独立 overlay 中，不修改冻结 guard。
- GLM U-CUDA 额外第1次成功；Kimi U-CUDA 第1次失败、第2次成功；DeepSeek 原始 R-CUDA predictors 额外第1次成功。成功后停止，未按分数择优。
- 调度曾误触发 DeepSeek R-CUDA 重复采集 T223905，已隔离作废并保留全部原始记录，未用于结果；此事见 closeout-dispatch-incident.json。

## 修订依据

本次累计 34 项指标修订/恢复，逐项旧值、新值、运行ID和理由见 closeout-approved-changes.json；另有不改变评分规则的逐字引用修复。

- M10沿用冻结锚点：仅替换明确环境参数为4，需纠错或补实质内容为3，可直接执行且前提完整为5；未实际运行本身不扣分。原146条审阅加新单元补审，最终覆盖所有3/4/5。
- I-CUDA原3/4/5并无足以支撑后两档的独立证据：缺少所选PyTorch wheel与实际cuDNN配套关系，按各自材料复核为3；并非强制模型一致。Kimi I-CANN M9原N/A与冻结适用范围不符，改3。
- DeepSeek R-CUDA M4保留4：已取得同版PyTorch 2.14接口及迁移约束，可合并确定适用性；用户本机版本未知不等于该任务缺少官方对应关系。
- 第三方材料已出现但无法核验时保留证据不足，不标为不适用、不补0。来源归属仍无法确认者继续保留未知。

## M11与剩余问题

全批：{"bounded": 106, "incomplete_inputs": 21, "calculated": 29}。
主分析150单元（排除G）：{"bounded": 101, "incomplete_inputs": 20, "calculated": 29}。
G的6单元单列：{"bounded": 5, "incomplete_inputs": 1}。

点值、证据上下界和输入不足分别报告；证据界不是置信区间。共有21个单元输入不足，逐项缺失指标及理由见 closeout-final.json。未新增外部证据填补这些未知。配对汇总仅使用各指标可用的完整配对，样本量随指标变化，不把缺失对补齐。

## 文件

- results.json / results.html：最新结果及各单元状态。
- assessment-status.json：两阶段评分状态。
- paired-summary.json：G单列的配对汇总。
- batch-audit.json / arithmetic-audit.json / review-audit.json：结构、独立算术及引文审计。
- m10-closeout-review.json / m10-closeout-supplement.json：M10逐项复核。
- version-source-closeout-review.json / additional-m9-closeout-review.json：版本、适用性及来源复核。

论文、正式安装的Skill、冻结公式与系数均未修改；没有全量重跑。
