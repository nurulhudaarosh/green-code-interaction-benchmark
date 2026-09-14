"""Dataset schema tests: every dataset/<category>/dataset.json is valid,
well-formed, and (for collected categories) has a runnable harness."""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CATEGORIES = {
    "file_data_processing": "FD",
    "text_log_processing": "TL",
    "search_retrieval": "SR",
    "algorithms_computation": "AC",
    "image_media_processing": "IM",
    "realistic_applications_utilities": "RA",
}
INTERACTIONS = {"ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE",
                "FULL_MULTI_TURN"}
REQUIRED_TASK_KEYS = {"task_id", "title", "problem_description",
                      "reference_solution", "interactions", "category"}


def dataset_files():
    for cat in sorted(CATEGORIES):
        yield cat, REPO / "dataset" / cat / "dataset.json"


class TestDatasets(unittest.TestCase):
    def test_files_exist_and_parse(self):
        for cat, path in dataset_files():
            with self.subTest(category=cat):
                self.assertTrue(path.is_file(), f"missing {path}")
                self.assertGreater(path.stat().st_size, 0,
                                   f"{path} is empty (run scripts/project-setup.sh)")
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIn("tasks", data)
                self.assertIsInstance(data["tasks"], list)

    def test_task_schema(self):
        for cat, path in dataset_files():
            data = json.loads(path.read_text(encoding="utf-8"))
            for task in data.get("tasks", []):
                tid = task.get("task_id", "?")
                with self.subTest(task=tid):
                    for key in REQUIRED_TASK_KEYS:
                        self.assertIn(key, task)
                    self.assertTrue(task["task_id"].startswith(
                        json.loads(path.read_text())["dataset_metadata"]
                        .get("category_code", cat[:2].upper())))
                    ref = task["reference_solution"]
                    self.assertTrue((ref or {}).get("code"),
                                    f"{tid} has no reference_solution.code")
                    self.assertEqual(set(task["interactions"]), INTERACTIONS)

    def test_task_ids_unique(self):
        for cat, path in dataset_files():
            data = json.loads(path.read_text(encoding="utf-8"))
            ids = [t["task_id"] for t in data.get("tasks", [])]
            self.assertEqual(len(ids), len(set(ids)), f"duplicate ids in {cat}")

    def test_harness_exists_for_every_collected_task(self):
        for cat, path in dataset_files():
            data = json.loads(path.read_text(encoding="utf-8"))
            for task in data.get("tasks", []):
                tid = task["task_id"]
                with self.subTest(task=tid):
                    self.assertTrue(
                        (REPO / "tests" / "harness" / cat / f"{tid}.py").is_file(),
                        f"missing harness tests/harness/{cat}/{tid}.py")


if __name__ == "__main__":
    unittest.main()
