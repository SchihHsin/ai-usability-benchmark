# 开发者生态 AI 可用性 Benchmark

在对应开发任务上比较两个生态对检索型AI助手的知识支撑。支持GLM、DeepSeek、Kimi等实际模型；本仓库不提供模型服务或凭证。

## 本次更新：每次运行两个文件

- `process.jsonl`：问句、配置、真实搜索/获取请求和返回、最终回答、停止原因。
- `evaluation.json`：需求覆盖、问题与替代路径、恢复结果、证据引用、指标观测及修订。

保留完整工具可见内容。后续成功不会覆盖早先障碍；不同模型不要求同分，而是比较实际共同问题及恢复差异。

## 使用

将整个仓库复制到客户端的Skill目录；Codex通常为`~/.codex/skills/ai-usability-benchmark/`。其他客户端用各自安装位置。阅读[SKILL.md](SKILL.md)，按[Prompt](references/prompts.md)执行，按[记录规范](references/recording.md)接入客户端。

```bash
python3 scripts/run_log.py --help
python3 scripts/run_log.py check --run-dir runs/example
```

记录器提供init/begin/dispatch/finish/report/end/evaluate/check；不自动拦截工具、不执行模型、不强制预算。只有客户端实际导出并接入，才能自动保存真实过程。格式检查不等于内容判断已验证。

## 评分版本

新实验默认`v2-draft`，按[评价规则](references/evaluation.md)保存观测；分档未定稿，分值保持null。任务配对和规则未确定时不称正式评分实验。

`score_template.py`及[rubric](references/rubric.md)保留旧版`2026-09-14`。仅显式选择此版本的输入可计算；旧实验不自动改分，不能把新定义套进旧公式。既有多文件运行使用`scripts/legacy_run_log.py`检查，见[旧版说明](references/legacy-recording.md)。

## 检查

```bash
python3 -m unittest discover -s tests -v
```

仓库仅包含通用规则、程序和合成测试，不包含真实研究数据、凭证或论文附件。矩阵、论文和模型服务接入按各自任务处理。
