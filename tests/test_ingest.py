"""Tests for ingest code-copy semantics (local fixes survive re-ingest)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ingest_zips  # noqa: E402

import tempfile  # noqa: E402


class TestLocalFixPreservation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "inbox" / "code"
        self.dest = self.root / "collected" / "code"
        (self.src / "gpt" / "T-001").mkdir(parents=True)
        (self.src / "gpt" / "T-001" / "final.py").write_text("x = 1\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_copy_then_local_fix_survives(self):
        kept = ingest_zips.copy_code_preserving_local(self.src, self.dest)
        self.assertEqual(kept, [])
        self.assertEqual((self.dest / "gpt/T-001/final.py").read_text(),
                         "x = 1\n")
        # user edits the collected copy to fix a bug
        (self.dest / "gpt/T-001/final.py").write_text("x = 2  # local fix\n")
        kept = ingest_zips.copy_code_preserving_local(self.src, self.dest)
        self.assertEqual(kept, [str(Path("gpt/T-001/final.py"))])
        self.assertIn("local fix",
                      (self.dest / "gpt/T-001/final.py").read_text())

    def test_new_inbox_file_still_copied(self):
        ingest_zips.copy_code_preserving_local(self.src, self.dest)
        (self.src / "gpt" / "T-002").mkdir()
        (self.src / "gpt" / "T-002" / "code.py").write_text("y = 1\n")
        kept = ingest_zips.copy_code_preserving_local(self.src, self.dest)
        self.assertEqual(kept, [])
        self.assertTrue((self.dest / "gpt/T-002/code.py").is_file())


if __name__ == "__main__":
    unittest.main()
