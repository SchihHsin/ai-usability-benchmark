# 全量实验进行中

本批次156个计划单元；采集未完成不得宣称全量完成。GLM、DeepSeek、Kimi各52次。3个5.6 Luna子代理分别调度；程序run_model.py按ledger跳过已核验成功项。旧18次试跑未并入本批次。

采集后按模型运行assess_model.py，统一GLM自动后评；后评需继续复核门禁失败，不等同于技术验证。每次两个评价。后评技术失败最多保留两次尝试，不能按评分择优。已有第一份GLM后评超时、第二份outcome ID结构错误，已保留，后续用显式ID schema和900秒超时。

完成采集后prepare_assessment.py按本批次runs生成assessment-input；consolidate_evaluations.py追加evaluation修订，不改process。后续须核对312份评价状态、逐项未完成原因及M11点值/区间。不能调用assess.py --export把门禁失败当拟合有效样本，本批次不拟合系数。

首条GLM/DeepSeek/Kimi采集实际成功但控制器读错evaluation层级，ledger保留原false并追加true修复记录，原始运行未重跑；controller-repair.json和各ledger可追溯。评分规则和协议未因此改变。

status.py生成status.json/progress.html。采集和评分完成数分别报告。git每轮仅提交本实验相关资料，不动论文。
