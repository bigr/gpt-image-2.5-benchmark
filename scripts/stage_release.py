"""Stage the GitHub release assets for the images (tag ``dataset-v2``).

    python scripts/stage_release.py <images_dir> <out_dir>

Every PNG is verified against ``data/image-manifest.csv`` first; any missing, mismatched or extra
file aborts before anything is copied. Then ``<out_dir>`` receives the flat copies
``<prompt id>__<variant>-<index>.png``, ``images-v2.zip`` (stored, original directory layout) and
``SHA256SUMS`` for all of them. Standard library only.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark import verify_images as vi  # noqa: E402

ZIP_NAME = "images-v2.zip"


def stage(images: Path, out: Path, manifest_path: Path | None = None) -> list[str]:
    manifest = vi.read_manifest(manifest_path or ROOT / "data" / "image-manifest.csv")
    res = vi.verify(images, manifest)
    if any(res.values()):
        raise SystemExit(f"refusing to stage, directory does not match the manifest: {res}")
    out.mkdir(parents=True, exist_ok=True)
    names = sorted(manifest)
    for n in names:
        dest = out / vi.flat_name(n)
        dest.write_bytes((images / n).read_bytes())
        if vi.sha256_of(dest) != manifest[n][0]:
            raise SystemExit(f"copy of {n} does not match the manifest")
    zpath = out / ZIP_NAME
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_STORED) as zf:
        for n in names:
            zf.write(images / n, arcname=n)
    sums = [f"{manifest[n][0]}  {vi.flat_name(n)}" for n in names]
    sums.append(f"{vi.sha256_of(zpath)}  {ZIP_NAME}")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return names


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    names = stage(Path(argv[0]), Path(argv[1]))
    print(f"staged {len(names)} images + {ZIP_NAME} + SHA256SUMS in {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
