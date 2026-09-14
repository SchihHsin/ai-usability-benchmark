#!/usr/bin/env python3
"""Two-file evidence recorder; no tool interception or provider execution."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
try:
    from .legacy_run_log import now, read_json, safe_id, reject_credentials
except ImportError:
    from legacy_run_log import now, read_json, safe_id, reject_credentials

SCHEMA = "two-file-1"
DRAFT = "v2-draft"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack(data):
    try:
        payload = {"encoding": "utf-8", "content": data.decode("utf-8")}
    except UnicodeDecodeError:
        payload = {"encoding": "base64", "content": base64.b64encode(data).decode("ascii")}
    return {**payload, "bytes": len(data), "sha256": digest(data)}


def unpack(payload):
    if payload["encoding"] == "utf-8":
        data = payload["content"].encode("utf-8")
    elif payload["encoding"] == "base64":
        data = base64.b64decode(payload["content"], validate=True)
    else:
        raise ValueError("未知编码")
    if len(data) != payload["bytes"] or digest(data) != payload["sha256"]:
        raise ValueError("内容大小或哈希不符")
    return data


def events(directory):
    rows = [json.loads(line) for line in (directory / "process.jsonl").read_text(encoding="utf-8").splitlines()]
    if not rows or rows[0].get("type") != "run_start" or rows[0].get("schema_version") != SCHEMA:
        raise ValueError("缺少有效run_start")
    ids = set()
    for seq, row in enumerate(rows, 1):
        if row.get("seq") != seq or row.get("id") in ids:
            raise ValueError("事件序号或ID重复/不连续")
        ids.add(row["id"])
    return rows


def append(directory, row):
    rows = events(directory)
    if rows[-1]["type"] == "run_end":
        raise ValueError("运行已结束，过程禁止追加")
    if any(r["id"] == row["id"] for r in rows):
        raise ValueError("事件ID重复")
    reject_credentials(row)
    data = json.dumps({**row, "seq": len(rows) + 1, "recorded_at": now()}, ensure_ascii=False, allow_nan=False) + "\n"
    with (directory / "process.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def init_run(directory, metadata, question):
    for key in ("run_id", "task_id", "ecosystem", "model_id", "protocol_version", "rubric_version"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"metadata缺少{key}")
    if type(metadata.get("repetition")) is not int or metadata["repetition"] < 1:
        raise ValueError("repetition须为正整数")
    reject_credentials(metadata)
    body = question.read_bytes()
    if not body.strip():
        raise ValueError("问句不能为空")
    row = {"seq": 1, "id": "run-start", "type": "run_start", "schema_version": SCHEMA,
           "recorded_at": now(), "metadata": metadata, "question": pack(body)}
    encoded = json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n"
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "process.jsonl").write_text(encoded, encoding="utf-8")
    (directory / "evaluation.json").write_text(json.dumps({"schema_version": SCHEMA,
        "run_id": metadata["run_id"], "revisions": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def begin(directory, event_id, role, tool, request, parent=None):
    safe_id(event_id)
    rows = events(directory)
    if role not in {"search", "fetch", "other"} or not isinstance(request, dict) or not tool:
        raise ValueError("无效角色、工具或请求")
    if parent and not any(r["id"] == parent for r in rows):
        raise ValueError("父事件不存在")
    append(directory, {"id": event_id, "type": "tool_request", "role": role, "tool": tool,
                       "arguments": request, "parent_event_id": parent})


def request_state(directory, event_id):
    rows = events(directory)
    request = next((r for r in rows if r["id"] == event_id and r["type"] == "tool_request"), None)
    if request is None:
        raise ValueError("请求不存在")
    linked = [r for r in rows if r.get("request_id") == event_id]
    return rows, request, linked


def dispatch(directory, event_id):
    _, _, linked = request_state(directory, event_id)
    if linked:
        raise ValueError("请求已有派发或结果")
    append(directory, {"id": event_id + ".dispatch", "type": "tool_dispatch", "request_id": event_id})


def finish(directory, event_id, response, status, observation):
    _, _, linked = request_state(directory, event_id)
    if status not in {"ok", "error", "not_dispatched"} or not isinstance(observation, dict):
        raise ValueError("无效状态或observation")
    if any(r["type"] == "tool_result" for r in linked):
        raise ValueError("此请求已有返回，重试须新ID")
    dispatched = any(r["type"] == "tool_dispatch" for r in linked)
    if dispatched == (status == "not_dispatched"):
        raise ValueError("实际派发后才能保存ok/error；未派发使用not_dispatched")
    append(directory, {"id": event_id + ".result", "type": "tool_result", "request_id": event_id,
        "tool_status": status, "response": pack(response.read_bytes()), "observation": observation})


def report(directory, event_id, content, kind):
    if kind not in {"self_report", "client_note"}:
        raise ValueError("只保存显式自评或客户端事实说明，不保存隐藏推理")
    append(directory, {"id": safe_id(event_id), "type": kind, "content": pack(content.read_bytes())})


def end_run(directory, answer, reason):
    if not reason.strip():
        raise ValueError("须填写实际停止原因")
    append(directory, {"id": "run-end", "type": "run_end", "answer": pack(answer.read_bytes()), "stop_reason": reason})


def validate_evaluation(rows, value):
    if not isinstance(value, dict):
        raise ValueError("评价须为对象")
    reject_credentials(value)
    version = rows[0]["metadata"]["rubric_version"]
    if value.get("rubric_version") != version:
        raise ValueError("评价规则版本与运行不符")
    for field in ("requirements", "issues", "evidence", "metrics"):
        if not isinstance(value.get(field), list):
            raise ValueError(f"须提供{field}数组；未知使用空数组并填写limitations")
    if not isinstance(value.get("limitations"), list) or not value.get("assessor"):
        raise ValueError("须填写assessor与limitations")
    by_id = {r["id"]: r for r in rows}
    evidence = {}
    for ref in value["evidence"]:
        if ref["id"] in evidence:
            raise ValueError("证据ID重复")
        row = by_id.get(ref.get("event_id"))
        if row is None or ref.get("field") not in {"response", "answer", "question", "content"} or ref["field"] not in row:
            raise ValueError("证据事件/内容字段不存在")
        payload = row[ref["field"]]
        if ref.get("sha256") != payload["sha256"]:
            raise ValueError("证据哈希不符")
        text = unpack(payload).decode("utf-8")
        start, end = ref.get("start"), ref.get("end")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise ValueError("证据字符区间无效")
        if text[start:end] != ref.get("quote"):
            raise ValueError("证据引文与字符区间不符")
        evidence[ref["id"]] = ref
    def walk(node):
        if isinstance(node, dict):
            for key, item in node.items():
                if key == "evidence_refs" and (not isinstance(item, list) or any(r not in evidence for r in item)):
                    raise ValueError("证据引用不存在")
                if key == "event_refs" and (not isinstance(item, list) or any(r not in by_id for r in item)):
                    raise ValueError("事件引用不存在")
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(value)
    if version == DRAFT:
        if value.get("overall") is not None or any(m.get("score") is not None for m in value["metrics"]):
            raise ValueError("v2-draft尚未定稿，禁止输出正式分值或套用旧综合公式")


def save_evaluation(directory, value):
    rows = events(directory)
    if rows[-1]["type"] != "run_end":
        raise ValueError("先结束运行，再保存评价")
    validate_evaluation(rows, value)
    target = directory / "evaluation.json"
    saved = read_json(target)
    saved["revisions"].append({"revision": len(saved["revisions"]) + 1, "recorded_at": now(),
        "process_sha256": digest((directory / "process.jsonl").read_bytes()), "evaluation": value})
    # One writer per run. Atomic replacement; old revisions remain inside this file.
    temporary = target.with_suffix(".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(saved, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(target)


def check(directory):
    rows = events(directory)
    issues = []
    for row in rows:
        for field in ("question", "response", "answer", "content"):
            if field in row:
                try:
                    unpack(row[field])
                except (ValueError, KeyError) as error:
                    issues.append(f'{row["id"]}: {error}')
    counts = {state: {role: 0 for role in ("search", "fetch", "other")} for state in ("requested", "dispatched", "returned", "not_dispatched")}
    for request in (r for r in rows if r["type"] == "tool_request"):
        linked = [r for r in rows if r.get("request_id") == request["id"]]
        role = request["role"]
        counts["requested"][role] += 1
        dispatched = any(r["type"] == "tool_dispatch" for r in linked)
        result = next((r for r in linked if r["type"] == "tool_result"), None)
        counts["dispatched"][role] += int(dispatched)
        if result:
            counts["not_dispatched" if result["tool_status"] == "not_dispatched" else "returned"][role] += 1
        else:
            issues.append(f'{request["id"]}: 未保存返回，派发状态={dispatched}')
    if rows[-1]["type"] != "run_end":
        issues.append("未保存最终回答及停止原因")
    evaluation = read_json(directory / "evaluation.json")
    if evaluation.get("run_id") != rows[0]["metadata"]["run_id"]:
        issues.append("评价run_id不符")
    if not evaluation["revisions"]:
        issues.append("尚未评价")
    for revision in evaluation["revisions"]:
        if revision["process_sha256"] != digest((directory / "process.jsonl").read_bytes()):
            issues.append("评价与过程哈希不符")
        try:
            validate_evaluation(rows, revision["evaluation"])
        except (ValueError, KeyError) as error:
            issues.append(f"评价: {error}")
    return {"run_id": rows[0]["metadata"]["run_id"], "issues": issues, "counts": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "begin", "dispatch", "finish", "end", "report", "evaluate", "check"):
        p = subs.add_parser(command)
        p.add_argument("--run-dir", type=Path, required=True)
        if command == "init":
            p.add_argument("--metadata", type=Path, required=True)
            p.add_argument("--question", type=Path, required=True)
        if command in {"begin", "dispatch", "finish"}:
            p.add_argument("--event-id", required=True)
        if command == "begin":
            p.add_argument("--role", choices=["search", "fetch", "other"], required=True)
            p.add_argument("--tool", required=True)
            p.add_argument("--request", type=Path, required=True)
            p.add_argument("--parent")
        if command == "finish":
            p.add_argument("--response", type=Path, required=True)
            p.add_argument("--status", choices=["ok", "error", "not_dispatched"], required=True)
            p.add_argument("--observation", type=Path)
        if command == "report":
            p.add_argument("--event-id", required=True)
            p.add_argument("--content", type=Path, required=True)
            p.add_argument("--kind", choices=["self_report", "client_note"], required=True)
        if command == "end":
            p.add_argument("--answer", type=Path, required=True)
            p.add_argument("--reason", required=True)
        if command == "evaluate":
            p.add_argument("--input", type=Path, required=True)
    a = parser.parse_args()
    try:
        if a.command == "init": init_run(a.run_dir, read_json(a.metadata), a.question)
        elif a.command == "begin": begin(a.run_dir, a.event_id, a.role, a.tool, read_json(a.request), a.parent)
        elif a.command == "dispatch": dispatch(a.run_dir, a.event_id)
        elif a.command == "finish": finish(a.run_dir, a.event_id, a.response, a.status, read_json(a.observation) if a.observation else {})
        elif a.command == "report": report(a.run_dir, a.event_id, a.content, a.kind)
        elif a.command == "end": end_run(a.run_dir, a.answer, a.reason)
        elif a.command == "evaluate": save_evaluation(a.run_dir, read_json(a.input))
        else:
            result = check(a.run_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return bool(result["issues"])
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
