# Part 2: same price, different eyes

Data and offline scoring for **[gpt-6-luna vs Claude Haiku 5.5: same price, different eyes](https://bigr.cz/luna-vs-haiku-5-5-vision-judges/)**, by Pavel Klinger, October 2026.

## Reproduce every result

Python 3.10+, standard library only. No API keys, network, database or model calls.
From the repository root:

```sh
python3 part2/analyze.py
python3 -m unittest discover -s part2/tests
```

Outputs: [`results/tables.md`](results/tables.md) and [`results/summary.json`](results/summary.json).
The tables include all raw numerators and denominators underlying the article's summary,
counting breakdown, effort comparisons, generator fidelity, misfits, agent readings and costs.
Input files are never modified; an output path inside `data/` is refused.

## Images

- 60 counting images reused from [part 1's dataset-v2 release](https://github.com/bigr/gpt-image-2.5-benchmark/releases/tag/dataset-v2).
- 144 new counting illustrations: six categories, six requested counts, two layouts and two images per cell.
- 96 misfit illustrations: eight settings, seeded/clean pairs and six images per setting variant.

Browse the [gallery](gallery.md). All 240 new full-resolution PNGs are individual assets of
[`dataset-part2`](https://github.com/bigr/gpt-image-2.5-benchmark/releases/tag/dataset-part2), plus
`images-part2.zip` and `SHA256SUMS`. The archive also contains the 144 original anonymous copies
used by the human reference reader. `anon/tasks.json` contains only anonymous filenames and
counting prompts; the separately published mapping in `data/anonymous-tally.json` reveals the
original keys, so do not consult that mapping during a blind reading.

```sh
python3 part2/verify_images.py /path/to/downloaded-assets
python3 part2/verify_images.py /path/to/extracted-zip --require-anon
```

## Reference and exclusions

This is a model reference corrected through selected human adjudications, not an independently
human-labelled dataset. The person decided presence/count; Claude matched paraphrases and
assessed historical plausibility from descriptions. Only objects some reader reported can be
scored. Historical ambiguity and shared reference errors remain limitations.

Counting reference: `counts_b.json` plus human rounds 1-4. Four specific ladder questions and
two uncertain sack questions are excluded everywhere, leaving 434 questions; the sack subset
has 58. New counting reference: `tally_b.json` plus human rounds 1-3. The final decision for
`tally-sheep-07-overlap/gpt-image-2.5-flare/0` is eight, an interpretation of an occluded animal.

Misfit reference applies rounds 1-11 in order. Exclusions are explicit `(image key, item)` pairs:
ambiguous village chimneys, longhouse knitting, a flowering plant, Egyptian mooring chains and
shelved book orientation. Knitting on another image can remain a scored false alarm. There are
eight confirmed generator-added misfit images and 40 clean negatives. Rejected-item rates use
only adjudicated items, not all phrases returned by a judge. `data/exclusions.json` is normative.

## Configurations are not repeats

sol and luna use the Responses API. Luna has three repeat runs at low plus medium/high runs.
Haiku 5.5 uses OpenRouter: default and explicitly requested low/medium/high effort. The four
Haiku configurations are different settings, not four repeated trials of one configuration.
Claude Opus/Sonnet/Haiku 4.5 agent readings are separate from single-call API judges; Opus's
reference reading has an advantage. No requested object count is disclosed in counting prompts.

The first Haiku tally result contains 125 initial calls and 19 queue calls repeated after a
format slip. The original `strict-v1` file preserves that initial run, where those 19 parsed
counts were empty. The scorer accepts `queue` and `queue: people` as the same identifier and
scores the numeric count normally. Fifteen of the 19 recovered counts match the final reference.
`strict-v1` is audit evidence, not a scored configuration.

## Cost audit

Scored judge calls total $3.3603025. The 19 discarded-format calls add $0.0071841; the other 125
strict-v1 rows are duplicates and are not billed again. Reasoning probes add approximately
$0.003 (raw token usage was not retained), generation is recorded as rounded totals of $1.27.
This reproduces the article's rounded $3.37 judges and $4.64 overall. Reference readings and
human time are excluded. Cost-based estimates of thinking are not direct reasoning-token counts.

## How this was made

Pavel Klinger designed the experiment, supplied prompts, adjudicated selected disagreements,
reviewed the analysis and wrote/edited the article. AI tools assisted with code and analysis.
This export was independently checked against the reviewed results, including exclusions,
format recovery and differences between repeated trials and effort configurations.

Code: MIT, under the repository's `LICENSE`. Images/data: CC BY 4.0, under `LICENSE-DATA`.
