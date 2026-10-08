# Part 2 reproduced results

Percentages use exact matches against the corrected reference. Haiku settings are configurations, not repeat trials.

## Counting: part 1 and sacks

| Model / setting | All questions | Sacks |
| --- | --- | --- |
| gpt-6.1-sol | 96.3% (418/434) | 77.6% (45/58) |
| gpt-6-luna | 91.5% (397/434) | 46.6% (27/58) |
| gpt-6-luna.low-rep1 | 92.6% (402/434) | 50.0% (29/58) |
| gpt-6-luna.low-rep2 | 92.4% (401/434) | 50.0% (29/58) |
| gpt-6-luna@medium | 91.5% (397/434) | 46.6% (27/58) |
| gpt-6-luna@high | 91.2% (396/434) | 43.1% (25/58) |
| claude-haiku-5.5 | 88.9% (386/434) | 27.6% (16/58) |
| claude-haiku-5.5@low | 88.9% (386/434) | 29.3% (17/58) |
| claude-haiku-5.5@medium | 89.2% (387/434) | 29.3% (17/58) |
| claude-haiku-5.5@high | 88.5% (384/434) | 25.9% (15/58) |

## Who can count: new set and effort sweeps

| Model / setting | All | 2-3 | 5-7 | 10 | 15 | Separate | Overlap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-6.1-sol | 96.5% (139/144) | 100.0% (48/48) | 95.8% (46/48) | 91.7% (22/24) | 95.8% (23/24) | 100.0% (72/72) | 93.1% (67/72) |
| gpt-6-luna | 89.6% (129/144) | 100.0% (48/48) | 93.8% (45/48) | 79.2% (19/24) | 70.8% (17/24) | 94.4% (68/72) | 84.7% (61/72) |
| gpt-6-luna.low-rep1 | 89.6% (129/144) | 100.0% (48/48) | 89.6% (43/48) | 83.3% (20/24) | 75.0% (18/24) | 95.8% (69/72) | 83.3% (60/72) |
| gpt-6-luna.low-rep2 | 90.3% (130/144) | 100.0% (48/48) | 91.7% (44/48) | 91.7% (22/24) | 66.7% (16/24) | 94.4% (68/72) | 86.1% (62/72) |
| gpt-6-luna@medium | 94.4% (136/144) | 100.0% (48/48) | 95.8% (46/48) | 87.5% (21/24) | 87.5% (21/24) | 100.0% (72/72) | 88.9% (64/72) |
| gpt-6-luna@high | 95.1% (137/144) | 100.0% (48/48) | 95.8% (46/48) | 87.5% (21/24) | 91.7% (22/24) | 100.0% (72/72) | 90.3% (65/72) |
| claude-haiku-5.5 | 86.8% (125/144) | 100.0% (48/48) | 87.5% (42/48) | 75.0% (18/24) | 70.8% (17/24) | 86.1% (62/72) | 87.5% (63/72) |
| claude-haiku-5.5@low | 77.1% (111/144) | 100.0% (48/48) | 79.2% (38/48) | 66.7% (16/24) | 37.5% (9/24) | 80.6% (58/72) | 73.6% (53/72) |
| claude-haiku-5.5@medium | 84.7% (122/144) | 100.0% (48/48) | 85.4% (41/48) | 70.8% (17/24) | 66.7% (16/24) | 83.3% (60/72) | 86.1% (62/72) |
| claude-haiku-5.5@high | 92.4% (133/144) | 100.0% (48/48) | 85.4% (41/48) | 91.7% (22/24) | 91.7% (22/24) | 93.1% (67/72) | 91.7% (66/72) |

## Generator fidelity

| Requested / layout | Exact |
| --- | --- |
| 2 | 100.0% (24/24) |
| overlap | 77.8% (56/72) |
| separate | 94.4% (68/72) |
| 3 | 100.0% (24/24) |
| 5 | 95.8% (23/24) |
| 7 | 91.7% (22/24) |
| 10 | 83.3% (20/24) |
| 15 | 45.8% (11/24) |

## What does not belong

| Model / setting | Planted | Generator-added | False alarms | Rejected / adjudicated |
| --- | --- | --- | --- | --- |
| gpt-6.1-sol | 100.0% (48/48) | 62.5% (5/8) | 17.5% (7/40) | 11.6% (8/69) |
| gpt-6-luna | 97.9% (47/48) | 0.0% (0/8) | 12.5% (5/40) | 24.6% (15/61) |
| gpt-6.1-sol@medium | 100.0% (48/48) | 62.5% (5/8) | 17.5% (7/40) | 11.8% (8/68) |
| claude-haiku-5.5 | 91.7% (44/48) | 37.5% (3/8) | 17.5% (7/40) | 24.2% (16/66) |
| claude-haiku-5.5@low | 100.0% (48/48) | 12.5% (1/8) | 32.5% (13/40) | 30.7% (23/75) |
| claude-haiku-5.5@medium | 93.8% (45/48) | 37.5% (3/8) | 7.5% (3/40) | 11.7% (7/60) |
| claude-haiku-5.5@high | 91.7% (44/48) | 25.0% (2/8) | 17.5% (7/40) | 18.0% (11/61) |

## Claude as agents

| Agent | Exact |
| --- | --- |
| Claude Opus 5.5 (medium) | 97.2% (140/144) |
| Claude Sonnet 5.5 (low) | 96.5% (139/144) |
| Claude Haiku 4.5 (low) | 79.9% (115/144) |

## Costs of three scored tests

| Label | USD |
| --- | --- |
| claude-haiku-5.5 | 0.1257528 |
| claude-haiku-5.5@high | 0.1354248 |
| claude-haiku-5.5@low | 0.1197618 |
| claude-haiku-5.5@medium | 0.1255773 |
| gpt-6-luna | 0.0938379 |
| gpt-6-luna.low-rep1 | 0.0659866 |
| gpt-6-luna.low-rep2 | 0.0657936 |
| gpt-6-luna@high | 0.0764216 |
| gpt-6-luna@medium | 0.0720921 |
| gpt-6.1-sol | 1.8832880 |
| gpt-6.1-sol@medium | 0.5963660 |

Combined sol low + Haiku default: 7/8. With sol medium: 8/8.

Total including approximate probe cost: $4.64.
Probe and image costs are documented totals; raw probe usage is unavailable.
