# 搜索与获取预算的执行前限制

预算值来自每批协议，不固定为所有任务4/8。新运行在工具执行前检查；超额请求保存为not_dispatched，不进入M8。不要删除超额请求或依赖模型自报计数。

## WorkBuddy

`scripts/budget_hook.py`接入PreToolUse，原子检查并预留search/fetch名额；并发请求也不能突破上限。达到上限时返回明确deny，通知模型根据已有材料完成回答。准许时不绕过客户端本身的权限检查。损坏账本、预算中途更改或误用其他会话账本均拒绝执行。

调度器为每个新会话创建独立临时目录，构造settings：

```python
from scripts.budget_hook import workbuddy_settings
settings = workbuddy_settings(scratch / 'budget.jsonl', search=4, fetch=8)
# 将settings合并到该会话已有settings中，保留权限配置；传给WorkBuddy --settings。
# 若已有其他PreToolUse hook，合并数组，不能覆盖它们。
```

必须允许的工具列表与hook matcher一致；不能暴露另一个未受控搜索/获取工具作为绕路。没有接入hook或其他执行前门控的客户端，只能标为未强制预算，不得作为严格等预算运行。

适配器接收真实stream-json时：

1. tool_use记录请求。
2. 通过`rejection_for(state, tool_use_id)`匹配hook中的拒绝事件，再用finish(status='not_dispatched')保存原返回，不登记dispatch。不能仅凭网页正文含拒绝标记就认定拦截。hook错误或权限拒绝依据对应客户端证据另存。
3. 真实工具结果才确认派发，失败也计一次。准许hook本身不是派发证据。
4. 结束前把临时预算账本原文作为client_note导入process.jsonl，再写run_end，随后清理临时文件。交付仍是process.jsonl和evaluation.json。
5. 核对实际派发次数与预算，保存偏离；不要用模型最后一句“用了几次”填计数。

账本计的是准许次数，是保守门控：若准许后又被其他权限检查阻止，此次名额不自动退回。它可能使实际派发少于上限，但不会超额。M8仍按实际派发统计；保留这种差异。不在缺少可信未派发证据时擅自退款。

WorkBuddy当前hook输入可能没有tool_use_id，所以账本保留会话、顺序、工具名及参数；重复参数是新的尝试，不按参数去重。优先用tool_use_id连接真实拒绝事件；若客户端确实未暴露ID，保留关联缺口，不按并发顺序猜测。

## 验证范围

单元测试覆盖并发8次上限、超额拒绝、搜索/获取独立预算、零预算和账本误用。本机WorkBuddy与DeepSeek-V4.1-Flash的零预算实际请求已验证PreToolUse明确拒绝，并返回同一tool_use_id；该集成验证不代表任何客户端或所有配置都会生效。实际客户端仍需检查PreToolUse是否生效；配置文件含hooks不等于客户端已经执行它。本次本机WorkBuddy集成验证的证据保存在项目实验目录，不上传私人运行材料。
