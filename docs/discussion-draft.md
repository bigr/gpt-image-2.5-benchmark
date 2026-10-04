<!-- DRAFT for the main GitHub Discussions thread. Not posted. Category suggestion: General or Show and tell. -->

# Image-generation benchmark: results and methodology

I tested how faithfully gpt-image-2.5 follows long, specific prompts, and which model can check the
result. 15 prompts x 2 variants x 10 images = 300 images; three judge models; a reference reading by
Claude corrected by me, blind, over several rounds.

Article: https://bigr.cz/gpt-image-2-5-benchmark/

This repository has the prompts and checklists, every judge's answers, the reference reading, every
human round, the scoring code, and a manifest of the 300 images. One command recomputes all tables:

```sh
python -m benchmark.analyze --data data/ --output results/
```

What I would most like feedback on:

1. **Method.** Is a binary "any unrequested addition?" per image a sensible way to score addition
   detection? Is correcting a model reference by blind human rounds a fair reference, given that I
   settled the disagreements alone?
2. **Individual ratings.** If you disagree with the answer for a particular image or checklist item,
   say which (for example `retention-25/gpt-image-2.5-flare/0`, item `e04`) and what you see. The images
   are in the release archive.
3. **Checklist wording.** Items such as "a low, squat bell tower" and "a flywheel" could not be settled
   consistently and were excluded. Which other items read two ways?
4. **Next tests.** Counting and out-of-place objects are being prepared as a second part. Suggestions
   for prompts, models or scoring are welcome.

Known limits: 15 prompts, one illustration style, 10 images per prompt and variant, one person settling
disagreements, a shared model reference behind every score. A number here describes this sample, not a
general ranking.

Concrete errors (a wrong figure, a wrong answer for a named image, a failing test) are better as Issues;
everything else, here.
