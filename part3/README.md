# Part 3: Counting beyond storybook pictures

Three vision judge configurations on two published counting datasets, scored against their original answer keys. No images from either dataset are redistributed here.

[Article](https://bigr.cz/countqa-holocount-vision-judges/) · [Reproduced tables](results/tables.md) · [Full report](results/report.json)

## Reproduce the scores (offline, no dependencies)

From the repository root, with Python 3.10 or newer:

```sh
python3 part3/analyze.py
python3 part3/analyze.py --out /tmp/counting-results
python3 -m unittest discover -s part3/tests -v
```

The first command only reads the bundled data and prints tables. The second also writes `report.json`, `errors.json` and `tables.md` into the requested output directory. Neither uses API keys, a database, a model service or network access.

Files under `data/`:

- `plan.json`: seed **20261013**, exact ordered question selections.
- `countqa.manifest.json`, `holocount.manifest.json`: dataset identifiers, original questions and integer answer keys. `image` is a dataset identifier, never a local filesystem path.
- `readings/*.jsonl`: six complete judge runs; one question per line, including count, note, submitted-image dimensions and recorded dollar cost.
- `protocol.json`: exact system instruction, requested configurations and discarded probe cost.
- `image-sha256.json`: **3,481 SHA-256 checksums of the original image bytes** (1,001 CountQA and 2,480 HoloCount), keyed by dataset filename. Checksums refer to original files, not the two JPEG-recompressed API inputs.

`results/` is derived from those inputs, not an alternative source of truth. The analyzer rejects duplicate answers, missing planned answers, split-photo CountQA selections and nonmatching HoloCount samples.

## Fetch and verify the original datasets

Only fetching CountQA needs `pyarrow`; scoring does not. Use a separate virtual environment:

```sh
python3 -m venv /tmp/counting-fetch-env
/tmp/counting-fetch-env/bin/pip install -r part3/requirements-fetch.txt
/tmp/counting-fetch-env/bin/python part3/fetch.py --out /tmp/counting-datasets
```

This downloads public data directly from Hugging Face at immutable revisions:

| Dataset | Revision | Selection |
|---|---|---|
| [Jayant-Sravan/CountQA](https://huggingface.co/datasets/Jayant-Sravan/CountQA) | `f92cc6fe46542c61e2916e3d2ae9a911e2216b1a` | test split; 13 parquet shards |
| [MM-MVR/HoloCount](https://huggingface.co/datasets/MM-MVR/HoloCount) | `f44cfe591e8f7e64b63a2fb080b98bffa10b45aa` | `data/metadata.jsonl` and its original image files |

`fetch.py` compares **every question, key, row identifier and selected metadata field**, and every original image checksum, against the bundled manifests. It writes verified manifests under `--out`. An optional read-only `--cache` can reuse prior `countqa/raw/` parquet shards and `holocount/images/` files. In that case HoloCount images remain in the cache instead of being copied; their hashes are still checked. Use `--dataset countqa` or `--dataset holocount` to fetch just one.

The revisions were identified on 18 October 2026 and checked against the files used in the run: all 13 CountQA parquet files match the pinned Hugging Face LFS SHA-256 identifiers; all 2,480 HoloCount images match the pinned upstream Git/LFS blob identifiers. All 4,008 question/key pairs were re-extracted and verified. See [source verification](results/source-verification.json) and the [image checksum list](data/image-sha256.json).

The downloaded files remain outside the repository. Do not add them to a release or assume the dataset-level licence overrides third-party rights in individual images.

## What ran

| Judge label | Provider | Requested reasoning effort |
|---|---|---|
| `gpt-6.1-sol@low` | OpenAI Responses API | low |
| `gpt-6-luna@low` | OpenAI Responses API | low |
| `claude-haiku-5.5@high` | OpenRouter, `anthropic/claude-haiku-5.5` | high |

One image and one verbatim dataset question per call; no tools, retrieval, conversation history or answer-key hint. Structured output: `{"count": <integer>, "note": "<short explanation>"}`.

System instruction, exactly:

> You answer ONE counting question about ONE image. Count what is visible in the pixels; count every instance anywhere in the image, never answer from what such a scene usually holds. If none is visible the count is 0. Return an integer count and a short note.

CountQA: Luna and Haiku answered all **1,528 questions**. Sol answered **400 questions from 258 whole photos**, all questions of each selected photo, as a prefix of the seeded shuffled photo order. The shared comparisons use those same 400 for all three. HoloCount: the same **300 questions** for every judge, spanning all **20 subsets**, with 8–27 questions per subset. Each configuration ran once.

Original image bytes were used except for **5 of the 4,356 scored calls**: two files exceeded a local 4.5 MB limit and were JPEG-recompressed at unchanged pixel dimensions. These transformations are recorded in `image_sent`. The reference image checksums remain those of the original dataset images.

Costs: the scored run was **$7.9301780**, plus **$0.1680163** for a discarded 60-call probe, totalling **$8.0981943 ($8.10)**. The probe answers are not part of this release and are not scored. Its stated cost is included as a separate constant; the analyzer recomputes all scored-run costs from the six journals. Costs are recorded charges, not estimates from today's token rates.

## Interpretation and limits

- Exact match and inclusive ±1 are measured against the published keys; no answer was relabelled. The 16 shared disagreements are candidates to inspect, not 16 proven key errors.
- These are selected model **configurations**, not each model's best possible performance. Effort labels are not standardized across vendors; Luna medium was not retested here.
- The prompt is ours, not a reproduction of the papers' protocols. “Every instance anywhere” may conflict with regional/foreground restrictions or encourage counting a depicted object as well as a physical one.
- Wilson intervals operate at the question level and do not account for multiple questions from one photo or variation between repeated runs.
- HoloCount scores here are question-weighted on a 300-question sample. The paper gives equal weight to its 20 subsets; its macro ranking is not directly comparable.
- HoloCount includes synthetic and altered images as well as photographs. The change from part 2 does not isolate picture style from prompt, question distribution, count range or answer-key differences.
- Other published runs may use different prompts, samples, maximum effort and tools. They are context, not controlled measurements of the gain from changing one setting.

## Licences and attribution

Code in this folder: **MIT**, see the repository's [LICENSE](../LICENSE).

Our judge responses, plan, protocol and derived reports: **CC BY 4.0**, attributed to Pavel Klinger. Judge responses are model-generated outputs. This does **not** relicense the original benchmark questions, answers or images.

CountQA questions and keys are attributed to **Jayant Sravan Tamarapalli, Rynaa Grover, Nilay Pande and Sahiti Yerramilli**, under the dataset's [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) declaration. HoloCount questions and keys are attributed to **Jinhong Deng, Limeng Qiao and Guanglu Wan**, under its dataset card's CC BY 4.0 declaration. The manifests select fields and replace local image paths with dataset identifiers; the questions and answers are preserved. The original datasets and underlying images remain subject to their respective authors' licences and third-party rights.

Dataset sources: [CountQA](https://huggingface.co/datasets/Jayant-Sravan/CountQA), [HoloCount](https://huggingface.co/datasets/MM-MVR/HoloCount). No benchmark images are included in this folder or a release.

## References

- Tamarapalli, J. S., Grover, R., Pande, N., and Yerramilli, S. (2025). *CountQA: How Well Do MLLMs Count in the Wild?* [arXiv:2508.06585](https://arxiv.org/abs/2508.06585).
- Deng, J., Qiao, L., and Wan, G. (2026). *HoloCount: A Holistic Visual Counting Benchmark for MLLMs.* [arXiv:2607.06420](https://arxiv.org/abs/2607.06420).
