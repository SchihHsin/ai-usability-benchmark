# 旧版多文件记录（仅兼容既有数据）

记录器路径使用`scripts/legacy_run_log.py`。新运行使用[两文件规范](recording.md)。

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
- 每次读取独立event_id，返回文件保留大小/哈希；不因后面成功而删早期失败。
- evidence_id关联返回文件的行号/段落/字符区间和必要原文。整理后的“详尽”“有用”等评价不能替代原文。
- 任务需求逐项关联证据及支撑范围，标明命令、参数、步骤、诊断案例、版本适用关系。未取得支持不等于原网页不存在这些信息。
- 版本先保存component→version→source→compatibility；不同组件正常配套不直接算冲突。
- 保存最终answer原文，后处理可生成回答—证据映射；缺少外部依据不自动等同于错误或模型记忆。
- M7自评单独保存，不混进工具返回。自评、自动计数、内容判断、复核分别标注。
- 保存停止原因和未满足需求。预算耗尽、中断、工具故障与正常完成分别标记。

## 最低文件结构

```text
runs/<run_id>/
  metadata.json
  question.txt
  events/<event_id>/
    request.json
    response.bin
    result.json
  answer.md
  observations.json
  scores.json
```

JSONL形式的全量事件索引也可以使用，关键是每个事件、时间和原始返回能还原。可在后处理派生search_results、sources、acquisitions、evidence、requirements和answer_evidence表；不要求执行模型每步手填所有重复表格。

大返回可无损分块/压缩，保存顺序与哈希。不能为省输出空间静默截断原始工具返回；工具自身已截断时只记录实际收到的内容和缺口。

原始指研究相关且可留存的返回。保存前移除凭证和签名令牌；如需脱敏，留变更说明，哈希对应所保存版本。不要采集浏览器凭证、无关聊天、隐藏推理或本机其他私人材料。

## 本地记录器如何接入

在工具封装层/Agent工作流中，调用前begin，调用后finish。记录器不自动接入任何模型或搜索工具，不把普通模型总结变成原始返回。

以下命令的JSON与返回文件来自真实运行；event-id须唯一：

```bash
python3 scripts/legacy_run_log.py init --run-dir runs/run-001 --metadata metadata.json --question question.txt
python3 scripts/legacy_run_log.py begin --run-dir runs/run-001 --event-id s001 --role search --tool actual_search --request request.json
# 此处由实际客户端执行真实搜索，将工具返回导出为response.txt
python3 scripts/legacy_run_log.py finish --run-dir runs/run-001 --event-id s001 --response response.txt --status ok --observation search-info.json
python3 scripts/legacy_run_log.py begin --run-dir runs/run-001 --event-id f001 --role fetch --tool actual_fetch --request fetch-request.json --parent s001
# 客户端实际读取后，同样调用finish；失败也保存工具实际错误返回
# 将实际最终回答保存为runs/run-001/answer.md
python3 scripts/legacy_run_log.py check --run-dir runs/run-001
```

`--observation`是可选附加信息，例如有序搜索结果、资源格式、内容状态、是否截断，缺省时保存空对象；RAW字段需要的信息不能因此被当作已记录。`--status ok/error`表示工具调用状态，不是正文充分性，不能直接等于fetch_fail。

begin在请求前登记；中断时只有request.json也会保留。finish保存完整提供文件的字节并计算哈希，不覆盖已有返回。重试建立新事件，parent关联前次事件。

check输出已登记search/fetch/other调用数及事件索引，并检查问句/返回哈希、未完成事件和answer文件。不自动推导fetch_fail，不核验语义或虚构的事件，也不保证未登记的真实调用没有发生。

同一run只由一个记录器进程串行写入；并行运行使用不同目录。记录器结构化凭证键检查只是辅助，调用方仍需清理自由文本或URL中的令牌。

## 统一计分输入

以下为格式示意，不是实验观测。JSON输入为记录列表；JSONL每行一个记录。

```json
[
  {
    "run_id": "glm-D-cann-1",
    "task_id": "D",
    "ecosystem": "CANN",
    "model_id": "configured-model-version",
    "repetition": 1,
    "protocol_version": "study-1",
    "rubric_version": "2026-09-14",
    "reference_month": "2026-09",
    "raw": {"rounds": 1, "rank": 4, "refine": false, "core_fetch": null},
    "field_status": {"core_fetch": "unknown"},
    "evidence_refs": {"rounds": ["s001"], "rank": ["s001:result4"], "refine": ["s001"]}
  }
]
```

完整字段见[rubric](rubric.md)。sources/platforms/dates逐项对应，日期可为null。空列表表示实际检查后无来源；缺失记录使用null。每个用于计分的字段在evidence_refs有非空ID列表，引用的实际材料必须存在；脚本只校验ID格式，引用解析和真实性须另行复核。

输入中的field_status、详细归类理由、证据文本保留在原始观测文件中；计分输出只保留身份、分数、中间量和缺项摘要，通过run_id关联原输入，不替代原始材料。

实际可锁定的模型版本和协议版本由运行配置提供，不得根据上述示例字符串伪造。当前脚本不会自动验证元数据所声明的模型是否真的执行过任务。

输出scores按M1–M10顺序，metric_status分别为scored/blocked/no_sources/missing/unverified；M11是overall及overall_exact。None转JSON null，不能被前端显示为0分。原始分1–5和综合0–1使用各自图例。
