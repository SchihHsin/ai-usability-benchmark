# 过程记录与输入格式

## 记录链路

实际问句 → 搜索请求与全部结果 → 选择的URL → 获取请求与实际返回 → 任务需求 → 最终回答 → RAW字段 → 分数。

按调用及时落盘，保留失败、空结果、重复获取、替代入口和未采用的来源。不要只保存最终回答或一个引用URL。原始返回与后续摘要、判断分开，按ID关联。

## 每次运行

metadata至少包含run_id、task_id、ecosystem、model_id、repetition、protocol_version、rubric_version，以及实际模型版本的取得依据/未知状态。另存客户端、工具和提供方、语言区域、采样与截断配置、预算、开始结束时间、时区、上下文/记忆状态。可见输入Prompt、Skill和任务包保存文本或版本哈希。

model_id使用实际配置中的模型标识，不通过模型自我介绍猜测。固定别名无法锁定底层版本时注明，不声称已控制版本。

## 搜索事件

- 实际工具名和原始查询参数；关键词、site/时间/语言过滤、分页、请求返回条数。
- 一次调用中的所有query，原始返回顺序及其所属query。批量查询数与调用数单独保存。
- **保存工具返回的全部结果**，每条保存位置、标题、原URL、域名、摘要、可见日期、版本线索和工具引用ID。工具只返回5条就保存5条，不补成10条。
- 保存官方/第三方/待定归类及依据、是否打开及后续获取事件ID。未打开不等于内容无用。
- 搜索目标、初次/改词/扩展/定站搜索、前一事件ID和简短改写理由。
- 工具返回位置、引擎真实排名、回答引用顺序分开；无法证实引擎排名时仅报告工具列表位置。
- 空结果、报错、开始结束时间、工具暴露的耗时/资源使用。

搜索工具原本没有暴露的字段标为not_exposed，不能从最终回答反推出搜索过程。

## 获取事件

| 维度 | 记录内容 |
|---|---|
| 入口来源 | 哪个query第几条，哪页链接/文档索引/站内搜索，用户提供还是模型提出；parent_event_id |
| 请求 | 原请求URL、目标信息、传给工具的提取指令、实际工具和非敏感参数 |
| 路径 | 可见最终URL、重定向、锚点、分页/offset、真实点击/跳转 |
| 获取方式 | HTTP、正文提取、浏览器渲染、独立Markdown地址、内容协商、TXT/PDF、仓库文件等 |
| 返回元数据 | 实际暴露的状态码、Content-Type、更新时间、大小、字符数、编码、耗时、缓存；不暴露则注明 |
| 完整可见返回 | 模型实际收到的正文、导航、元数据、表格、命令/代码、链接、引用编号、错误信息 |
| 完整性 | 截断/摘要/分页/分块，原工具限制与后续读取。没有原始HTML时不声称存了完整网页 |
| 结果与后续 | 正文/部分正文/仅导航/空返回/登录/限制/超时；依据；是否重试、换词、换入口、结束 |

原资源、工具返回和模型可见内容如不同，分别保存并说明能观察到哪一层。HTTP200不能直接当正文取得；工具错误也不能直接当网站内容问题。

实际用了浏览器才保存导航/点击，截图可作补充，不要求为所有URL另跑截图；截图不替代当次工具给模型的文本。

## 格式、交付、取得状态分别保存

- `source_format`：HTML、Markdown、TXT、PDF、JSON、代码文件、unknown；保存响应/扩展名等判断依据。
- `acquisition_method`：HTTP、browser、extractor、markdown_url、content_negotiation、download等实际方法。
- `returned_representation`：raw_html、extracted_text、converted_markdown、excerpt、summary、image、unknown。
- `delivery_evidence`：静态/SSR/动态页面的可见证据或unknown。没有证据不强行分类。
- `content_status`：目标正文取得、部分取得、仅导航、未取得、待定。

例如HTML页面由工具转成Markdown摘要，但摘要没有操作步骤：不能仅填“md获取成功”，也不能据此确定网站是静态或SSR。

## 来源、证据、需求与回答

- 来源用source_id，保留原URL/去重URL及规则、发布者、日期/版本及其出处、是否转载。不同URL不一定独立，同一URL在不同时间也不一定同一内容。
- 每次读取独立event_id，内嵌返回保留大小/哈希；不因后面成功而删早期失败。
- evidence_id关联返回事件内的字符区间和必要原文。整理后的“详尽”“有用”等评价不能替代原文。
- 任务需求逐项关联证据及支撑范围，标明命令、参数、步骤、诊断案例、版本适用关系。未取得支持不等于原网页不存在这些信息。
- 版本先保存component→version→source→compatibility；不同组件正常配套不直接算冲突。
- 保存最终answer原文，后处理可生成回答—证据映射；缺少外部依据不自动等同于错误或模型记忆。
- M7自评单独保存，不混进工具返回。自评、自动计数、内容判断、复核分别标注。
- 保存停止原因和未满足需求。预算耗尽、中断、工具故障与正常完成分别标记。

## 默认两文件结构

```text
runs/<run_id>/
  process.jsonl
  evaluation.json
```

问句、配置、回答不再单独存文件。每个过程事件一行JSON，公共字段为`seq`、唯一`id`、`type`、`recorded_at`。单个运行只允许一个写入者；不同运行使用不同目录。

