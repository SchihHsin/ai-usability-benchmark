"""Synthetic inputs only. No provider requests or real experiment data."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import score_template as score
from scripts import run_log


def raw():
    return copy.deepcopy(score.RAW["EXAMPLE"]["target"])


def record(model="test-model"):
    value = raw()
    return {"run_id": model + "-A-cann-1", "task_id": "A", "ecosystem": "CANN",
            "model_id": model, "repetition": 1, "protocol_version": "test-1",
            "rubric_version": score.RUBRIC_VERSION, "raw": value,
            "evidence_refs": {key: ["synthetic:event"] for key in value}}


class ScoringTests(unittest.TestCase):
    def test_existing_complete_example(self):
        result = score.score_record(raw(), (2026, 6))
        self.assertEqual(result["scores"], [3, 4, 4, 2, 3, 3, 3, 3, 4, 4])
        self.assertEqual(result["overall"], .663)
        self.assertAlmostEqual(result["overall_exact"], .6630617088)

    def test_model_label_does_not_change_score(self):
        values = score.score_records([record(m) for m in ("one", "two", "three")], (2026, 9))
        self.assertEqual(len({r["overall_exact"] for r in values}), 1)
        self.assertEqual(len({tuple(r["scores"]) for r in values}), 1)

    def test_confirmed_m2_partial(self):
        value = raw()
        value["core_fetch"] = "partial"
        result = score.score_record(value, (2026, 9))
        self.assertEqual(result["scores"][1], 3)
        self.assertEqual(result["scores"][2], 4)
        self.assertLess(result["overall_exact"], score.score_record(raw(), (2026, 9))["overall_exact"])

    def test_explicit_reference_month_reaches_m6(self):
        value = raw()
        value.update(sources=["tech_blog"], platforms=["example.org"], dates=["2023-07"], consist="high")
        before = score.score_record(value, (2026, 6))
        after = score.score_record(value, (2028, 8))
        self.assertEqual(before["scores"][5], 4)
        self.assertEqual(after["scores"][5], 4)  # Python round(3.5), not custom rounding.
        self.assertEqual(score.recency_factor(value["dates"], today=(2026, 6)), 0)
        self.assertEqual(score.recency_factor(value["dates"], today=(2028, 8)), -.5)
        value.update(sources=["qa_reputation"], consist="mid")
        self.assertEqual(score.score_record(value, (2026, 6))["scores"][5], 4)
        self.assertEqual(score.score_record(value, (2028, 8))["scores"][5], 3)

    def test_no_sources_is_not_unknown(self):
        value = raw()
        value.update(sources=[], platforms=[], dates=[], consist=None)
        result = score.score_record(value, (2026, 9))
        self.assertEqual(result["scores"][4:6], [1, "无来源"])
        self.assertEqual(result["mid"]["SEC"], 0)
        self.assertEqual(result["metric_status"][5], "no_sources")
        value["sources"] = None
        unknown = score.score_record(value, (2026, 9))
        self.assertEqual(unknown["scores"][4:6], [None, None])
        self.assertIsNone(unknown["overall"])

    def test_unknown_delivery_does_not_invent_m2_or_hide_m3(self):
        value = raw()
        value.update(core_fetch=None, body_status="retrieved")
        result = score.score_record(value, (2026, 9))
        self.assertIsNone(result["scores"][1])
        self.assertEqual(result["scores"][2], 4)
        self.assertIsNone(result["overall"])

    def test_blocked_body_not_low_detail(self):
        value = raw()
        value.update(core_fetch="robots", exec=None, ref_level=None)
        result = score.score_record(value, (2026, 9))
        self.assertEqual(result["scores"][1:3], [1, "受阻"])
        self.assertEqual(result["mid"]["OFF"], 0)

    def test_missing_outcomes_do_not_block_m11(self):
        value = raw()
        value.update(pin=None, repro=None)
        result = score.score_record(value, (2026, 9))
        self.assertEqual(result["scores"][8:], [None, None])
        self.assertIsNotNone(result["overall"])

    def test_missing_evidence_not_silent_score(self):
        result = score.score_record(raw(), (2026, 9), {})
        self.assertEqual(result["scores"], [None] * 10)
        self.assertIsNone(result["overall"])
        self.assertEqual(result["metric_status"], ["unverified"] * 10)

    def test_invalid_inputs(self):
        changes = [dict(fetch_fail=100), dict(exec="false"), dict(own=True),
                   dict(platforms=[]), dict(dates=["2026-13", None, None]),
                   dict(dates=["2030-01", None, None]), dict(sources=["official_doc"]),
                   dict(n_versions=0), dict(core_fetch="ssr", body_status="not_retrieved")]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                score.score_record({**raw(), **change}, (2026, 9))

    def test_duplicate_run_and_mixed_protocol_rejected(self):
        with self.assertRaises(ValueError):
            score.score_records([record(), record()], (2026, 9))
        second = record("other")
        second["protocol_version"] = "different"
        with self.assertRaises(ValueError):
            score.score_records([record(), second], (2026, 9))

    def test_cli_requires_date_and_reads_jsonl(self):
        with tempfile.TemporaryDirectory() as temp:
            input_path = Path(temp) / "observations.jsonl"
            input_path.write_text(json.dumps(record()) + "\n")
            cmd = [sys.executable, str(ROOT / "score_template.py"), "--input", str(input_path)]
            missing = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertEqual(missing.stdout, "")
            complete = subprocess.run(cmd + ["--as-of", "2026-09"], capture_output=True, text=True)
            self.assertEqual(complete.returncode, 0, complete.stderr)
            result = json.loads(complete.stdout)
            self.assertEqual(result[0]["model_id"], "test-model")
            self.assertEqual(result[0]["reference_month"], "2026-09")


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "run"
        self.question = self.root / "question.txt"
        self.question.write_text("合成测试问句\n", encoding="utf-8")
        run_log.init_run(self.directory, record(), self.question)

    def test_round_trip_bytes_and_detect_corruption(self):
        run_log.begin(self.directory, "s001", "search", "synthetic", {"query": "test"})
        body = self.root / "response.txt"
        body.write_bytes("第一条\r\n第二条\n".encode())
        run_log.finish(self.directory, "s001", body, "ok", {"returned_results": 2})
        (self.directory / "answer.md").write_text("合成回答")
        result = run_log.check(self.directory)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["calls"]["search"], 1)
        saved = self.directory / "events/s001/response.bin"
        self.assertEqual(saved.read_bytes(), body.read_bytes())
        saved.write_bytes(b"changed")
        self.assertTrue(any("哈希" in issue for issue in run_log.check(self.directory)["issues"]))

    def test_interrupted_call_is_retained(self):
        run_log.begin(self.directory, "f001", "fetch", "synthetic", {"url": "https://example.org"})
        result = run_log.check(self.directory)
        self.assertEqual(result["calls"]["fetch"], 1)
        self.assertTrue(any("未保存返回" in issue for issue in result["issues"]))

    def test_no_overwrite_and_parent_link(self):
        run_log.begin(self.directory, "s001", "search", "synthetic", {})
        with self.assertRaises(FileExistsError):
            run_log.begin(self.directory, "s001", "search", "synthetic", {})
        run_log.begin(self.directory, "f001", "fetch", "synthetic", {}, parent="s001")
        response = self.root / "response.txt"
        response.write_bytes(b"")
        run_log.finish(self.directory, "f001", response, "error", {})
        with self.assertRaises(ValueError):
            run_log.finish(self.directory, "f001", response, "ok", {})
        self.assertEqual(run_log.read_json(self.directory / "events/f001/request.json")["parent_event_id"], "s001")
        with self.assertRaises(FileExistsError):
            run_log.init_run(self.directory, record(), self.question)

    def test_reject_credentials_and_path_ids(self):
        with self.assertRaises(ValueError):
            run_log.begin(self.directory, "s001", "search", "synthetic", {"headers": {"Authorization": "secret"}})
        self.assertFalse((self.directory / "events/s001").exists())
        with self.assertRaises(ValueError):
            run_log.begin(self.directory, "../outside", "fetch", "synthetic", {})


if __name__ == "__main__":
    unittest.main()
