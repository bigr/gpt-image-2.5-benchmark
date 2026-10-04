"""Pure scoring functions. No file access, no network, no randomness.

Vocabulary
----------
image key   "<prompt id>/<variant>/<index>", e.g. "retention-25/gpt-image-2.5-flare/0"
reading     {"answers": {item id: bool}, "inventions": [str]} for one image
settlement  {image key: {item id or "inventions": bool}}; the pseudo-item "inventions"
            answers "does the image contain at least one unrequested addition?"
truth       {image key: {"answers": {item id: bool}, "has_addition": bool}}
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

Reading = Mapping[str, Any]
Settlement = Mapping[str, Mapping[str, bool]]

ADDITIONS = "inventions"  # item id the human rounds use for the per-image additions question


# --------------------------------------------------------------------------- readings


def has_addition(reading: Reading) -> bool:
    """True when the reading names at least one non-blank addition."""
    return any(str(s).strip() for s in reading.get("inventions", []))


def addition_count(reading: Reading) -> int:
    return sum(1 for s in reading.get("inventions", []) if str(s).strip())


def answers(reading: Reading) -> dict[str, bool]:
    return {str(k): bool(v) for k, v in reading.get("answers", {}).items()}


# --------------------------------------------------------------------------- human rounds


def merge_rounds(rounds: Sequence[Settlement]) -> dict[str, dict[str, bool]]:
    """Apply settlement rounds in the order given; a later round overrides an earlier one per item."""
    merged: dict[str, dict[str, bool]] = {}
    for rnd in rounds:
        for key, items in rnd.items():
            merged.setdefault(key, {}).update({str(i): bool(v) for i, v in items.items()})
    return merged


def build_truth(
    reference: Mapping[str, Reading],
    settlement: Settlement,
    unknown: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Reference reading, overridden by the human settlement.

    ``unknown`` maps an image key to item ids whose answer is unknown. Those keys are REMOVED
    from ``answers`` (never stored as None or False), so every scorer skips them.
    """
    truth: dict[str, dict[str, Any]] = {}
    for key in sorted(set(reference) | set(settlement)):
        base = reference.get(key, {})
        ans = answers(base)
        addition = has_addition(base)
        for item, value in settlement.get(key, {}).items():
            if item == ADDITIONS:
                addition = bool(value)
            else:
                ans[item] = bool(value)
        for item in (unknown or {}).get(key, ()):
            ans.pop(item, None)
        truth[key] = {"answers": ans, "has_addition": addition}
    return truth


# --------------------------------------------------------------------------- metrics


def confusion(pairs: Iterable[tuple[bool | None, bool | None]]) -> dict[str, int]:
    """Counts over (predicted, true) pairs; a pair with an unknown side is skipped."""
    c = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for pred, true in pairs:
        if pred is None or true is None:
            continue
        if pred and true:
            c["tp"] += 1
        elif pred:
            c["fp"] += 1
        elif true:
            c["fn"] += 1
        else:
            c["tn"] += 1
    return c


def _ratio(num: int, den: int) -> float | None:
    return num / den if den else None


def metrics(c: Mapping[str, int]) -> dict[str, Any]:
    """Precision, recall, specificity, accuracy; None where the denominator is zero.

    precision = tp / (tp + fp); recall = tp / (tp + fn);
    specificity = tn / (tn + fp); accuracy = (tp + tn) / n.
    """
    tp, fp, tn, fn = c["tp"], c["fp"], c["tn"], c["fn"]
    return {
        "n": tp + fp + tn + fn,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "specificity": _ratio(tn, tn + fp),
        "accuracy": _ratio(tp + tn, tp + fp + tn + fn),
    }


def always_yes(truth_values: Iterable[bool | None]) -> dict[str, Any]:
    """The baseline reader that never looks at an image and answers "yes" every time."""
    return metrics(confusion((True, t) for t in truth_values))


def excluded_set(exclusions: Mapping[str, Any]) -> set[tuple[str, str]]:
    return {(e["prompt"], e["item"]) for e in exclusions["excluded_items"]}


def prompt_of(key: str) -> str:
    return key.split("/")[0]


