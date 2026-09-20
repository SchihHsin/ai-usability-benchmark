#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_template.py — 「AI 可用性」11 项指标的量化打分管线（可分享模板）
======================================================================

这是一份**通用模板**：衡量「当一个会检索的 AI 助手回答某开发任务时，
能否把一份正确、具体、可锁版本、可复现的答案搬进回复，以及花多大力气」。
默认对照 = 基线生态 baseline（如 CUDA）vs 受测生态 target（如 CANN）；
你也可以换成任意两个生态（ROCm / TPU / 任何栈）。

把每个任务在两个生态各实测检索一遍（web_search/web_fetch），按统一指标打分。
每个指标一个 score_N() 函数，输入是实测检索得到的**可量化原始观测**，输出 1–5
（⑧反向；⑪由①–⑧噪声-OR汇总）。

运行：  python3 score_template.py          # 打印全矩阵
       python3 score_template.py --json   # 输出 JSON（供前端落库）

‼ 铁律：RAW 里的数字必须来自**实测检索记录**，绝不为凑分而编。来源标题/URL/
   日期/版本号无把握 → 重新检索拿到再写；拿不到的日期留 None、不杜撰。

设计原则
--------
1. 原始数据只来自实测检索记录；绝不编造。
2. 凡天然是判断的输入（⑦自带知识、⑥一致性档），用显式子档表量化、注明是自评。
3. ⑨⑩是产出/因变量，照打分但**不进⑪**（进了=重复加权）。
4. 受阻（官方页 SPA 抓不到正文）记 BLOCKED，归一时按 0，且**不等于给③打1分**。
"""

import sys, json, argparse, re, hashlib
from pathlib import Path

RUBRIC_VERSION = "2026-09-14"
NO_SOURCES = "无来源"
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
# 旧API/演示保留默认月；正式--input必须--as-of，显式传参给M6。日期None=未取得。
TODAY = (2026, 6)

def parse_month(ym):
    if not isinstance(ym, str) or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", ym):
        raise ValueError("日期必须为 YYYY-MM")
    return int(ym[:4]), int(ym[5:7])

def _age_months(ym, today=TODAY):
    y, m = parse_month(ym)
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
# 1. 原始观测数据（每格 = 一个任务×一个生态；字段全部来自实测检索记录）
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
#    跑你自己的任务时，请整组替换为实测检索得到的观测。
# ============================================================
RAW = {
    # —— 示例任务：模型转换 / 导出（baseline=CUDA 走 TensorRT；target=CANN 走 ATC）——
    "EXAMPLE": {
        # baseline（默认 = CUDA）：静态官方站、正文穷尽、版本可锁
        "baseline": dict(
            rounds=1, rank=1, refine=False, fetch=1, fetch_fail=0,
            core_fetch="static", exec=True, ref_level="exhaustive",
            n_versions=1, ver_matrix=False, ver_irrelev=False, two_axis=False,
            sources=["tech_blog", "tech_blog", "qa_reputation"],
            platforms=["tutorial.example.com", "blog.example.net", "qa.example.org"],
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
    return {"static":5, "ssr":4, "partial":3, "spa":2, "robots":1}[r["core_fetch"]]

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

def score6_sec_cred(r, today=TODAY):
    """⑥ 二手可信度/一致性 = 来源可信度均分 + 一致性因子 + 时效罚分 + 独立性罚分，clamp 1..5。"""
    if r["sources"] == []:
        return NO_SOURCES
    creds = [SOURCE_CRED[s] for s in r["sources"]]
    mean = sum(creds) / len(creds)
    val = (mean + CONSIST[r["consist"]]
           + recency_factor(r.get("dates", []), today=today)
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
    """归一：1–5 → 0.2–1.0；受阻/已确认无来源 → 0，未知不能归零。"""
    return 0.0 if v in (BLK, NO_SOURCES) else v / 5.0

def score11_overall(s):
    """s = 已算出的 ①–⑩ 分列表。返回 (综合分, 档位, 中间量)。"""
    OFF = nm(s[0]) * nm(s[1]) * nm(s[2])     # 官方：发现×抓取×详尽
    SEC = nm(s[4]) * nm(s[5])                # 二手：数量×可信
    OWN = nm(s[6])                           # 自带知识
    K = 1 - (1 - OFF) * (1 - SEC) * (1 - OWN)
    vf = 0.7 + 0.3 * nm(s[3])                # 版本因子（正常输入为0.76–1）
    cf = 0.9 + 0.1 * nm(s[7])                # 成本因子（正常输入为0.92–1）
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

def compute(today=TODAY):
    out = {}
    for t in TASKS:
        out[t] = {}
        for st in STACKS:
            r = RAW[t][st]
            s = [f(r, today=today) if f is score6_sec_cred else f(r) for f in METRICS]
            score, band, mid = score11_overall(s)
            out[t][st] = dict(scores=s, overall=round(score, 3),
                              band=band[0], mid=mid)
    return out

def fmt(v):
    return str(v).rjust(4)

# JSON observations are separate from this script; each model uses the same code.
REQUIRED = [
    ("rounds", "rank", "refine"), ("core_fetch",),
    ("core_fetch", "exec", "ref_level"),
    ("n_versions", "ver_matrix", "ver_irrelev", "two_axis"),
    ("sources",), ("sources", "platforms", "dates", "consist"),
    ("own", "churn"), ("rounds", "fetch", "fetch_fail"), ("pin",), ("repro",),
]
ENUMS = {
    "core_fetch": {"static", "ssr", "partial", "spa", "robots"},
    "ref_level": {"exhaustive", "core_only", "overview", "fragment", "none"},
    "consist": set(CONSIST), "churn": set(CHURN),
    "pin": {"exact", "mostly", "range", "none"},
    "repro": {"copyrun", "params", "partial", "skeleton"},
    "body_status": {"retrieved", "partial", "not_retrieved"},
}
BOOLS = {"refine", "exec", "ver_matrix", "ver_irrelev", "two_axis"}
COUNTS = {"rounds", "rank", "fetch", "fetch_fail", "n_versions", "own"}


def validate_raw(raw, today):
    if not isinstance(raw, dict):
        raise ValueError("raw必须是对象")
    for key, value in raw.items():
        if value is None:
            continue
        if key in BOOLS and type(value) is not bool:
            raise ValueError(f"{key}必须是布尔或null")
        if key in COUNTS and (type(value) is not int or value < (1 if key in {"rank", "own"} else 0)):
            raise ValueError(f"{key}必须是合法整数或null")
        if key == "own" and value > 5:
            raise ValueError("own必须在1–5之间")
        if key in ENUMS and value not in ENUMS[key]:
            raise ValueError(f"{key}的枚举值无效；未知请使用null")
    if raw.get("fetch") is not None and raw.get("fetch_fail") is not None and raw["fetch_fail"] > raw["fetch"]:
        raise ValueError("失败获取次数不能超过全部获取次数")
    if raw.get("n_versions") == 0 and raw.get("ver_irrelev") is not True:
        raise ValueError("版本敏感任务未确定版本时用null，不能用0获得高分")
    if raw.get("rank") is not None and raw.get("rounds") == 0:
        raise ValueError("零次搜索不能声称观察到搜索排名")
    if raw.get("body_status") in {"retrieved", "partial"} and raw.get("core_fetch") in {"spa", "robots"}:
        raise ValueError("正文取得状态与core_fetch受阻状态冲突")
    if raw.get("body_status") == "not_retrieved" and raw.get("core_fetch") in {"static", "ssr", "partial"}:
        raise ValueError("正文未取得与core_fetch取得状态冲突")
    for key in ("sources", "platforms", "dates"):
        if raw.get(key) is not None and not isinstance(raw[key], list):
            raise ValueError(f"{key}必须是列表或null")
    sources = raw.get("sources")
    if sources is not None:
        for source in sources:
            if not isinstance(source, str) or source not in SOURCE_CRED:
                raise ValueError("未知来源类型")
            if source.startswith("official_"):
                raise ValueError("官方来源不能计入第三方sources")
        for key in ("platforms", "dates"):
            if raw.get(key) is not None and len(raw[key]) != len(sources):
                raise ValueError(f"{key}必须与sources一一对应")
    if raw.get("platforms") is not None and any(not isinstance(x, str) or not x.strip() for x in raw["platforms"]):
        raise ValueError("platforms成员必须是非空域名；未知时整字段用null")
    for date in raw.get("dates") or []:
        if date is not None and parse_month(date) > today:
            raise ValueError("来源日期晚于统一参照月，请核对；不要推算为负月龄")


def score_record(raw, today, evidence_refs=None):
    """Score one run; unknown inputs remain null, not low scores. No network calls."""
    validate_raw(raw, today)
    if evidence_refs is not None and not isinstance(evidence_refs, dict):
        raise ValueError("evidence_refs必须是字段到证据ID列表的映射")
    values, states, issues = [], [], {}
    for i, function in enumerate(METRICS):
        required = REQUIRED[i]
        blocked = raw.get("core_fetch") in {"spa", "robots"} or raw.get("body_status") == "not_retrieved"
        if i == 2:
            if blocked:
                required = ("core_fetch",) if raw.get("core_fetch") in {"spa", "robots"} else ("body_status",)
            elif raw.get("body_status") in {"retrieved", "partial"}:
                required = ("body_status", "exec", "ref_level")
        if i == 3 and raw.get("ver_irrelev") is True:
            required = ("ver_irrelev",)
        if i == 5 and raw.get("sources") == []:
            required = ("sources",)
        missing = [key for key in required if raw.get(key) is None]
        unsupported = [] if evidence_refs is None else [
            key for key in required if not isinstance(evidence_refs.get(key), list)
            or not evidence_refs[key] or not all(isinstance(x, str) and x.strip() for x in evidence_refs[key])
        ]
        if missing or unsupported:
            values.append(None)
            states.append("missing" if missing else "unverified")
            issues[f"M{i+1}"] = {"missing_fields": missing, "fields_without_evidence": unsupported}
            continue
        if i == 2 and blocked:
            value = BLK
        elif i == 2 and raw.get("core_fetch") is None:
            # Retrieved content can be assessed without guessing static vs SSR.
            value = score3_detail({**raw, "core_fetch": None})
        elif i == 3 and raw.get("ver_irrelev") is True:
            value = 5
        else:
            value = function(raw, today=today) if i == 5 else function(raw)
        values.append(value)
        states.append("blocked" if value == BLK else "no_sources" if value == NO_SOURCES else "scored")
    overall = band = mid = None
    if all(value is not None for value in values[:8]):
        overall, band_pair, mid = score11_overall(values)
        band = band_pair[0]
    return dict(scores=values, metric_status=states,
                overall=None if overall is None else round(overall, 3),
                overall_exact=overall, band=band, mid=mid, issues=issues,
                rubric_version=RUBRIC_VERSION,
                score_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                reference_month=f"{today[0]:04d}-{today[1]:02d}")


def read_records(path):
    text = path.read_text(encoding="utf-8")
    records = ([json.loads(line) for line in text.splitlines() if line.strip()]
               if path.suffix == ".jsonl" else json.loads(text))
    if not isinstance(records, list) or not records:
        raise ValueError("输入必须是非空JSON记录列表或JSONL")
    return records


def score_records(records, today):
    result, seen = [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("每条运行必须是对象")
        identity = ("run_id", "task_id", "ecosystem", "model_id", "protocol_version", "rubric_version")
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in identity):
            raise ValueError("每条运行必须包含非空身份字段：" + ", ".join(identity))
        if record["rubric_version"] != RUBRIC_VERSION:
            raise ValueError("输入rubric_version与当前脚本不同，禁止静默重算旧规则")
        if type(record.get("repetition")) is not int or record["repetition"] < 1:
            raise ValueError("repetition必须是正整数")
        if record["run_id"] in seen:
            raise ValueError("重复run_id，不得覆盖或静默去重")
        seen.add(record["run_id"])
        if record.get("reference_month") not in (None, f"{today[0]:04d}-{today[1]:02d}"):
            raise ValueError("输入参照月与命令行不一致")
        scored = score_record(record.get("raw"), today, record.get("evidence_refs", {}))
        result.append({**{k: record[k] for k in identity}, "repetition": record["repetition"], **scored})
    if len({r["protocol_version"] for r in result}) > 1:
        raise ValueError("同一计分批次不可混用protocol_version")
    return result


def main():
    parser = argparse.ArgumentParser(description="统一计分；不调用模型、不执行检索")
    parser.add_argument("--input", type=Path, help="多模型JSON/JSONL观测；无输入仅演示")
    parser.add_argument("--as-of", help="统一参照月YYYY-MM，真实输入必须显式指定")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.input:
            if not args.as_of:
                parser.error("真实观测必须指定 --as-of YYYY-MM")
            data = score_records(read_records(args.input), parse_month(args.as_of))
        else:
            data = compute(parse_month(args.as_of) if args.as_of else TODAY)
    except (ValueError, TypeError, OSError) as error:
        parser.error(str(error))
    if args.json or args.input:
        print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
        return
    print("示例数据（非实测）；M1–M10为1–5，M11为0–1。")
    for task, sides in data.items():
        for side, value in sides.items():
            print(task, STACK_LABEL.get(side, side), value["scores"], value["overall"], value["band"])


if __name__ == "__main__":
    main()
