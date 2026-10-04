# Data guide (dataset revision 2)

All files are UTF-8 JSON unless noted. Image keys have the form `<prompt id>/<variant>/<index>`, for
example `retention-25/gpt-image-2.5-flare/0` (index 0-9). The same key names the image file
`images/<prompt id>/<variant>-<index>.png` in the release archive.

## Files

| File | Content |
|---|---|
| `data/prompts.json` | The 15 prompts: id, test, full prompt text, checklist (item id, text, expected: `present` or `absent`) |
| `data/reference.json` | Reference reading of all 300 images: answers per item and a list of additions |
| `data/judges/<model>.json` | Reading of one judge model on all 300 images (low reasoning effort) |
| `data/judges/gpt-6.1-sol.medium.json` | The same judge at medium effort (one sentence in the article) |
| `data/human/human-round-N.json` | Human rulings, one file per round, `{image key: {item id: true/false}}` |
| `data/human/sacks-uncertain.json` | The two images whose `e04` answer is unknown (list of image keys) |
| `data/rounds.json` | Index: the order in which the human rounds are applied, plus pointers to the other files |
| `data/exclusions.json` | The two excluded items and the unknown-answer rule |
| `data/image-manifest.csv` | Filename, SHA-256 and size in bytes of each of the 300 PNG files |

A reading is `{"answers": {item id: bool}, "inventions": [text, ...]}`. `inventions` is the list of
"material things drawn that the prompt did not ask for"; the additions question is whether that list is
non-empty. In a human round, the pseudo-item `inventions` answers the additions question directly
(`true` = at least one addition is present).

## How the reference ("truth") is built

1. Start from `reference.json` (the model reading).
2. Apply the human rounds in the order listed in `data/rounds.json`; a later round overrides an earlier
   one per (image, item).
   - **1**: questions where any judge disagreed with the reference.
   - **2**: blind re-ask of the questions where the person had ruled *against* the reference.
   - **3**: clarifications of four answers.
   - **4**: blind re-ask of the questions where the person had ruled *for* the reference against the
     best judge, plus new questions that arose from the medium-effort rerun.
   - **4b**: one answer corrected after the person reported a misclick in round 4.
   - **5**: the item "three flour sacks stacked beside the door" (`e04`) was split into two questions,
     how many sacks and whether one lies on another. `human-round-5.json` is the *resulting* answer
     for `e04` on 58 images (exactly three sacks AND one lying on another). The two source
     measurements (a counting settlement and a separate "lies on another" settlement) are not
     shipped; they would only reproduce this file.
3. Remove the `e04` answer for the images in `sacks-uncertain.json`. The key is deleted; it is never
   stored as `false` or null. Every scorer skips an answer that is absent.
4. Exclusions (`exclusions.json`) are skipped when scoring.

Rounds are applied by `benchmark.scoring.merge_rounds` and `benchmark.scoring.build_truth`; those
functions are covered by `tests/test_scoring.py`.

## Names

The dataset keeps the model and variant names as they were used in the article (`gpt-image-2.5-sunburst`,
`gpt-image-2.5-flare`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-luna`). Prompt ids and item ids are unchanged
from the original run. Files were renamed as follows.

| Public file | Original role |
|---|---|
| `data/prompts.json` | the 15 prompts of the run, composed as Scene / Subject / Details / Constraints and checked against the prompts shown to the reference reader |
| `data/reference.json` | reference reading (Claude Opus 5.5, medium effort) |
| `data/judges/gpt-6.1-sol.json`, `gpt-6-sol.json`, `gpt-6-luna.json` | judge readings, low effort |
| `data/judges/gpt-6.1-sol.medium.json` | judge reading, medium effort |
| `data/human/human-round-1.json` ... `human-round-5.json`, `human-round-4b.json` | human rounds 1, 2, 3, 4, 4b, 5 |
| `data/human/sacks-uncertain.json` | the two unknown `e04` answers |

## Sanitization

Removed: per-call cost and token metadata, journal records, the readings of an all-blank image used as
a sanity check, internal run identifiers and paths, and the free-text notes the person attached to some
answers (omitted by default). Not changed: every answer, every image key, every item, every list of
additions. A test (`tests/test_reproduce.py::DataIntegrity`) fails if known internal strings appear in
`data/`.

## Test and item ids

Prompt ids: `retention-08`, `retention-15`, `retention-25` (watermill, nested lists of the first 8, 15
and 25 elements, items `e01`...`e25`), `period-*` (six specific-detail scenes; the last item of each,
`landmark-substituted`, must be absent), `negpos-<subject>-negative` (prompt contains an explicit "No X")
and `negpos-<subject>-positive` (prompt describes only what should be there); their single item
`negated-thing-appears` must be absent.
