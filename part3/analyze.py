"""Reproduce part 3 offline with Python's standard library; never calls a model."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
JUDGES = ('gpt-6.1-sol@low', 'claude-haiku-5.5@high', 'gpt-6-luna@low')
DATASETS = ('countqa', 'holocount')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def statistics(pairs):
    """Question-level scores; Wilson does not account for photo clustering."""
    n = len(pairs)
    if not n:
        raise ValueError('Cannot score an empty sample')
    exact = sum(truth == answer for truth, answer in pairs)
    p, z = exact / n, 1.959963984540054
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {
        'n': n, 'exact': exact, 'percent': 100 * p,
        'within1': sum(abs(t - a) <= 1 for t, a in pairs),
        'within1_percent': 100 * sum(abs(t - a) <= 1 for t, a in pairs) / n,
        'over': sum(a > t for t, a in pairs),
        'under': sum(a < t for t, a in pairs),
        'key_zero': sum(t == 0 for t, _ in pairs),
        'positive_when_key_zero': sum(t == 0 and a > 0 for t, a in pairs),
        'zero_when_key_positive': sum(t > 0 and a == 0 for t, a in pairs),
        'wilson95_percent': [100 * (center - half), 100 * (center + half)],
    }


def read_answers(path, expected_keys):
    """Reject incomplete or duplicate runs instead of silently changing denominators."""
    rows = {}
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        row = json.loads(line)
        key = row['key']
        if key in rows:
            raise ValueError(f'{path.name}:{line_number}: duplicate key {key}')
        if row.get('kind') != 'answer' or type(row.get('count')) is not int or row['count'] < 0:
            raise ValueError(f'{path.name}:{line_number}: invalid answer')
        if not isinstance(row.get('cost'), (float, int)) or not math.isfinite(row['cost']) or row['cost'] < 0:
            raise ValueError(f'{path.name}:{line_number}: invalid cost')
        rows[key] = row
    if len(expected_keys) != len(set(expected_keys)) or set(rows) != set(expected_keys):
        raise ValueError(f'{path.name}: answers differ from the plan')
    return rows


def analyze(data):
    plan = load(data / 'plan.json')
    protocol = load(data / 'protocol.json')
    report = {'seed': plan['seed'], 'datasets': {}, 'cost': {}}
    errors = {}
    for dataset in DATASETS:
        items = load(data / f'{dataset}.manifest.json')['items']
        streams = plan['plan'][dataset]
        if set(streams) != set(JUDGES):
            raise ValueError(f'{dataset}: unexpected judge configurations')
        answers = {j: read_answers(data / 'readings' / f'{dataset}.{j}.jsonl', streams[j]) for j in JUDGES}
        if any(not set(a).issubset(items) for a in answers.values()):
            raise ValueError(f'{dataset}: unknown question key')
        shared = set.intersection(*(set(a) for a in answers.values()))
        if not shared:
            raise ValueError(f'{dataset}: no shared questions')
        if dataset == 'holocount' and any(set(a) != shared for a in answers.values()):
            raise ValueError('HoloCount judges must share the same sample')
        if dataset == 'countqa':
            if set(answers[JUDGES[0]]) != shared or any(set(answers[j]) != set(items) for j in JUDGES[1:]):
                raise ValueError('CountQA must have a shared sol subset and two full-set runs')
            selected_rows = {items[k]['row'] for k in shared}
            if any(k not in shared for k, item in items.items() if item['row'] in selected_rows):
                raise ValueError('CountQA sample splits a photo across question selections')
        def score(keys, judge):
            return statistics([(items[k]['answer'], answers[judge][k]['count']) for k in keys])
        groups = {}
        for lo, hi, label in [(0, 5, '0-5'), (6, 10, '6-10'), (11, 20, '11-20'), (21, math.inf, '21+')]:
            keys = sorted(k for k in shared if lo <= items[k]['answer'] <= hi)
            groups[label] = {j: score(keys, j) if keys else None for j in JUDGES}
        cost = {j: math.fsum(r['cost'] for r in a.values()) for j, a in answers.items()}
        agreement = []
        for key in sorted(shared, key=lambda k: tuple(map(int, k.split('-')))):
            counts = {answers[j][key]['count'] for j in JUDGES}
            if len(counts) == 1 and next(iter(counts)) != items[key]['answer']:
                agreement.append({'key': key, 'question': items[key]['question'], 'answer_key': items[key]['answer'], 'judges': next(iter(counts))})
        report['datasets'][dataset] = {
            'all': {j: score(sorted(a), j) for j, a in answers.items()},
            'shared': {j: score(sorted(shared), j) for j in JUDGES},
            'shared_questions': len(shared), 'shared_photo_rows': len({items[k]['row'] for k in shared}),
            'buckets': groups, 'cost_usd': cost,
            'cost_per1000_usd': {j: 1000 * cost[j] / len(answers[j]) for j in JUDGES},
            'subset_questions': dict(sorted(Counter(items[k]['meta'].get('split', 'CountQA') for k in shared).items())),
            'all_agree_against_key': agreement,
            'recompressed_calls': sum(r['image_sent']['resized'] for a in answers.values() for r in a.values()),
        }
        errors[dataset] = {j: [{'key': k, 'question': items[k]['question'], 'answer_key': items[k]['answer'], 'count': r['count'], 'note': r['note']} for k, r in sorted(a.items()) if r['count'] != items[k]['answer']] for j, a in answers.items()}
    report['cost'] = {'scored_run_usd': math.fsum(c for ds in report['datasets'].values() for c in ds['cost_usd'].values()), 'discarded_probe_usd': protocol['discarded_probe_usd']}
    report['cost']['total_usd'] = math.fsum(report['cost'].values())
    return report, errors


def tables(report):
    lines = ['# Part 3 reproduced results', '', 'Exact match against the published answer keys. Wilson intervals are question-level.', '']
    for dataset, ds in report['datasets'].items():
        lines += [f'## {dataset}', '', '| Sample | ' + ' | '.join(JUDGES) + ' |', '|---|---:|---:|---:|']
        for name, group in [('shared', ds['shared']), ('all answered', ds['all'])] + list(ds['buckets'].items()):
            values = [f"{group[j]['exact']}/{group[j]['n']} ({group[j]['percent']:.1f}%)" if group[j] else 'not sampled' for j in JUDGES]
            lines.append('| ' + name + ' | ' + ' | '.join(values) + ' |')
        lines += ['', '| Metric | ' + ' | '.join(JUDGES) + ' |', '|---|---:|---:|---:|']
        lines.append('| Shared within ±1 | ' + ' | '.join(f"{ds['shared'][j]['within1_percent']:.1f}%" for j in JUDGES) + ' |')
        lines.append('| USD / 1,000 | ' + ' | '.join(f"${ds['cost_per1000_usd'][j]:.2f}" for j in JUDGES) + ' |')
        lines += ['', f"All three agree against the key: {len(ds['all_agree_against_key'])}/{ds['shared_questions']}.", '']
    lines += [f"Scored run: ${report['cost']['scored_run_usd']:.8f}; discarded probe: ${report['cost']['discarded_probe_usd']:.8f}; total: ${report['cost']['total_usd']:.8f}."]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=HERE / 'data')
    parser.add_argument('--out', type=Path, help='Write report.json, errors.json and tables.md; omit for read-only stdout')
    args = parser.parse_args()
    try:
        report, errors = analyze(args.data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'Cannot analyze: {exc}\n')
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        for filename, value in [('report.json', report), ('errors.json', errors)]:
            (args.out / filename).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        (args.out / 'tables.md').write_text(tables(report), encoding='utf-8')
    print(tables(report))


if __name__ == '__main__':
    main()
