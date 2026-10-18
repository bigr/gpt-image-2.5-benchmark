# Part 3 reproduced results

Exact match against the published answer keys. Wilson intervals are question-level.

## countqa

| Sample | gpt-6.1-sol@low | claude-haiku-5.5@high | gpt-6-luna@low |
|---|---:|---:|---:|
| shared | 289/400 (72.2%) | 233/400 (58.2%) | 183/400 (45.8%) |
| all answered | 289/400 (72.2%) | 972/1528 (63.6%) | 683/1528 (44.7%) |
| 0-5 | 68/94 (72.3%) | 60/94 (63.8%) | 51/94 (54.3%) |
| 6-10 | 104/147 (70.7%) | 84/147 (57.1%) | 73/147 (49.7%) |
| 11-20 | 91/126 (72.2%) | 71/126 (56.3%) | 47/126 (37.3%) |
| 21+ | 26/33 (78.8%) | 18/33 (54.5%) | 12/33 (36.4%) |

| Metric | gpt-6.1-sol@low | claude-haiku-5.5@high | gpt-6-luna@low |
|---|---:|---:|---:|
| Shared within ±1 | 86.0% | 81.2% | 71.5% |
| USD / 1,000 | $12.10 | $0.70 | $0.70 |

All three agree against the key: 6/400.

## holocount

| Sample | gpt-6.1-sol@low | claude-haiku-5.5@high | gpt-6-luna@low |
|---|---:|---:|---:|
| shared | 240/300 (80.0%) | 242/300 (80.7%) | 204/300 (68.0%) |
| all answered | 240/300 (80.0%) | 242/300 (80.7%) | 204/300 (68.0%) |
| 0-5 | 176/213 (82.6%) | 179/213 (84.0%) | 161/213 (75.6%) |
| 6-10 | 33/40 (82.5%) | 30/40 (75.0%) | 20/40 (50.0%) |
| 11-20 | 19/28 (67.9%) | 20/28 (71.4%) | 15/28 (53.6%) |
| 21+ | 12/19 (63.2%) | 13/19 (68.4%) | 8/19 (42.1%) |

| Metric | gpt-6.1-sol@low | claude-haiku-5.5@high | gpt-6-luna@low |
|---|---:|---:|---:|
| Shared within ±1 | 93.3% | 94.7% | 87.7% |
| USD / 1,000 | $2.80 | $0.23 | $0.16 |

All three agree against the key: 10/300.

Scored run: $7.93017800; discarded probe: $0.16801630; total: $8.09819430.
