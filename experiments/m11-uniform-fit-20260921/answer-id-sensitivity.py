#!/usr/bin/env python3
"""Post-development sensitivity for canonical final-answer event IDs.

This script does not call a model, refit a model, or modify the original
assessment/review/data files.  It derives a separate audit packet by changing
only answer_event_id when the quoted answer text is an exact substring of the
final answer.  Raw IDs are retained as raw_answer_event_id.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import assess

ROOT = Path(__file__).resolve().parent
SENS = ROOT / "sensitivity"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def refuse_overwrite(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing sensitivity output: {path}")


def derive_outcome(item: dict, reviewed_path: Path):
    reviewed = load_json(reviewed_path)
    provenance = reviewed.get("_provenance", {})
    original_rel = provenance.get("original_assessment")
    if not original_rel:
        raise ValueError(f"missing original_assessment provenance: {reviewed_path}")
    original_path = ROOT / original_rel
    original = load_json(original_path)
    if not isinstance(original.get("raw_assessment"), dict):
        raise ValueError(f"missing raw_assessment: {original_path}")

    raw = copy.deepcopy(original["raw_assessment"])
    corrections = []
    final = item["final"]
    for req in raw.get("requirements", []):
        quote = req.get("answer_quote")
        old_id = req.get("answer_event_id")
        if (
            isinstance(quote, str)
            and bool(quote.strip())
            and quote in final
            and old_id not in ("run-end", "final")
        ):
            req["raw_answer_event_id"] = old_id
            req["answer_event_id"] = "run-end"
            corrections.append(
                {
                    "requirement": req.get("id"),
                    "raw_answer_event_id": old_id,
                    "canonical_answer_event_id": "run-end",
                    "answer_quote_exact_in_final": True,
                    "raw_status": req.get("status"),
                }
            )

    audited = assess.audit(raw, item, "outcome")
    audited.update(
        {
            "case": item["case"],
            "task_id": item["task_id"],
            "ecosystem": item["ecosystem"],
            "split": item["split"],
            "budget": item.get("budget"),
            "_sensitivity": {
                "kind": "answer_event_id_canonicalization",
                "primary_status": "post-development audit sensitivity; not the predeclared primary analysis",
                "original_assessment": str(original_path.relative_to(ROOT)),
                "original_assessment_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
                "reviewed_assessment": str(reviewed_path.relative_to(ROOT)),
            },
        }
    )
    return audited, corrections


def outcome_interval(outcome: dict):
    req = outcome.get("requirements", [])
    if len(req) != 6:
        raise ValueError(f"expected six requirements for {outcome.get('case')}")
    statuses = {x.get("status") for x in req}
    allowed = {"supported", "absent", "contradicted", "unverified"}
    if not statuses <= allowed:
        raise ValueError(f"invalid outcome status for {outcome.get('case')}: {statuses}")
    return [
        sum(x.get("status") == "supported" for x in req) / 6,
        sum(x.get("status") in ("supported", "unverified") for x in req) / 6,
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=("development", "heldout"), required=True)
    args = ap.parse_args()

    if args.split == "heldout" and not (SENS / "frozen-selection.json").exists():
        raise SystemExit("heldout sensitivity requires sensitivity/frozen-selection.json")

    packet = load_json(ROOT / "assessment-input" / f"{args.split}.json")
    rows_path = ROOT / f"{args.split}-data.json"
    rows = load_json(rows_path)
    if not isinstance(rows, list):
        raise ValueError(f"{rows_path} must contain a JSON array")
    by_case = {r["case"]: r for r in rows}
    if len(by_case) != len(rows):
        raise ValueError(f"duplicate cases in {rows_path}")
    packet_by_case = {x["case"]: x for x in packet}
    if len(packet_by_case) != len(packet) or not set(by_case) <= set(packet_by_case):
        raise ValueError(f"assessment packet/data case mismatch for {args.split}")

    out_dir = SENS / f"{args.split}-outcomes"
    data_path = SENS / f"{args.split}-data.json"
    corrections_path = SENS / f"{args.split}-corrections.json"
    refuse_overwrite(data_path)
    refuse_overwrite(corrections_path)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing sensitivity outcomes: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    derived_rows = []
    correction_records = []
    outcome_paths = []
    # Preserve the frozen input row order and every field verbatim.
    for base_row in rows:
        case = base_row["case"]
        item = packet_by_case[case]
        reviewed_path = ROOT / "reviewed" / args.split / f"{case}-outcome.json"
        if not reviewed_path.exists():
            raise FileNotFoundError(f"missing finalized outcome: {reviewed_path}")
        outcome, corrections = derive_outcome(item, reviewed_path)
        out_path = out_dir / f"{case}-outcome.json"
        out_path.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        outcome_paths.append(str(out_path.relative_to(ROOT)))
        correction_records.append({"case": case, "corrections": corrections})
        row = copy.deepcopy(base_row)
        row["outcome_interval"] = outcome_interval(outcome)
        derived_rows.append(row)

    data_path.write_text(json.dumps(derived_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    corrections_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "split": args.split,
                    "kind": "answer_event_id_canonicalization",
                    "primary_status": "post-development audit sensitivity; not the predeclared primary analysis",
                    "rule": "nonempty answer_quote exact in final => answer_event_id=run-end; preserve raw_answer_event_id",
                    "model_calls": 0,
                    "fit_run": False,
                    "source_data": str(rows_path.relative_to(ROOT)),
                    "outcome_dir": str(out_dir.relative_to(ROOT)),
                },
                "cases": correction_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "split": args.split,
                "rows": len(derived_rows),
                "corrections": sum(len(x["corrections"]) for x in correction_records),
                "data": str(data_path.relative_to(ROOT)),
                "corrections_file": str(corrections_path.relative_to(ROOT)),
                "outcomes": len(outcome_paths),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
