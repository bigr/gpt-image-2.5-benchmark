"""Check a directory of images against ``data/image-manifest.csv``.

    python -m benchmark.verify_images <dir> [--manifest data/image-manifest.csv]

Accepts the nested layout (``<prompt id>/<variant>-<index>.png``, as in ``images-v2.zip``) or the
flat release names (``<prompt id>__<variant>-<index>.png``). Prints missing / mismatched / extra
counts and exits 1 on any problem. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path

FLAT_SEP = "__"


def read_manifest(path: Path) -> dict[str, tuple[str, int]]:
    """Manifest name (nested form) -> (sha256, bytes)."""
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["filename"]: (r["sha256"], int(r["bytes"])) for r in csv.DictReader(fh)}


def flat_name(nested: str) -> str:
    return nested.replace("/", FLAT_SEP)


def canonical(rel: str) -> str:
    """Map a relative file path (nested or flat) to the manifest's nested form."""
    rel = rel.replace("\\", "/")
    if "/" not in rel and FLAT_SEP in rel:
        return rel.replace(FLAT_SEP, "/", 1)
    return rel


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(directory: Path, manifest: dict[str, tuple[str, int]]) -> dict[str, list[str]]:
    found: dict[str, Path] = {}
    extra: list[str] = []
    for p in sorted(directory.rglob("*.png")):
        name = canonical(p.relative_to(directory).as_posix())
        if name in manifest and name not in found:
            found[name] = p
        else:
            extra.append(p.relative_to(directory).as_posix())
    missing = sorted(set(manifest) - set(found))
    mismatched = [
        n
        for n, p in sorted(found.items())
        if p.stat().st_size != manifest[n][1] or sha256_of(p) != manifest[n][0]
    ]
    return {"missing": missing, "mismatched": mismatched, "extra": extra}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("directory", type=Path)
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "image-manifest.csv",
    )
    args = ap.parse_args(argv)
    if not args.directory.is_dir():
        print(f"not a directory: {args.directory}", file=sys.stderr)
        return 2
    manifest = read_manifest(args.manifest)
    res = verify(args.directory, manifest)
    ok = len(manifest) - len(res["missing"]) - len(res["mismatched"])
    print(
        f"expected {len(manifest)}: ok {ok}, missing {len(res['missing'])}, "
        f"mismatched {len(res['mismatched'])}, extra {len(res['extra'])}"
    )
    for label in ("missing", "mismatched", "extra"):
        for n in res[label][:20]:
            print(f"  {label}: {n}")
    return 1 if any(res.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