def checklist_pairs(
    prompts: Mapping[str, Mapping[str, Any]],
    reader: Mapping[str, Reading],
    truth: Mapping[str, Mapping[str, Any]],
    excluded: set[tuple[str, str]],
) -> list[tuple[bool | None, bool | None]]:
    """(reader answer, true answer) for every checklist item that is not excluded.

    Positive means "the item is visible", also for the "must be absent" items.
    """
    out: list[tuple[bool | None, bool | None]] = []
    for key in sorted(truth):
        pid = prompt_of(key)
        got = answers(reader[key])
        for item in prompts[pid]["items"]:
            if (pid, item["id"]) in excluded:
                continue
            out.append((got.get(item["id"]), truth[key]["answers"].get(item["id"])))
    return out


def addition_pairs(
    reader: Mapping[str, Reading], truth: Mapping[str, Mapping[str, Any]]
) -> list[tuple[bool | None, bool | None]]:
    """(reader says "has an addition", truth says so) for every image: one binary question each."""
    return [(has_addition(reader[k]), truth[k]["has_addition"]) for k in sorted(truth)]


# --------------------------------------------------------------------------- image model results


def image_model_rates(
    prompts: Mapping[str, Mapping[str, Any]],
    truth: Mapping[str, Mapping[str, Any]],
    excluded: set[tuple[str, str]],
) -> dict[str, dict[tuple[Any, ...], list[int]]]:
    """[count, denominator] per (test, number of listed elements, variant), against the truth.

    required   [items that pass, items counted] for items that must be present
    forbidden  [forbidden things drawn, items counted] for items that must be absent
    additions  [images with an addition, images]

    Excluded items and items with an unknown answer are skipped in numerator and denominator.
    """
    req: dict[tuple[Any, ...], list[int]] = defaultdict(lambda: [0, 0])
    forb: dict[tuple[Any, ...], list[int]] = defaultdict(lambda: [0, 0])
    adds: dict[tuple[Any, ...], list[int]] = defaultdict(lambda: [0, 0])
    for key, val in truth.items():
        pid, variant, _ = key.split("/")
        p = prompts[pid]
        group = (p["test"], p.get("elements"), variant)
        for item in p["items"]:
            if (pid, item["id"]) in excluded:
                continue
            got = val["answers"].get(item["id"])
            if got is None:
                continue
            bucket = req if item["expect"] == "present" else forb
            bucket[group][1] += 1
            bucket[group][0] += int(got)
        adds[group][1] += 1
        adds[group][0] += int(val["has_addition"])
    return {"required": dict(req), "forbidden": dict(forb), "additions": dict(adds)}


def mean_additions_per_image(
    prompts: Mapping[str, Mapping[str, Any]], reference: Mapping[str, Reading]
) -> dict[tuple[str, str], float]:
    """Average number of additions the reference reading listed, per (test, variant)."""
    acc: dict[tuple[str, str], list[int]] = defaultdict(list)
    for key, val in reference.items():
        pid, variant, _ = key.split("/")
        acc[(prompts[pid]["test"], variant)].append(addition_count(val))
    return {k: sum(v) / len(v) for k, v in acc.items()}


# --------------------------------------------------------------------------- settled rows


def settled_rows(settlement: Settlement, excluded: set[tuple[str, str]]) -> list[tuple[str, str]]:
    """Every (image, item) a human ruled on in any round, minus excluded items."""
    return [
        (key, item)
        for key, items in sorted(settlement.items())
        for item in sorted(items)
        if (prompt_of(key), item) not in excluded
    ]


def _reader_answer(reading: Reading, key: str, item: str) -> bool | None:
    if item == ADDITIONS:
        return has_addition(reading)
    return answers(reading).get(item)


def settled_agreement(
    reader: Mapping[str, Reading],
    truth: Mapping[str, Mapping[str, Any]],
    rows: Sequence[tuple[str, str]],
    skip_unknown: bool = False,
) -> tuple[int, int]:
    """(agreeing rows, counted rows) of a reader against the truth on the settled rows.

    With ``skip_unknown`` a row whose true answer was removed (unknown) is not counted; by default it counts as a disagreement.
    """
    ok = n = 0
    for key, item in rows:
        want = truth[key]["has_addition"] if item == ADDITIONS else truth[key]["answers"].get(item)
        if want is None and skip_unknown:
            continue
        n += 1
        ok += _reader_answer(reader[key], key, item) == want
    return ok, n
