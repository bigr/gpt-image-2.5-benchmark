# Plan: distributing the 300 images (not built)

Facts, read from the original run directory:

- 300 PNG files, 1,192,414,991 bytes in total (about 1.19 GB, 1.11 GiB). PNGs of this kind compress
  very little, so an archive is about the same size.
- Layout: `images/<prompt id>/<variant>-<index>.png`, 15 prompt directories x 20 files.
- `data/image-manifest.csv` has the filename, SHA-256 and size of every file.

Proposal (needs the author's approval; limits to be re-checked on the day of publication):

1. Do not commit the images to git. A 1.2 GB binary history is permanent and slows every clone.
2. Attach to the first GitHub Release of the repository:
   - `images-v2.zip` (the whole set, about 1.2 GB), or three archives by test if a single asset
     turns out to exceed the per-file limit that applies at that time (as understood now, a release
     asset may be up to 2 GiB; verify before relying on it);
   - `images-v2.sha256` (the SHA-256 of the archive itself).
3. `python -m benchmark.verify_images <dir>` (to be added) would check an extracted directory against
   `data/image-manifest.csv`. Not built yet; `sha256sum -c`-style verification can be done with any tool.
4. Small samples: only images the article already shows may be committed, downscaled below 500 KB each
   (optional; the author chooses which).
5. Alternative hosts (for instance a dataset hosting service) are possible if the author prefers one;
   they change only the download link.

Until the archive exists, the README states that the tables can be recomputed but the 300 images
cannot yet be judged independently.
