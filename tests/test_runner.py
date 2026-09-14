"""Unit tests for runner/ (tester, inputs, sandbox) + executor protocol."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from runner import tester  # noqa: E402
from runner import inputs as inputmod  # noqa: E402
from runner.sandbox import run_capped  # noqa: E402


class TestTester(unittest.TestCase):
    def test_compare_equal_and_different(self):
        self.assertTrue(tester.compare([1, 2], [1, 2]))
        self.assertTrue(tester.compare({"b": 1, "a": 2}, {"a": 2, "b": 1}))
        self.assertFalse(tester.compare([1, 2], [2, 1]))
        self.assertFalse(tester.compare(1, "1"))

    def test_load_reference(self):
        ns = tester.load_reference(
            {"reference_solution": {"code": "def f(x):\n    return x + 1\n"}})
        self.assertEqual(ns["f"](1), 2)

    def test_load_reference_missing(self):
        with self.assertRaises(ValueError):
            tester.load_reference({})

    def test_safe_call_captures_errors(self):
        errors = []
        self.assertIsNone(tester.safe_call(lambda: 1 / 0, (), {}, errors))
        self.assertIn("ZeroDivisionError", errors[0])
        self.assertEqual(tester.safe_call(lambda: 7, (), {}, errors), 7)


class TestInputs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gcb-test-inputs-"))
        self.inp = {
            "docs": ["alpha beta", "gamma"],
            "records": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}],
            "k": 5,
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_materialize(self):
        inputmod.materialize(self.tmp, self.inp)
        self.assertEqual(json.loads((self.tmp / "docs.json").read_text()),
                         self.inp["docs"])
        csv_text = (self.tmp / "records.csv").read_text().strip().splitlines()
        self.assertEqual(csv_text[0], "id,v")
        self.assertEqual(csv_text[1], "1,x")
        self.assertEqual(
            json.loads((self.tmp / "manifest.json").read_text())["__content_sha256__"],
            inputmod.content_sha256(self.inp))

    def test_stdin_text_prefers_string_list(self):
        self.assertEqual(inputmod.stdin_text(self.inp), "alpha beta\ngamma\n")

    def test_stage_links_and_refreshes(self):
        work = self.tmp / "work"
        work.mkdir()
        persistent = self.tmp / "inputs" / "CAT" / "T-1" / "small"
        env = inputmod.stage(persistent, work, self.inp)
        self.assertTrue((work / "docs.json").is_file())
        self.assertTrue((work / "input.txt").read_text().startswith("alpha"))
        self.assertEqual(env["GCB_INPUT_DIR"], str(persistent))
        # changed workload -> files refreshed
        self.inp["docs"] = ["changed"]
        inputmod.stage(persistent, work, self.inp)
        self.assertEqual(json.loads((persistent / "docs.json").read_text()),
                         ["changed"])


class TestSandbox(unittest.TestCase):
    def test_run_capped_captures_output(self):
        out, err, metrics, timed_out = run_capped(
            [sys.executable, "-c", "print('hello')"], timeout_s=30)
        self.assertFalse(timed_out)
        self.assertIn("hello", out)
        self.assertEqual(metrics["returncode"], 0)
        self.assertGreater(metrics["wall_ms"], 0)

    def test_run_capped_timeout(self):
        _, _, _, timed_out = run_capped(
            [sys.executable, "-c", "import time; time.sleep(5)"], timeout_s=1)
        self.assertTrue(timed_out)

    def test_stdin_is_devnull_no_hang(self):
        # input() must hit EOF immediately instead of blocking forever
        code = ("try:\n input()\n print('GOT')\n"
                "except EOFError:\n print('EOF')\n")
        out, _, _, timed_out = run_capped(
            [sys.executable, "-c", code], timeout_s=15)
        self.assertFalse(timed_out)
        self.assertIn("EOF", out)


class TestExecutorProtocol(unittest.TestCase):
    """End-to-end: a correct candidate vs the real SR-001 reference."""

    CANDIDATE = """
def build_index(docs):
    idx = {}
    for i, d in enumerate(docs):
        for t in d.lower().split():
            idx.setdefault(t, set()).add(i)
    return idx

def search(index, query_tokens):
    if not query_tokens:
        return []
    sets = [index.get(str(t).lower(), set()) for t in query_tokens]
    out = set.intersection(*sets) if sets else set()
    return sorted(out)
"""

    def run_executor(self, code_src):
        with tempfile.TemporaryDirectory() as td:
            code = Path(td) / "cand.py"
            code.write_text(code_src, encoding="utf-8")
            task = json.loads((REPO / "dataset" / "search_retrieval" /
                               "dataset.json").read_text(encoding="utf-8"))
            t = next(t for t in task["tasks"] if t["task_id"] == "SR-001")
            task_file = Path(td) / "task.json"
            task_file.write_text(json.dumps(t), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(REPO / "runner" / "executor.py"),
                 "--code", str(code), "--task-json", str(task_file),
                 "--category", "search_retrieval"],
                capture_output=True, text=True, timeout=280)
            return r

    def test_correct_candidate_status_ok_and_inputs_materialized(self):
        r = self.run_executor(self.CANDIDATE)
        payload = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(r.returncode, 0)
        self.assertIn("correct", payload)
        self.assertIn("inputs", payload)
        inputs_dir = REPO / payload["inputs"]
        self.assertTrue((inputs_dir / "small" / "manifest.json").is_file())
        self.assertTrue((inputs_dir / "small" / "docs.json").is_file())


if __name__ == "__main__":
    unittest.main()
