"""Generate ``gallery/``: an index plus one page per prompt id, from the committed data.

    python scripts/make_gallery.py [--out gallery]

Each page shows the 20 thumbnails (two variants x 10 images), the prompt, and for every image the
outcome in the corrected reference (model reading overridden by human rulings): checklist items
that failed, whether an unrequested addition is present, and how many questions a person ruled on.
Nothing is shown that the data does not contain. Thumbnails are relative links; full-resolution PNGs
link to the ``dataset-v2`` release. Standard library only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark import analyze  # noqa: E402
from benchmark import scoring as sc  # noqa: E402
from benchmark import verify_images as vi  # noqa: E402

RELEASE = "https://github.com/bigr/gpt-image-2.5-benchmark/releases/download/dataset-v2/"
VARIANTS = analyze.VARIANTS
N_PER_VARIANT = 10


def image_outcome(
    prompt: dict[str, Any],
    key: str,
    truth: dict[str, Any],
    excluded: set[tuple[str, str]],
    ruled: dict[str, Any],
) -> dict[str, Any]:
    t = truth[key]
    failed: list[str] = []
    skipped: list[str] = []
    for it in prompt["items"]:
        if (prompt["id"], it["id"]) in excluded or it["id"] not in t["answers"]:
            skipped.append(it["id"])
            continue
        seen = t["answers"][it["id"]]
        if (it["expect"] == "present") != seen:
            failed.append(it["id"])
    return {
        "failed": failed,
        "skipped": skipped,
        "addition": t["has_addition"],
        "ruled": len(ruled.get(key, {})),
    }


def _short(text: str, n: int = 90) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def page(
    prompt: dict[str, Any],
    ds: dict[str, Any],
    truth: dict[str, Any],
    excluded: set[tuple[str, str]],
    ruled: dict[str, Any],
) -> str:
    pid = prompt["id"]
    items = {i["id"]: i for i in prompt["items"]}
    L = [f"# {pid}", "", f"[Gallery index](README.md) | test: **{prompt['test']}**", ""]
    L += [
        "<details><summary>Prompt</summary>",
        "",
        "```text",
        prompt["prompt"],
        "```",
        "",
        "</details>",
        "",
    ]
    L += ["Checklist (the person-corrected answers below refer to these item ids):", ""]
    for i in prompt["items"]:
        want = "must be visible" if i["expect"] == "present" else "must NOT be visible"
        mark = " (excluded from every score)" if (pid, i["id"]) in excluded else ""
        L.append(f"- `{i['id']}` ({want}): {i['text']}{mark}")
    L.append("")
    for v in VARIANTS:
        L += [f"## {analyze.SHORT[v]}", ""]
        rows: list[str] = []
        for r in range(2):
            thumbs, notes = [], []
            for c in range(5):
                n = r * 5 + c
                key = f"{pid}/{v}/{n}"
                name = f"{v}-{n}"
                o = image_outcome(prompt, key, truth, excluded, ruled)
                png = RELEASE + vi.flat_name(f"{pid}/{name}.png")
                thumbs.append(f"[![{name}](../thumbnails/{pid}/{name}.webp)]({png})")
                bits = [
                    "all items OK"
                    if not o["failed"]
                    else "failed: " + ", ".join(f"`{f}`" for f in o["failed"])
                ]
                bits.append("addition: yes" if o["addition"] else "addition: none")
                if o["ruled"]:
                    bits.append(f"{o['ruled']} human ruling(s)")
                notes.append(f"**{n}**: " + "; ".join(bits))
            rows.append("| " + " | ".join(thumbs) + " |")
            rows.append("| " + " | ".join(notes) + " |")
        L += [rows[0], "|---|---|---|---|---|", rows[1], rows[2], rows[3], ""]
        L += ["Click a thumbnail for the full-resolution PNG (release asset).", ""]
        L += [
            "Additions named by the reference reading (a model reading; the yes/no above is "
            "person-corrected):",
            "",
        ]
        for n in range(N_PER_VARIANT):
            key = f"{pid}/{v}/{n}"
            names = [s for s in ds["reference"].get(key, {}).get("inventions", []) if str(s).strip()]
            L.append(f"- **{n}**: " + ("; ".join(names) if names else "none listed"))
        L.append("")
    L += [
        "Items: " + "; ".join(f"`{k}` = {_short(v['text'])}" for k, v in items.items()),
        "",
    ]
    return "\n".join(L) + "\n"


def index(prompts: list[dict[str, Any]], summary: dict[str, dict[str, Any]]) -> str:
    L = [
        "# Gallery",
        "",
        "All 300 images of the benchmark, one page per prompt (15 pages). Thumbnails are 512 px WebP",
        "(CC BY 4.0); each links to the full-resolution PNG in the `dataset-v2` release. Outcomes are",
        "from the corrected reference: the model reading overridden by the author's rulings.",
        "See [`../docs/DATA.md`](../docs/DATA.md).",
        "",
        "| Prompt | Test | sunburst: images with a failed item / with an addition | flare: same |",
        "|---|---|---|---|",
    ]
    for p in prompts:
        cells = []
        for v in VARIANTS:
            s = summary[p["id"]][v]
            cells.append(f"{s['failed']} / {s['addition']} (of {N_PER_VARIANT})")
        L.append(f"| [{p['id']}]({p['id']}.md) | {p['test']} | {cells[0]} | {cells[1]} |")
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "gallery")
    args = ap.parse_args(argv)
    data = ROOT / "data"
    ds = analyze.load_dataset(data)
    excluded = sc.excluded_set(ds["exclusions"])
    ruled = sc.merge_rounds(ds["rounds"])
    truth = sc.build_truth(ds["reference"], ruled, ds["unknown"])
    args.out.mkdir(parents=True, exist_ok=True)
    prompts = list(ds["prompts"].values())
    summary: dict[str, dict[str, Any]] = {}
    for p in prompts:
        summary[p["id"]] = {}
        for v in VARIANTS:
            outs = [
                image_outcome(p, f"{p['id']}/{v}/{n}", truth, excluded, ruled)
                for n in range(N_PER_VARIANT)
            ]
            summary[p["id"]][v] = {
                "failed": sum(bool(o["failed"]) for o in outs),
                "addition": sum(o["addition"] for o in outs),
            }
        (args.out / f"{p['id']}.md").write_text(
            page(p, ds, truth, excluded, ruled), encoding="utf-8"
        )
    (args.out / "README.md").write_text(index(prompts, summary), encoding="utf-8")
    print(f"wrote {len(prompts) + 1} pages to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
