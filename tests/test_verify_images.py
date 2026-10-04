"""verify_images on tiny synthetic files (never the real images)."""

import contextlib
import hashlib
import io
import tempfile
import unittest
from pathlib import Path

from benchmark import verify_images as vi

FILES = {"p1/a-0.png": b"alpha", "p1/a-1.png": b"beta", "p2/b-0.png": b"gamma"}


def manifest_for(root: Path) -> Path:
    lines = ["filename,sha256,bytes"]
    for n, b in FILES.items():
        lines.append(f"{n},{hashlib.sha256(b).hexdigest()},{len(b)}")
    path = root / "manifest.csv"
    path.write_text("\n".join(lines) + "\n")
    return path


def run(directory: Path, manifest: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = vi.main([str(directory), "--manifest", str(manifest)])
    return code, buf.getvalue()


class VerifyImages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.manifest = manifest_for(self.root)
        self.imgs = self.root / "imgs"
        self.imgs.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, name: str, data: bytes) -> None:
        p = self.imgs / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def test_nested_layout_passes(self):
        for n, b in FILES.items():
            self.put(n, b)
        code, out = run(self.imgs, self.manifest)
        self.assertEqual(code, 0)
        self.assertIn("ok 3, missing 0, mismatched 0, extra 0", out)

    def test_flat_names_pass(self):
        for n, b in FILES.items():
            self.put(vi.flat_name(n), b)
        self.assertEqual(run(self.imgs, self.manifest)[0], 0)

    def test_missing_mismatched_extra_each_fail(self):
        self.put("p1/a-0.png", b"alpha")
        self.put("p1/a-1.png", b"WRONG")
        self.put("zzz/unknown-0.png", b"x")
        code, out = run(self.imgs, self.manifest)
        self.assertEqual(code, 1)
        self.assertIn("ok 1, missing 1, mismatched 1, extra 1", out)
        self.assertIn("missing: p2/b-0.png", out)
        self.assertIn("mismatched: p1/a-1.png", out)

    def test_same_size_different_content_is_mismatch(self):
        for n, b in FILES.items():
            self.put(n, b)
        self.put("p1/a-0.png", b"ALPHA")
        self.assertEqual(run(self.imgs, self.manifest)[0], 1)

    def test_duplicate_in_both_layouts_counts_as_extra(self):
        for n, b in FILES.items():
            self.put(n, b)
        self.put("p1__a-0.png", b"alpha")
        code, out = run(self.imgs, self.manifest)
        self.assertEqual(code, 1)
        self.assertIn("extra 1", out)

    def test_empty_directory_and_bad_path(self):
        self.assertEqual(run(self.imgs, self.manifest)[0], 1)
        self.assertEqual(vi.main([str(self.root / "nope")]), 2)

    def test_real_manifest_parses(self):
        m = vi.read_manifest(Path(__file__).resolve().parent.parent / "data" / "image-manifest.csv")
        self.assertEqual(len(m), 300)


if __name__ == "__main__":
    unittest.main()
