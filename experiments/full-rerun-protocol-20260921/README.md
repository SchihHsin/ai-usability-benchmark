# 全量重跑执行准备

26任务×两侧×三模型=156次；G的CUDA栏实为ROCm迁移类比，保留运行但不纳入25对生态汇总。此目录仅完成协议修正，尚未声称全量已运行。

使用本目录tasks.json、protocol.json、frozen-skill与runner.py，不能读取旧结论。先运行prepare_assessment.py生成后评输入，再assess.py执行带门禁的后评。协议与评分范围在新采集前固定；旧18次结果不回写。

M2未知完整性、M6无第三方来源及Z不适用可合法导致M11缺失；修复流程不等于补齐所有点分。原公式与五档保持不变。

## 核验与复用

在本目录运行：

```sh
python3 -m unittest test_execution_checks -v
python3 prepare_assessment.py --runs ../three-model-pilot-20260921/runs --out validation-input
python3 validate_preparation.py
```

validation-input只为复用旧日志验证，不能作为新采集结果。后评新批次时用默认runs目录重新生成assessment-input。validation.json记录18份旧日志解析和156个计划组合的预检，live_model_runs=0。

正式安装的Skill仍保留旧版本；全量批次必须显式指定本目录frozen-skill，不能使用默认安装入口。已确认五档和M11公式逐字保留于references/rules.md；仅追加execution-checks.md和机器检查。约束语义、来源主体判定仍须内容复核，自动门禁并不保证评分正确。
