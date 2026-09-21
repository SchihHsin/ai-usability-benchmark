#!/usr/bin/env python3
"""Local evidence recorder. Does not call providers, scrape pages or reconstruct logs."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def safe_id(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", value):
        raise ValueError("event-id须为字母数字开头的短ID，不能包含路径")
    return value


def reject_credentials(value):
    # A guard on structured keys, not a complete redaction system.
    # The caller must also strip credentials in URLs/free text before recording.
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in {"authorization", "proxy_authorization", "cookie", "set_cookie", "api_key", "apikey", "access_token", "refresh_token", "password"}:
                raise ValueError(f"请先移除凭证字段：{key}")
            reject_credentials(item)
    elif isinstance(value, list):
        for item in value:
            reject_credentials(item)


def init_run(directory, metadata, question):
    if not isinstance(metadata, dict):
        raise ValueError("metadata须为对象")
    for key in ("run_id", "task_id", "ecosystem", "model_id", "protocol_version", "rubric_version"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"metadata缺少{key}")
    if type(metadata.get("repetition")) is not int or metadata["repetition"] < 1:
        raise ValueError("metadata缺少正整数repetition")
    reject_credentials(metadata)
    question_bytes = question.read_bytes()
    if not question_bytes.strip():
        raise ValueError("问句不能为空")
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "events").mkdir()
    write_new(directory / "metadata.json", {**metadata, "logger_created_at": now(),
              "question_sha256": hashlib.sha256(question_bytes).hexdigest()})
    (directory / "question.txt").write_bytes(question_bytes)


def begin(directory, event_id, role, tool, request, parent=None):
    read_json(directory / "metadata.json")
    if not isinstance(request, dict):
        raise ValueError("请求参数须为JSON对象")
    reject_credentials(request)
    event_id = safe_id(event_id)
    if parent:
        parent = safe_id(parent)
        if not (directory / "events" / parent / "request.json").is_file():
            raise ValueError("父事件不存在")
    folder = directory / "events" / event_id
    folder.mkdir(exist_ok=False)
    write_new(folder / "request.json", {"event_id": event_id, "role": role,
              "tool": tool, "parent_event_id": parent, "recorded_start_at": now(), "arguments": request})


def finish(directory, event_id, response, status, observation):
    folder = directory / "events" / safe_id(event_id)
    read_json(folder / "request.json")
    if (folder / "result.json").exists() or (folder / "response.bin").exists():
        raise ValueError("此事件已有返回，禁止覆盖；重试请建立新事件")
    if not isinstance(observation, dict):
        raise ValueError("observation须为JSON对象")
    reject_credentials(observation)
    body = response.read_bytes()
    (folder / "response.bin").write_bytes(body)
    write_new(folder / "result.json", {"event_id": event_id, "recorded_end_at": now(),
              "tool_status": status, "response_file": "response.bin", "bytes": len(body),
              "sha256": hashlib.sha256(body).hexdigest(), "observation": observation})


def check(directory):
    metadata = read_json(directory / "metadata.json")
    issues, events = [], []
    question = directory / "question.txt"
    if not question.exists() or hashlib.sha256(question.read_bytes()).hexdigest() != metadata["question_sha256"]:
        issues.append("question.txt缺失或哈希不符")
    for folder in sorted((directory / "events").iterdir()):
        request = read_json(folder / "request.json")
        result_path = folder / "result.json"
        result = read_json(result_path) if result_path.exists() else None
        if result is None:
            issues.append(f"{folder.name}: 未保存返回（可能中断）")
        else:
            body = folder / "response.bin"
            if not body.exists() or hashlib.sha256(body.read_bytes()).hexdigest() != result["sha256"]:
                issues.append(f"{folder.name}: 返回缺失或哈希不符")
        events.append({"request": request, "result": result})
    answer = directory / "answer.md"
    if not answer.exists() or not answer.read_bytes().strip():
        issues.append("answer.md缺失或为空")
    if not events:
        issues.append("尚无工具事件")
    events.sort(key=lambda event: event["request"]["recorded_start_at"])
    # Fetch failures need an acquisition outcome, not just HTTP/tool status.
    return {"run_id": metadata["run_id"], "issues": issues,
            "calls": {role: sum(e["request"]["role"] == role for e in events)
                      for role in ("search", "fetch", "other")}, "events": events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--run-dir", type=Path, required=True)
    init.add_argument("--metadata", type=Path, required=True)
    init.add_argument("--question", type=Path, required=True)
    start = sub.add_parser("begin")
    start.add_argument("--run-dir", type=Path, required=True)
    start.add_argument("--event-id", required=True)
    start.add_argument("--role", choices=["search", "fetch", "other"], required=True)
    start.add_argument("--tool", required=True)
    start.add_argument("--request", type=Path, required=True)
    start.add_argument("--parent")
    end = sub.add_parser("finish")
    end.add_argument("--run-dir", type=Path, required=True)
    end.add_argument("--event-id", required=True)
    end.add_argument("--response", type=Path, required=True)
    end.add_argument("--status", choices=["ok", "error"], required=True)
    end.add_argument("--observation", type=Path)
    verify = sub.add_parser("check")
    verify.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_run(args.run_dir, read_json(args.metadata), args.question)
        elif args.command == "begin":
            begin(args.run_dir, args.event_id, args.role, args.tool, read_json(args.request), args.parent)
        elif args.command == "finish":
            finish(args.run_dir, args.event_id, args.response, args.status,
                   read_json(args.observation) if args.observation else {})
        else:
            result = check(args.run_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result["issues"] else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
