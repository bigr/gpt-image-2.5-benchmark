"""Write WebP thumbnails (longest side 512 px) of every image.

    uv run --with pillow python scripts/make_thumbnails.py <images_dir> <out_dir>

Reads ``<images_dir>/<prompt id>/<variant>-<index>.png`` and writes
``<out_dir>/<prompt id>/<variant>-<index>.webp``. Optional tool: Pillow is needed only here, never
by ``benchmark/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

SIDE = 512
QUALITY = 80


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src, out = Path(argv[0]), Path(argv[1])
    pngs = sorted(src.glob("*/*.png"))
    if not pngs:
        print(f"no PNG files under {src}", file=sys.stderr)
        return 1
    total = 0
    for p in pngs:
        dest = out / p.parent.name / (p.stem + ".webp")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(p) as im:
            im = im.convert("RGB")
            scale = SIDE / max(im.size)
            if scale < 1:
                im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
            im.save(dest, "WEBP", quality=QUALITY, method=6)
        total += dest.stat().st_size
    print(f"{len(pngs)} thumbnails, {total / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
