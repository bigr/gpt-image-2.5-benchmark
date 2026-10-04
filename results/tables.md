# Recomputed tables

Images: 300; with an addition in the corrected reference: 279; checklist answers scored: 1758.

## Image model

| | sunburst | flare |
|---|---|---|
| 8 elements | 88.8% | 95.0% |
| 15 elements | 94.0% | 96.0% |
| 25 elements | 94.0% | 96.0% |
| Specific details | 97.6% | 98.6% |
| Landmark substituted | 0 of 60 | 0 of 60 |
| Forbidden thing drawn | 0 of 50 | 0 of 50 |
| Period images with additions | 54 of 60 | 45 of 60 |

## Checklist (positive = visible)

| Reader | n | Precision | Recall | Specificity |
|---|---|---|---|---|
| gpt-6.1-sol | 1758 | 98.7% | 99.1% | 93.3% |
| gpt-6-sol | 1758 | 98.0% | 98.6% | 89.8% |
| gpt-6-luna | 1758 | 96.6% | 99.5% | 81.7% |
| gpt-6.1-sol (medium effort) | 1758 | 98.7% | 99.2% | 93.3% |

## Additions (one binary question per image)

| Reader | Accuracy | Precision | Recall |
|---|---|---|---|
| gpt-6.1-sol | 98.3% | 100.0% | 98.2% |
| gpt-6-sol | 84.7% | 100.0% | 83.5% |
| gpt-6-luna | 60.7% | 100.0% | 57.7% |
| gpt-6.1-sol (medium effort) | 99.0% | 99.3% | 99.6% |
| always yes | 93.0% | 93.0% | 100.0% |

## Agreement on the 273 settled rows (the definition used in the article)

| Reader | Agree | Counted | % |
|---|---|---|---|
| reference | 238 | 273 | 87.2% |
| gpt-6.1-sol | 231 | 273 | 84.6% |
| gpt-6-sol | 159 | 273 | 58.2% |
| gpt-6-luna | 82 | 273 | 30.0% |
| gpt-6.1-sol (medium effort) | 231 | 273 | 84.6% |

## Stricter variant: 249 questions (excluded items and unknown rows dropped)

| Reader | Agree | Counted | % |
|---|---|---|---|
| reference | 217 | 249 | 87.1% |
| gpt-6.1-sol | 212 | 249 | 85.1% |
| gpt-6-sol | 153 | 249 | 61.4% |
| gpt-6-luna | 72 | 249 | 28.9% |
| gpt-6.1-sol (medium effort) | 215 | 249 | 86.3% |
