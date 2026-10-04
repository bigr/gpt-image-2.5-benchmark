# Images

All 300 images are available; downloads are free and unlimited.

- **Thumbnails in git**: `thumbnails/<prompt id>/<variant>-<index>.webp`, longest side 512 px, WebP
  quality 80 (about 11 MB in total). The [gallery](../gallery/README.md) shows them with the
  corrected outcome of each image. Regenerate with
  `uv run --with pillow python scripts/make_thumbnails.py <images_dir> thumbnails`
  (Pillow is needed only by that optional script).
- **Full-resolution PNGs**: 300 files, 1,192,414,991 bytes (about 1.19 GB), attached to the GitHub
  release tagged `dataset-v2` as individual assets named `<prompt id>__<variant>-<index>.png`
  (release assets cannot have directories), plus `images-v2.zip` with the original layout
  `<prompt id>/<variant>-<index>.png`, and `SHA256SUMS` for all of them.
- **Staging**: `python scripts/stage_release.py <images_dir> release` verifies every file against
  `data/image-manifest.csv`, then writes the flat copies, the zip (stored, not recompressed) and
  `SHA256SUMS`. The `release` directory is git-ignored.

## Verify a download

```sh
python -m benchmark.verify_images <dir>
```

`<dir>` may hold the nested layout (the unzipped archive) or the flat release files. The command
compares SHA-256 and size of each image with `data/image-manifest.csv`, prints how many are missing,
mismatched or extra, and exits 1 on any problem. `sha256sum -c SHA256SUMS` works too.

The images are CC BY 4.0, see `LICENSE-DATA`.
