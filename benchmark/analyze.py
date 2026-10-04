"""Recompute every table of the benchmark from the stored answers.

    python -m benchmark.analyze --data data/ --output results/

Reads ``--data`` (never modified), writes ``summary.json`` and ``tables.md`` into ``--output``.
No network, no API keys. The output directory must not be inside the data directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import scoring as sc

VARIANTS = ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare")
SHORT = {"gpt-image-2.5-sunburst": "sunburst", "gpt-image-2.5-flare": "flare"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dataset(data: Path) -> dict[str, Any]:
    index = _load(data / "rounds.json")
    prompts = {p["id"]: p for p in _load(data / index["prompts"])["prompts"]}
    exclusions = _load(data / index["exclusions"])
    unknown_file = data / exclusions["unknown_answers"]["images_file"]
    unknown = {k: [exclusions["unknown_answers"]["item"]] for k in _load(unknown_file)}
    return {
        "prompts": prompts,
        "reference": _load(data / index["reference"]),
        "rounds": [_load(data / f) for f in index["rounds"]],
        "exclusions": exclusions,
        "unknown": unknown,
        "judges": {n: _load(data / f)["readings"] for n, f in index["judges"].items()},
        "extra_judges": {n: _load(data / f)["readings"] for n, f in index["extra_judges"].items()},
    }


def _pct(x: float | None) -> float | None:
    return None if x is None else round(100 * x, 1)


def _rounded(m: dict[str, Any]) -> dict[str, Any]:
    return {k: (_pct(v) if isinstance(v, float) else v) for k, v in m.items()}


def analyze(ds: dict[str, Any]) -> dict[str, Any]:
    prompts = ds["prompts"]
    excluded = sc.excluded_set(ds["exclusions"])
    settlement = sc.merge_rounds(ds["rounds"])
    truth = sc.build_truth(ds["reference"], settlement, ds["unknown"])
    out: dict[str, Any] = {}

    readers = {**ds["judges"], **ds["extra_judges"]}
    out["checklist"] = {}
    out["additions"] = {}
    for name, reading in readers.items():
        c = sc.metrics(sc.confusion(sc.checklist_pairs(prompts, reading, truth, excluded)))
        a = sc.metrics(sc.confusion(sc.addition_pairs(reading, truth)))
        out["checklist"][name] = _rounded(c)
        out["additions"][name] = _rounded(a)
    out["additions"]["always yes"] = _rounded(
        sc.always_yes(t["has_addition"] for t in truth.values())
    )

    rates = sc.image_model_rates(prompts, truth, excluded)
    gen: dict[str, Any] = {}
    for v in VARIANTS:
        s = SHORT[v]
        g: dict[str, Any] = {}
        for n in (8, 15, 25):
            ok, den = rates["required"][("how-much-it-keeps", n, v)]
            g[f"elements_{n}"] = {"passed": ok, "counted": den, "pct": _pct(ok / den)}
        ok, den = rates["required"][("specific-details", None, v)]
        g["specific_details"] = {"passed": ok, "counted": den, "pct": _pct(ok / den)}
        # the single forbidden item of a specific-details prompt is "a landmark was substituted"
        drawn, den = rates["forbidden"][("specific-details", None, v)]
        g["landmark_substituted"] = {"drawn": drawn, "counted": den}
        drawn, den = rates["forbidden"][("saying-no", None, v)]
        g["forbidden_thing_drawn"] = {"drawn": drawn, "counted": den}
        w, n_img = rates["additions"][("specific-details", None, v)]
        g["period_images_with_additions"] = {"with_additions": w, "images": n_img}
        gen[s] = g
    out["image_model"] = gen
    means = sc.mean_additions_per_image(prompts, ds["reference"])
    out["reference_additions_per_image"] = {
        SHORT[v]: {t: round(means[(t, v)], 1) for t in sorted({k[0] for k in means})}
        for v in VARIANTS
    }

    # Published definition: every (image, item) any round ruled on, the two excluded items
    # INCLUDED, and a row whose true answer is unknown counted as a disagreement.
    # The stricter variant drops excluded items and unknown rows from the count.
    readers_all = {"reference": ds["reference"], **readers}
    rows_all = sc.settled_rows(settlement, set())
    rows_strict = sc.settled_rows(settlement, excluded)

    def agree(rows: list[tuple[str, str]], skip: bool) -> dict[str, Any]:
        res = {n: sc.settled_agreement(r, truth, rows, skip) for n, r in readers_all.items()}
        return {n: {"agree": ok, "counted": d, "pct": _pct(ok / d)} for n, (ok, d) in res.items()}

    out["settled_rows"] = {
        "rows": len(rows_all),
        "agreement": agree(rows_all, False),
        "strict": {"rows": len(rows_strict), "agreement": agree(rows_strict, True)},
    }
    out["counts"] = {
        "images": len(truth),
        "images_with_addition": sum(t["has_addition"] for t in truth.values()),
        "checklist_answers_scored": out["checklist"]["gpt-6.1-sol"]["n"],
    }
    return out


def _f(x: Any) -> str:
    return "n/a" if x is None else f"{x:.1f}%"


def render_tables(r: dict[str, Any]) -> str:
    L = ["# Recomputed tables", ""]
    L += [
        f"Images: {r['counts']['images']}; with an addition in the corrected reference: "
        f"{r['counts']['images_with_addition']}; checklist answers scored: "
        f"{r['counts']['checklist_answers_scored']}.",
        "",
    ]
    L += ["## Image model", "", "| | sunburst | flare |", "|---|---|---|"]
    g = r["image_model"]
    for label, key in (
        ("8 elements", "elements_8"),
        ("15 elements", "elements_15"),
        ("25 elements", "elements_25"),
        ("Specific details", "specific_details"),
    ):
        L.append(f"| {label} | {_f(g['sunburst'][key]['pct'])} | {_f(g['flare'][key]['pct'])} |")
    for label, key, a, b in (
        ("Landmark substituted", "landmark_substituted", "drawn", "counted"),
        ("Forbidden thing drawn", "forbidden_thing_drawn", "drawn", "counted"),
        (
            "Period images with additions",
            "period_images_with_additions",
            "with_additions",
            "images",
        ),
    ):
        L.append(
            f"| {label} | "
            + " | ".join(f"{g[s][key][a]} of {g[s][key][b]}" for s in ("sunburst", "flare"))
            + " |"
        )
    L += [
        "",
        "## Checklist (positive = visible)",
        "",
        "| Reader | n | Precision | Recall | Specificity |",
        "|---|---|---|---|---|",
    ]
    for n, m in r["checklist"].items():
        L.append(
            f"| {n} | {m['n']} | {_f(m['precision'])} | {_f(m['recall'])} | {_f(m['specificity'])} |"
        )
    L += [
        "",
        "## Additions (one binary question per image)",
        "",
        "| Reader | Accuracy | Precision | Recall |",
        "|---|---|---|---|",
    ]
    for n, m in r["additions"].items():
        L.append(f"| {n} | {_f(m['accuracy'])} | {_f(m['precision'])} | {_f(m['recall'])} |")
    s = r["settled_rows"]
    L += [
        "",
        f"## Agreement on the {s['rows']} settled rows (the definition used in the article)",
        "",
        "| Reader | Agree | Counted | % |",
        "|---|---|---|---|",
    ]
    for n, a in s["agreement"].items():
        L.append(f"| {n} | {a['agree']} | {a['counted']} | {_f(a['pct'])} |")
    st = s["strict"]
    L += [
        "",
        f"## Stricter variant: {st['agreement']['reference']['counted']} questions "
        "(excluded items and unknown rows dropped)",
        "",
        "| Reader | Agree | Counted | % |",
        "|---|---|---|---|",
    ]
    for n, a in st["agreement"].items():
        L.append(f"| {n} | {a['agree']} | {a['counted']} | {_f(a['pct'])} |")
    return "\n".join(L) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--output", type=Path, default=Path("results"))
    args = ap.parse_args(argv)
    data, out = args.data.resolve(), args.output.resolve()
    if out == data or data in out.parents:
        print("refusing to write inside the data directory", file=sys.stderr)
        return 2
    result = analyze(load_dataset(data))
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    text = render_tables(result)
    (out / "tables.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
