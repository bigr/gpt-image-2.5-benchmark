# image-generation-benchmark

Data and offline scoring code for the article
**[What gpt-image-2.5 draws when you describe everything, and which model can check it](https://bigr.cz/gpt-image-2-5-benchmark/)**
(300 images, three judge models, one human).

> Working repository name; final name, account and licences are still to be confirmed by the author
> (see [`LICENSE-PROPOSAL.md`](LICENSE-PROPOSAL.md)). Nothing here is published yet.

This repository lets you recompute every table of the article from the stored answers, without API
keys, a database or network access, and inspect exactly which answers were given by a model and which
were settled by a person.

**Dataset revision: 2** (human settlement rounds 1-5). It matches the revised version of the article.
Earlier rounds are part of this data (they are applied first), but earlier published numbers are not
reproduced here; later rounds re-checked the reference, and that is part of the finding.

## What was tested

- 15 prompts x 2 variants of `gpt-image-2.5` (`sunburst`, `flare`) x 10 images = **300 images**
  (quality "low", portrait 1088x1936, one image per call).
- Three tests: *how much it keeps* (a watermill yard with 8, 15 or 25 listed elements), *specific
  details against the stereotype* (six period or scientific scenes), *saying "no"* (three subjects,
  each written with an explicit "No X" and described positively only).
- Every prompt has a yes/no checklist. Each image also gets one open question: did the model draw
  anything nobody asked for?
- Three judge models answered the checklist for every image at low reasoning effort: `gpt-6.1-sol`,
  `gpt-6-sol`, `gpt-6-luna`. One extra run: `gpt-6.1-sol` at medium effort (one sentence in the article).
- A **reference reading** by Claude Opus 5.5 at medium effort, one image at a time, same checklist.
- Wherever any judge disagreed with the reference, a person settled the question **blind**: one large
  image, one question, nobody's answers shown. Later rounds re-asked questions in both directions.

## Reproduce the numbers

Requires Python 3.10 or newer, standard library only.

```sh
python -m benchmark.analyze --data data/ --output results/
python -m unittest discover -s tests -t .
```

`analyze` never modifies `data/` (it refuses to write inside it); it writes `results/summary.json` and
`results/tables.md`. The committed `results/` is the output of that command on the committed data.

## What the reference is, and is not

The reference is a **model reading corrected by a person**. It is not a complete, independent human
annotation of all answers. Where the person did not rule, Claude's reading stands. The settled rows are
a selection of hard cases (every disagreement between a judge and the reference, plus re-checks), so
agreement rates on them are not a ranking of models. See [`docs/DATA.md`](docs/DATA.md) for how the
reference is built, step by step.

## Definitions

- **Checklist** (1,758 scored answers): every (image, item) pair. Positive means "the item is visible",
  also for items that must be *absent*. Precision = TP/(TP+FP), recall = TP/(TP+FN),
  specificity = TN/(TN+FP). Pairs with a missing answer on either side are skipped in numerator and
  denominator.
- **Additions** (300 images): **one binary question per image**: does it contain at least one unrequested
  addition? Accuracy = (TP+TN)/300, precision, recall as above. This is not a score for finding every
  addition, nor for each named addition being right.
- **Always-yes baseline**: a reader that never looks and answers "yes" to the additions question. 279 of
  300 images contain an addition, so it scores 93.0% accuracy.
- **Image model pass rates**: share of required items drawn as written, per variant and test, against
  the corrected reference. Excluded and unknown items are skipped. `results/summary.json` gives the numerator
  and denominator of every figure.
- **Settled-row agreement** (273 rows): every question a person ruled on, excluded items included, and a
  row whose true answer is unknown counted as a disagreement (this is how the article counted it).
  `results/` also contains a stricter variant that drops excluded and unknown rows.
- Percentages are rounded to one decimal place.

## Exclusions

- `period-italian-town-10c / squat-tower` ("a low, squat bell tower": low compared to what?) and
  `negpos-flywheel-positive / negated-thing-appears` ("a flywheel": is a solid crank disc one?), because
  the person settling could not decide consistently. They are skipped in all checklist and pass-rate
  scores.
- `e04` ("three flour sacks stacked beside the door") on two images where the person could not tell
  three sacks from four: the answer is removed from the reference (unknown, not "false") and skipped
  everywhere. In total 1,760 - 2 = 1,758 scored answers.

## Images

The 300 PNG files (about 1.19 GB) are **not** in git. `data/image-manifest.csv` lists filename, SHA-256
and size of each. The plan for a release archive is in [`docs/image-release-plan.md`](docs/image-release-plan.md).
Until the archive exists, you can recompute all tables from the stored answers, but you cannot
independently judge all 300 images yourself.

## Limits

15 prompts, one illustration style, 10 images per prompt and variant, one person writing the checklist
and settling disagreements, and a shared model reference behind every score. A number here describes this
sample, not a guarantee elsewhere. A new generation run will not reproduce these images or exact
percentages; the offline recomputation does.

## Cost

The original API calls cost USD 7.66 (USD 1.71 for the images, USD 5.95 for the judges, including USD 1.33
for one judge run that crashed and was repeated). The medium-effort rerun, the reference reading and
human time are **not** included.

## Discussion and issues

- Questions, methodology comments, disagreements with an image rating, ideas for further tests:
  GitHub Discussions (link to be added after publication).
- Concrete errors in the data or code (wrong number, wrong answer for a named image, a failing test):
  Issues. Please quote the image key, for example `retention-25/gpt-image-2.5-flare/0`.
