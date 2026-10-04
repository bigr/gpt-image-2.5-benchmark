"""End-to-end: the published dataset reproduces the numbers printed in the article (revision 2).

Every expected value is exact to one decimal. If one fails, do not adjust the data: find the cause.
"""

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from benchmark import analyze

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


class Reproduce(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {
            p: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.rglob("*") if p.is_file()
        }
        cls.r = analyze.analyze(analyze.load_dataset(DATA))

    def test_inputs_are_untouched(self):
        after = {
            p: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.rglob("*") if p.is_file()
        }
        self.assertEqual(self.before, after)

    def test_counts(self):
        self.assertEqual(self.r["counts"]["images"], 300)
        self.assertEqual(self.r["counts"]["images_with_addition"], 279)
        self.assertEqual(self.r["counts"]["checklist_answers_scored"], 1758)

    def test_checklist_precision_recall_specificity(self):
        want = {
            "gpt-6.1-sol": (98.7, 99.1, 93.3),
            "gpt-6-sol": (98.0, 98.6, 89.8),
            "gpt-6-luna": (96.6, 99.5, 81.7),
        }
        for name, (p, rec, s) in want.items():
            m = self.r["checklist"][name]
            self.assertEqual((m["precision"], m["recall"], m["specificity"]), (p, rec, s), name)

    def test_additions_accuracy_precision_recall(self):
        want = {
            "gpt-6.1-sol": (98.3, 100.0, 98.2),
            "gpt-6-sol": (84.7, 100.0, 83.5),
            "gpt-6-luna": (60.7, 100.0, 57.7),
            "always yes": (93.0, 93.0, 100.0),
        }
        for name, (a, p, rec) in want.items():
            m = self.r["additions"][name]
            self.assertEqual((m["accuracy"], m["precision"], m["recall"]), (a, p, rec), name)

    def test_medium_effort_rerun(self):
        n = "gpt-6.1-sol (medium effort)"
        self.assertEqual(self.r["checklist"][n]["specificity"], 93.3)
        a = self.r["additions"][n]
        self.assertEqual((a["accuracy"], a["precision"], a["recall"]), (99.0, 99.3, 99.6))

    def test_generator_tables(self):
        g = self.r["generator"]
        self.assertEqual(
            [g["sunburst"][f"elements_{n}"]["pct"] for n in (8, 15, 25)], [88.8, 94.0, 94.0]
        )
        self.assertEqual(
            [g["flare"][f"elements_{n}"]["pct"] for n in (8, 15, 25)], [95.0, 96.0, 96.0]
        )
        self.assertEqual(g["sunburst"]["specific_details"]["pct"], 97.6)
        self.assertEqual(g["flare"]["specific_details"]["pct"], 98.6)
        for s in ("sunburst", "flare"):
            self.assertEqual(g[s]["forbidden_thing_drawn"], {"drawn": 0, "counted": 50})
            self.assertEqual(g[s]["landmark_substituted"], {"drawn": 0, "counted": 60})
        self.assertEqual(g["sunburst"]["period_images_with_additions"]["with_additions"], 54)
        self.assertEqual(g["flare"]["period_images_with_additions"]["with_additions"], 45)

    def test_additions_per_image_range(self):
        v = self.r["reference_additions_per_image"]
        self.assertEqual((min(v["sunburst"].values()), max(v["sunburst"].values())), (3.2, 5.3))
        self.assertEqual((min(v["flare"].values()), max(v["flare"].values())), (2.0, 4.2))

    def test_settled_rows(self):
        s = self.r["settled_rows"]
        self.assertEqual(s["rows"], 273)
        ag = s["agreement"]
        self.assertEqual(ag["reference"]["pct"], 87.2)
        self.assertEqual(ag["gpt-6.1-sol"]["pct"], 84.6)

    def test_cli_writes_outputs_and_refuses_data_dir(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(analyze.main(["--data", str(DATA), "--output", tmp]), 0)
            self.assertTrue((Path(tmp) / "summary.json").exists())
            self.assertTrue((Path(tmp) / "tables.md").exists())
            self.assertEqual(
                json.loads((Path(tmp) / "summary.json").read_text())["counts"]["images"], 300
            )
        self.assertEqual(analyze.main(["--data", str(DATA), "--output", str(DATA / "out")]), 2)
        self.assertFalse((DATA / "out").exists())


class DataIntegrity(unittest.TestCase):
    def test_manifest_lists_300_images_and_total_bytes(self):
        lines = (DATA / "image-manifest.csv").read_text().splitlines()[1:]
        self.assertEqual(len(lines), 300)
        self.assertEqual(sum(int(line.split(",")[2]) for line in lines), 1192414991)

    def test_no_internal_strings_in_data(self):
        import hashlib
        import re

        banned = ("founder", "/home/", "_reasons")
        # names that must not appear are checked by hash, so this test does not publish them
        banned_hashes = {"9eaf6dd036b82a982e32d5159c68749ac3ad848a9410ddedec8da3d6b222c4e2"}
        for p in DATA.rglob("*"):
            if p.is_file():
                text = p.read_text(encoding="utf-8").lower()
                for b in banned:
                    self.assertNotIn(b, text, f"{p} contains {b}")
                for word in set(re.findall(r"[a-z]+", text)):
                    digest = hashlib.sha256(word.encode()).hexdigest()
                    self.assertNotIn(digest, banned_hashes, f"{p} contains an internal name")


if __name__ == "__main__":
    unittest.main()
