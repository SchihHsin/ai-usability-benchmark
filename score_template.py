#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_template.py — 「AI 可用性」11 项指标的量化打分管线（可分享模板）
======================================================================

这是一份**通用模板**：衡量「当一个会检索的 AI 助手回答某开发任务时，
能否把一份正确、具体、可锁版本、可复现的答案搬进回复，以及花多大力气」。
默认对照 = 基线生态 baseline（如 CUDA）vs 受测生态 target（如 CANN）；
你也可以换成任意两个生态（ROCm / TPU / 任何栈）。

把每个任务在两个生态各真跑一遍检索（web_search/web_fetch），按统一指标打分。
每个指标一个 score_N() 函数，输入是真跑得到的**可量化原始观测**，输出 1–5
（⑧反向；⑪由①–⑧噪声-OR汇总）。

运行：  python3 score_template.py          # 打印全矩阵
       python3 score_template.py --json   # 输出 JSON（供前端落库）

‼ 铁律：RAW 里的数字必须来自**真跑记录**，绝不为凑分而编。来源标题/URL/
   日期/版本号无把握 → 重新检索拿到再写；拿不到的日期留 None、不杜撰。

设计原则
--------
1. 原始数据只来自真跑记录；绝不编造。
2. 凡天然是判断的输入（⑦自带知识、⑥一致性档），用显式子档表量化、注明是自评。
3. ⑨⑩是产出/因变量，照打分但**不进⑪**（进了=重复加权）。
4. 受阻（官方页 SPA 抓不到正文）记 BLOCKED，归一时按 0，且**不等于给③打1分**。
"""

import sys, json

BLK = "受阻"   # 受阻态（③ 在官方 SPA 抓不到正文时）

# ============================================================
# 0. 二手来源可信度评分表（回答「每条来源可信度多少、怎么算」）
#    按来源**类型**定基准分；这是一张可复核的锚定表，不是逐条拍脑袋。
# ============================================================
SOURCE_CRED = {
    "official_doc":   5.0,  # 一手官方文档镜像
    "official_repo":  5.0,  # 官方代码仓
    "official_forum": 4.5,  # 官方论坛/邮件列表
    "cloud_vendor":   4.0,  # 大厂云技术博客
    "arxiv":          4.0,  # 学术论文
    "qa_reputation":  3.5,  # 有声誉的问答/专栏（如 StackOverflow、知乎专栏）
    "tech_blog":      3.0,  # 个人技术博客（CSDN / 博客园 / Medium）
    "aggregator":     2.5,  # 聚合站/科普号/转载
}
# 一致性因子：各源对「命令/版本/写法」是否对得上。high=互证、mid=深度参差、low=彼此矛盾
CONSIST = {"high": +1.0, "mid": 0.0, "low": -1.0}

# 时效性（recency）—— ⑥ 的「只罚不奖」修正项（够新是基线、过时才扣）。
# today 固定为某个参照月，便于复算；各源真实发表日期由 web_search 实测，None=未拿到。
TODAY = (2026, 6)

def _age_months(ym, today=TODAY):
    y, m = int(ym[:4]), int(ym[5:7])
    return (today[0] - y) * 12 + (today[1] - m)

def recency_factor(dates, today=TODAY):
    """二手来源发表日期中位月龄 → ⑥ 罚分。≤36mo 不罚、≤48mo −0.25、>48mo −0.5。"""
    ages = sorted(_age_months(d, today) for d in dates if d)
    if not ages:
        return 0.0
    n = len(ages)
    med = ages[n // 2] if n % 2 else (ages[n // 2 - 1] + ages[n // 2]) / 2
    if med <= 36:  return 0.0
    if med <= 48:  return -0.25
    return -0.5

def independence_factor(platforms):
    """来源独立性（因子B）：去重平台域名数/来源总数=indep。
       indep≥0.8 不罚 / ≥0.6 −0.25 / <0.6 −0.5（治「同平台互抄回声」）。"""
    if not platforms:
        return 0.0
    indep = len(set(platforms)) / len(platforms)
    if indep >= 0.8:  return 0.0
    if indep >= 0.6:  return -0.25
    return -0.5

# 因子 A：知识截止 gap —— ⑦ 的「只罚不奖」修正项。
# 技术迭代越快，模型训练知识越可能落后于最新版本。
CHURN = {"stable": 0.0, "moderate": -0.25, "fast": -0.5}

def cutoff_gap_factor(churn):
    return CHURN[churn]


# ============================================================
# 1. 原始观测数据（每格 = 一个任务×一个生态；字段全部来自真跑记录）
# ------------------------------------------------------------
# 字段说明：
#  rounds        检索轮数（web_search 次数）
#  rank          首条官方结果在 SERP 的大致名次（1=首条；越大越靠后）
#  refine        是否需要换关键词二次检索才浮出官方源
#  fetch         web_fetch 次数
#  fetch_fail    web_fetch 抓取失败次数（SPA 抓空）
#  core_fetch    核心 how-to 页抓取形态：static/ssr/partial/spa/robots
#  exec          官方正文是否含可执行核心（命令或可跑代码）
#  ref_level     正文参考完整度：exhaustive / core_only / overview / fragment / none
#  n_versions    检索中并存的版本号个数（去重）
#  ver_matrix    官方是否给出清晰支持矩阵
#  ver_irrelev   该任务是否本质与版本无关（选型类）
#  two_axis      是否需同时定两轴（如芯片+框架）但可锁
#  sources       二手来源类型列表（用 SOURCE_CRED 的键；官方渠道不算二手！）
#  platforms     每条二手来源的平台/域名 token（与 sources 一一对应，判独立性）
#  dates         每条二手来源发表日期 'YYYY-MM'，拿不到记 None
#  consist       二手一致性：high / mid / low
#  own           ⑦ 模型自带知识自评 1–5（唯一显式自评，注明无法外部量测）
#  churn         相关工具迭代节奏：stable / moderate / fast
#  pin           ⑨ 版本可锁定性：exact / mostly / range / none
#  repro         ⑩ 步骤可复现性：copyrun / params / partial / skeleton
#
# ⚠ 下面是【示例数据】，仅用于让脚本能跑通并演示输出格式。
#    跑你自己的任务时，请整组替换为真跑得到的观测。
# ============================================================
RAW = {
    # —— 示例任务：模型转换 / 导出（baseline=CUDA 走 TensorRT；target=CANN 走 ATC）——
    "EXAMPLE": {
        # baseline（默认 = CUDA）：静态官方站、正文穷尽、版本可锁
        "baseline": dict(
            rounds=1, rank=1, refine=False, fetch=1, fetch_fail=0,
            core_fetch="static", exec=True, ref_level="exhaustive",
            n_versions=1, ver_matrix=False, ver_irrelev=False, two_axis=False,
            sources=["official_doc", "tech_blog", "qa_reputation"],
            platforms=["docs.example.com", "blog.example.net", "qa.example.org"],
            dates=["2025-06", "2024-09", None], consist="high",
            own=4, churn="stable", pin="exact", repro="copyrun",
        ),
        # target（默认 = CANN）：官方部分可抓、二手偏薄、多版本并存
        "target": dict(
            rounds=2, rank=2, refine=False, fetch=2, fetch_fail=0,
            core_fetch="ssr", exec=True, ref_level="core_only",
            n_versions=3, ver_matrix=False, ver_irrelev=False, two_axis=False,
            sources=["tech_blog", "tech_blog", "cloud_vendor"],
            platforms=["csdn.net", "csdn.net", "cloud.example.com"],
            dates=["2025-05", "2024-11", "2025-01"], consist="mid",
            own=3, churn="moderate", pin="mostly", repro="params",
        ),
    },
}

# 默认两个生态的显示名（用户若指定别的，改这里 + RAW 里的键）
STACKS = ["baseline", "target"]
STACK_LABEL = {"baseline": "CUDA", "target": "CANN"}


# ============================================================
# 2. 各指标公式（① 越大越好；⑧ 反向：越省越高）
# ============================================================
def score1_discover(r):
    """① 官方可发现性 = f(命中排名, 轮数, 是否需二次检索)。"""
    if r["rounds"] >= 2 and r["refine"]:
        return 2
    if r["rounds"] >= 2:
        return 3
    rk = r["rank"]
    if rk == 1:  return 5
    if rk <= 3:  return 4
    if rk <= 6:  return 4
    if rk <= 10: return 3
    return 2

def score2_fetch(r):
    """② 官方可抓取性 = 核心 how-to 页抓取形态映射。"""
    return {"static":5, "ssr":4, "partial":4, "spa":2, "robots":1}[r["core_fetch"]]

def score3_detail(r):
    """③ 官方正文详尽度。② 为 SPA/robots（抓不到正文）→ 受阻中性态。"""
    if r["core_fetch"] in ("spa", "robots"):
        return BLK
    exec_ok = bool(r["exec"])
    ref = r["ref_level"]
    if ref == "exhaustive":  return 5 if exec_ok else 4
    if ref == "core_only":   return 4 if exec_ok else 3
    if ref == "overview":    return 3
    if ref == "fragment":    return 2
    return 1

def score4_version(r):
    """④ 版本清晰度 = f(并存版本数, 支持矩阵, 是否版本无关/双轴)。"""
    if r["ver_irrelev"]:     return 5
    if r["n_versions"] <= 1: return 5
    if r["ver_matrix"]:      return 4
    if r["two_axis"]:        return 3
    if r["n_versions"] >= 3: return 2
    return 3

def score5_sec_qty(r):
    """⑤ 二手丰富度 = 去重二手来源条数分档。"""
    n = len(r["sources"])
    if n >= 6: return 5
    if n >= 5: return 4
    if n >= 3: return 3
    if n >= 1: return 2
    return 1

def score6_sec_cred(r):
    """⑥ 二手可信度/一致性 = 来源可信度均分 + 一致性因子 + 时效罚分 + 独立性罚分，clamp 1..5。"""
    creds = [SOURCE_CRED[s] for s in r["sources"]]
    mean = sum(creds) / len(creds)
    val = (mean + CONSIST[r["consist"]]
           + recency_factor(r.get("dates", []))
           + independence_factor(r.get("platforms", [])))
    return max(1, min(5, round(val)))

def score7_own(r):
    """⑦ 模型自带知识 = 自评档 own + 知识截止 gap 罚分（因子 A），clamp 1..5。"""
    val = r["own"] + cutoff_gap_factor(r.get("churn", "stable"))
    return max(1, min(5, round(val)))

def score8_cost(r):
    """⑧ 检索成本（反向，越省越高）= f(轮数, 抓取次数, 抓取失败惩罚)。"""
    cost = r["rounds"] + 0.5 * r["fetch"] + 4.0 * r["fetch_fail"]
    if cost <= 1.5: return 5
    if cost <= 2.5: return 4
    if cost <= 4.0: return 3
    if cost <= 6.0: return 2
    return 1

def score9_pin(r):
    """⑨ 版本可锁定性（产出/因变量，不进⑪）。"""
    return {"exact":5, "mostly":4, "range":3, "none":2}[r["pin"]]

def score10_repro(r):
    """⑩ 步骤可复现性（产出/因变量，不进⑪）。"""
    return {"copyrun":5, "params":4, "partial":3, "skeleton":2}[r["repro"]]


# ============================================================
# 3. ⑪ 综合置信度 = 三源噪声-OR（OFF/SEC/OWN 任一扛住即可答）
# ============================================================
def nm(v):
    """归一：1–5 → 0.2–1.0；受阻 → 0。"""
    return 0.0 if v == BLK else v / 5.0

def score11_overall(s):
    """s = 已算出的 ①–⑩ 分列表。返回 (综合分, 档位, 中间量)。"""
    OFF = nm(s[0]) * nm(s[1]) * nm(s[2])     # 官方：发现×抓取×详尽
    SEC = nm(s[4]) * nm(s[5])                # 二手：数量×可信
    OWN = nm(s[6])                           # 自带知识
    K = 1 - (1 - OFF) * (1 - SEC) * (1 - OWN)
    vf = 0.7 + 0.3 * nm(s[3])                # 版本因子（跨渠道 ±30%）
    cf = 0.9 + 0.1 * nm(s[7])                # 成本因子（±10%）
    score = K * vf * cf
    band = ("高",5) if score>=0.80 else ("中高",4) if score>=0.63 else \
           ("中",3) if score>=0.45 else ("低",2) if score>=0.24 else ("很低",1)
    return score, band, dict(OFF=OFF,SEC=SEC,OWN=OWN,K=K,vf=vf,cf=cf)


# ============================================================
# 4. 跑全矩阵
# ============================================================
METRICS = [score1_discover, score2_fetch, score3_detail, score4_version,
           score5_sec_qty, score6_sec_cred, score7_own, score8_cost,
           score9_pin, score10_repro]
LABELS = ["①发现","②抓取","③详尽","④版本清","⑤二手量","⑥二手信",
          "⑦自带","⑧成本","⑨版本锁","⑩复现","⑪综合"]

TASKS = list(RAW.keys())

def compute():
    out = {}
    for t in TASKS:
        out[t] = {}
        for st in STACKS:
            r = RAW[t][st]
            s = [f(r) for f in METRICS]
            score, band, mid = score11_overall(s)
            out[t][st] = dict(scores=s, overall=round(score, 3),
                              band=band[0], mid=mid)
    return out

def fmt(v):
    return str(v).rjust(4)

def main():
    data = compute()
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("AI 可用性矩阵（① 越大越好；⑧ 反向；⑪=三源噪声-OR 综合）\n")
    head = "任务".ljust(10) + "生态".ljust(8) + "".join(l.rjust(6) for l in LABELS)
    print(head)
    print("-" * len(head))
    for t in TASKS:
        for st in STACKS:
            d = data[t][st]
            row = (t.ljust(10) + STACK_LABEL.get(st, st).ljust(8)
                   + "".join(fmt(x) + "  " for x in d["scores"])
                   + fmt(d["overall"]) + f"  ({d['band']})")
            print(row)
        print()

if __name__ == "__main__":
    main()
