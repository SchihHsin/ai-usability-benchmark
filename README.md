# ai-usability-benchmark

在开发者任务上比较两个生态对检索型AI助手的知识支撑，使用统一M1–M11指标，并保存搜索、网页获取、最终回答和评分依据。

支持GLM、DeepSeek、Kimi等实际模型，以及用户指定的其他工具型模型。默认对照CANN/CUDA，也可替换为其他生态；不预设任一侧高分。

## 使用条件

需要实际的网页搜索、指定URL内容获取和文件保存能力。Python 3.9+用于本地计分与记录器，均仅用标准库。Skill本身不连接模型API、不提供搜索服务；在客户端配置真正的模型与工具。同一模型品牌的不同版本需分别记录。

将**整个仓库目录**复制到客户端支持的Skill目录；只复制SKILL.md会缺少脚本和判定规则。Codex个人安装示例：

```bash
mkdir -p ~/.codex/skills/ai-usability-benchmark
cp -R SKILL.md score_template.py references scripts ~/.codex/skills/ai-usability-benchmark/
```

其他客户端使用各自的安装位置。如果客户端没有Skill机制，可让Agent读取仓库内SKILL.md及其引用文件；仅把文字贴进不支持工具的普通聊天窗口，不能完成实测。

## 从哪里开始

1. 读[SKILL.md](SKILL.md)，确定任务、两生态、实际模型版本及同一工具协议。
2. 用[配置与Prompt](references/prompts.md)准备执行输入，按[记录规范](references/recording.md)保存过程。
3. 直接跑正式任务，第一批顺便检查日志和计分是否正常；不强制另跑校准实验或试跑批次。
4. 按[共同判定字典](references/rubric.md)整理观测，统一脚本计算，再用于矩阵、分析或论文。

## 计分

```bash
# 仅演示，不是实测结果
python3 score_template.py
python3 score_template.py --json

# 正式观测：参照月来自你的实验协议，不能由每个模型各自设定
python3 score_template.py --input observations.jsonl --as-of 2026-09 > scores.json

# 检查已保存的单次运行；不会访问网络
python3 scripts/run_log.py check --run-dir runs/example
```

正式输入格式及本地记录命令见[记录规范](references/recording.md)。`check`只检查文件/哈希/已登记事件是否完整，不能证明事件覆盖全部真实调用，也不能代替证据内容复核。

## 这次更新

- 增加任务×生态×模型×轮次的独立输入和完整证据记录要求。
- 同步已确认M2口径：`partial=3`，不再使用仓库早期的4分。
- 真实输入显式指定参照月，不再默认套用2026年6月。
- 零第三方来源：M5=1、M6“无来源”、SEC=0；信息缺失保持null，不能当成没有来源。
- 正式输入拒绝把官方文档/仓库/论坛/厂商博客混入第三方列表。
- 修正版本/成本乘子范围的文字说明，保留原系数及分档。
- 去掉基线满分预设，新增跨模型判分规则、Prompt和日志辅助脚本。

规则版本为`2026-09-14`。普通有效输入除已确认M2修正外沿用原公式；边界及兼容细节见[rubric](references/rubric.md)。旧实验文件不会被这些脚本自动更新。

## 开发检查

```bash
python3 -m unittest discover -s tests -v
```

本仓库包含通用方法及合成示例，不包含研究项目原始数据、模型凭证或论文附件。新增指标、统计报告、矩阵界面和论文写作应在各自任务中完成；不要为了三个模型同分而调整观测。