| type | 主要字段 |
|---|---|
| run_start | schema_version=two-file-1、metadata、question |
| tool_request | role=search/fetch/other、实际tool、arguments、parent_event_id |
| tool_dispatch | request_id；客户端确认已向工具派发时登记 |
| tool_result | request_id、tool_status、response、observation |
| self_report / client_note | content；显式M7自评或实际客户端说明，不含隐藏推理 |
| run_end | answer、stop_reason；之后不再追加过程 |

`metadata`包含上文运行信息，以及公共Prompt、任务要求、协议/Skill/任务包版本和哈希；不可只存一个后来无法找回的临时路径。问句、response、answer用`{encoding, content, bytes, sha256}`内嵌：UTF-8文本保持换行原样，非UTF-8使用base64。哈希针对清理敏感信息后实际保存的字节。只保存模型可见内容、可公开的工具元数据；不保存隐藏推理或凭证。调用方须清理自由文本/URL中的令牌；脚本结构化凭证检查不能代替脱敏。

`observation`存客户端可见元数据，例如有序搜索结果、批量query数量、资源格式、返回形式、截断、可见时间与用量，以及导出/脱敏缺口。后续推断的内容质量、问题和恢复结论放进evaluation，不冒充工具返回。

## 记录器接入

```bash
python3 scripts/run_log.py init --run-dir runs/run-001 --metadata metadata.json --question question.txt
python3 scripts/run_log.py begin --run-dir runs/run-001 --event-id s001 --role search --tool actual_search --request request.json
# 客户端实际派发工具时登记dispatch；begin本身不代表调用已经发生
python3 scripts/run_log.py dispatch --run-dir runs/run-001 --event-id s001
# 实际调用返回后，response.txt为客户端导出的完整可见返回
python3 scripts/run_log.py finish --run-dir runs/run-001 --event-id s001 --response response.txt --status ok
python3 scripts/run_log.py end --run-dir runs/run-001 --answer answer.txt --reason task_complete
python3 scripts/run_log.py evaluate --run-dir runs/run-001 --input evaluation-input.json
python3 scripts/run_log.py check --run-dir runs/run-001
```

命令读取的metadata、question、request、response、answer、evaluation-input是客户端输入或临时导出文件，不是额外交付物；Python接口也可直接由封装层调用。finish可用`--observation info.json`附加元数据。重试新建请求ID，以parent关联前一请求或返回事件。

M7显式自评可用`report --run-dir runs/run-001 --event-id m7 --kind self_report --content self-report.txt`保存；客户端限制说明用`--kind client_note`。两者都在process内，后处理引用content片段。

工具未派发就被本地权限/预算阻止时，不登记dispatch，用`finish --status not_dispatched`保存实际阻止信息。工具已派发后失败使用error。客户端不暴露派发状态时保留请求和日志缺口，不能凭模型总结补派发事件。统计区分requested/dispatched/returned/not_dispatched；工具派发数不等同于网络HTTP请求数或批量query数。

记录器不执行搜索、不自动截获任何客户端工具调用、不强制工具预算；这些需要客户端/调度器实际接入。Prompt中的预算只是指令，不能声称硬限制。中断保留已有事件，恢复评价时说明缺口，不补造返回。脚本仅防止常规重复写入并检查哈希，不提供防篡改认证或并发写入保证。

## evaluation.json

文件顶层为`schema_version`、`run_id`、`revisions`。每次evaluate在同一个文件内增加修订，绑定完整process的SHA-256，保留旧判定。每个修订包含`evaluation`：

- `rubric_version`、`assessor`（实际评价者/脚本及方法）、`limitations`。
- `evidence`：每条有id、event_id、field（response/answer/question/content）、sha256、start、end、quote。字符位置为解码后Unicode字符，零起点，左闭右开；quote必须与对应片段完全相同。
- `requirements`：任务要求ID、覆盖状态、具体覆盖及不足、evidence_refs。
- `issues`：问题ID、受影响需求、障碍证据、尝试过的替代路径及其事件/证据、恢复状态、最终剩余缺口。用`event_refs`和`evidence_refs`链接真实材料。
- `metrics`：指标ID、观测、适用性、判定依据、score、状态、evidence_refs/event_refs；`v2-draft`的score必须为null。
- `overall`：新草案为null。来源去重表、回答—证据映射、M7自评提取结果放在本文件相应对象中，不另存文件。

示例片段（仅说明格式）：

```json
{
  "rubric_version": "v2-draft",
  "assessor": {"type": "human_or_model", "id": "实际评价者标识"},
  "limitations": ["尚未形成正式分档"],
  "evidence": [],
  "requirements": [],
  "issues": [],
  "metrics": [{"id": "M2", "score": null, "status": "pending", "observation": null}],
  "overall": null
}
```

空数组不代表没有问题，只表示尚未整理；须在limitations注明。`check`检查字节哈希、未完成请求、结束事件、评价与过程绑定、引文和引用是否可解析。它不判断引用是否足以支撑结论，也不能确认未导出的工具调用是否遗漏。缺少评价时会报告“尚未评价”，不会自动填分。

旧输入及公式仅见[旧版说明](legacy-recording.md)。新草案不能生成旧RAW后冒充新评分。
