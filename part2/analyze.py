"""Offline reproduction of the part 2 article. Python standard library only."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parent / 'data'
COUNT_LABELS = ['gpt-6.1-sol', 'gpt-6-luna', 'gpt-6-luna.low-rep1', 'gpt-6-luna.low-rep2', 'gpt-6-luna@medium', 'gpt-6-luna@high', 'claude-haiku-5.5', 'claude-haiku-5.5@low', 'claude-haiku-5.5@medium', 'claude-haiku-5.5@high']
MISFIT_LABELS = ['gpt-6.1-sol', 'gpt-6-luna', 'gpt-6.1-sol@medium', 'claude-haiku-5.5', 'claude-haiku-5.5@low', 'claude-haiku-5.5@medium', 'claude-haiku-5.5@high']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def readings(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def merge_count_rounds(paths):
    result = {}
    for path in paths:
        for key, values in load(path).items():
            result.setdefault(key, {}).update(values)
    return result


def ratio(correct, total):
    return {'correct': correct, 'n': total, 'percent': 100 * correct / total if total else None}


def accuracy(pairs):
    return ratio(sum(a == b for a, b in pairs), len(pairs))


def normalize(text):
    return ' '.join(text.lower().split())


def analyze(data):
    exclusions = load(data / 'exclusions.json')
    count_dir, tally_dir, misfit_dir = (data / name for name in ('count', 'tally', 'misfit'))
    count_truth = merge_count_rounds([count_dir / 'counts_b.json'] + [count_dir / f'count_resolution.{name}.json' for name in ('founder-round1', 'founder-round2', 'founder-round3-haiku', 'founder-round4-haiku-efforts')])
    uncertain = set(load(count_dir / 'sacks_uncertain.json'))
    ladders = set(exclusions['count_ladders'])
    result = {'count': {}, 'tally': {}, 'misfit': {}, 'agents': {}, 'generator': {}, 'cost': {}}
    for label in COUNT_LABELS:
        rows = {row['key']: row for row in readings(count_dir / f'reading_count.{label}.jsonl')}
        pairs, sacks = [], []
        for key, values in count_truth.items():
            for item, true in values.items():
                if (item == 'e16' and key in ladders) or (item == 'e04' and key in uncertain):
                    continue
                pair = (rows.get(key, {}).get('counts', {}).get(item), true)
                pairs.append(pair)
                if item == 'e04':
                    sacks.append(pair)
        result['count'][label] = {'all': accuracy(pairs), 'sacks': accuracy(sacks)}
    tally_truth = load(tally_dir / 'tally_b.json')
    for name in ('founder-round1', 'founder-round2-haiku', 'founder-round3-haiku-efforts'):
        for key, value in load(tally_dir / f'tally_resolution.{name}.json').items():
            tally_truth[key] = next(iter(value.values())) if isinstance(value, dict) else value
    for label in COUNT_LABELS:
        rows = {row['key']: row for row in readings(tally_dir / f'reading_tally.{label}.jsonl')}
        groups = defaultdict(list)
        for key, true in tally_truth.items():
            _, thing, requested, layout = key.split('/')[0].split('-')
            got = next((value for item, value in rows.get(key, {}).get('counts', {}).items() if item.partition(':')[0].strip() == thing), None)
            bucket = '2-3' if int(requested) < 5 else '5-7' if int(requested) < 10 else str(int(requested))
            for group in ('all', 'count:' + bucket, 'layout:' + layout):
                groups[group].append((got, true))
        result['tally'][label] = {group: accuracy(pairs) for group, pairs in groups.items()}
    for label, filename in [('Claude Opus 5.5 (medium)', 'tally_b.json'), ('Claude Sonnet 5.5 (low)', 'tally_sonnet-low.json'), ('Claude Haiku 4.5 (low)', 'tally_haiku-low.json')]:
        answers = load(tally_dir / filename)
        result['agents'][label] = accuracy([(answers.get(key), value) for key, value in tally_truth.items()])
    groups = defaultdict(list)
    for key, true in tally_truth.items():
        _, _, requested, layout = key.split('/')[0].split('-')
        for group in (str(int(requested)), layout):
            groups[group].append(true == int(requested))
    result['generator'] = {group: ratio(sum(hits), len(hits)) for group, hits in groups.items()}
    truth = {}
    for name in exclusions['misfit_rounds']:
        for key, fields in load(misfit_dir / f'misfit_resolution.{name}.json').items():
            for field, value in fields.items():
                if isinstance(value, dict):
                    truth.setdefault(key, {}).setdefault(field, {}).update(value)
                else:
                    truth.setdefault(key, {})[field] = value
    skipped = {(key, normalize(item)) for key, item in exclusions['misfit_items']}
    discoveries = {}
    for label in MISFIT_LABELS:
        seeded = planted = real = negative = alarms = rejected = adjudicated = 0
        found, unknown = [], []
        for row in readings(misfit_dir / f'reading_misfit.{label}.jsonl'):
            key = row['key']
            items = {normalize(item): verdict for item, verdict in truth.get(key, {}).get('items', {}).items() if (key, normalize(item)) not in skipped}
            names = [normalize(item['thing']) for item in row['misfits'] if (key, normalize(item['thing'])) not in skipped]
            verdicts = [items.get(name) for name in names]
            unknown.extend([key, name] for name, verdict in zip(names, verdicts) if verdict is None)
            adjudicated += sum(value is not None for value in verdicts)
            rejected += sum(value is False for value in verdicts)
            if '-seeded/' in key:
                seeded += 1
                matched = truth.get(key, {}).get('matched', {}).get(label)
                planted += bool(matched) if matched is not None else any(value is True for value in verdicts)
            elif any(items.values()):
                real += 1
                if any(value is True for value in verdicts):
                    found.append(key)
            else:
                negative += 1
                alarms += any(value is False for value in verdicts)
        discoveries[label] = set(found)
        result['misfit'][label] = {'planted': ratio(planted, seeded), 'model_added': ratio(len(found), real), 'false_alarms': ratio(alarms, negative), 'rejected': ratio(rejected, adjudicated), 'found_image_keys': found, 'unresolved_items': unknown}
    result['combined_misfits'] = {'sol_low_and_haiku_default': len(discoveries['gpt-6.1-sol'] | discoveries['claude-haiku-5.5']), 'plus_sol_medium': len(discoveries['gpt-6.1-sol'] | discoveries['claude-haiku-5.5'] | discoveries['gpt-6.1-sol@medium'])}
    totals = defaultdict(float)
    for directory, axis in ((count_dir, 'count'), (tally_dir, 'tally'), (misfit_dir, 'misfit')):
        for path in sorted(directory.glob(f'reading_{axis}.*.jsonl')):
            label = path.name.split('.', 1)[1][:-6]
            totals[label] += sum(row.get('cost', 0) or 0 for row in readings(path))
    original = readings(tally_dir / 'reading_tally.claude-haiku-5.5.jsonl.strict-v1')
    discarded_cost = sum(row['cost'] for row in original if not row['counts'])
    costs = load(data / 'cost-notes.json')
    result['cost'] = {'scored_calls_by_label': dict(totals), 'scored_calls_total': sum(totals.values()), 'discarded_format_calls': {'n': sum(not row['counts'] for row in original), 'usd': discarded_cost}, **costs, 'judges_usd_including_approx_probes': sum(totals.values()) + discarded_cost + costs['reasoning_probes_usd_approx'], 'total_usd_including_approx_probes': sum(totals.values()) + discarded_cost + costs['reasoning_probes_usd_approx'] + costs['image_generation_usd']}
    return result


def tables(result):
    lines = ['# Part 2 reproduced results', '', 'Percentages use exact matches against the corrected reference. Haiku settings are configurations, not repeat trials.', '']
    def table(title, headers, rows):
        lines.extend(['## ' + title, '', '| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'])
        lines.extend('| ' + ' | '.join(str(value) for value in row) + ' |' for row in rows)
        lines.append('')
    def pct(value):
        return f"{value['percent']:.1f}% ({value['correct']}/{value['n']})"
    table('Counting: part 1 and sacks', ['Model / setting', 'All questions', 'Sacks'], [[label, pct(value['all']), pct(value['sacks'])] for label, value in result['count'].items()])
    table('Who can count: new set and effort sweeps', ['Model / setting', 'All', '2-3', '5-7', '10', '15', 'Separate', 'Overlap'], [[label] + [pct(value[key]) for key in ('all', 'count:2-3', 'count:5-7', 'count:10', 'count:15', 'layout:separate', 'layout:overlap')] for label, value in result['tally'].items()])
    table('Generator fidelity', ['Requested / layout', 'Exact'], [[key, pct(value)] for key, value in result['generator'].items()])
    table('What does not belong', ['Model / setting', 'Planted', 'Generator-added', 'False alarms', 'Rejected / adjudicated'], [[label] + [pct(value[key]) for key in ('planted', 'model_added', 'false_alarms', 'rejected')] for label, value in result['misfit'].items()])
    table('Claude as agents', ['Agent', 'Exact'], [[label, pct(value)] for label, value in result['agents'].items()])
    table('Costs of three scored tests', ['Label', 'USD'], [[label, f'{value:.7f}'] for label, value in result['cost']['scored_calls_by_label'].items()])
    lines.extend(['Combined sol low + Haiku default: ' + str(result['combined_misfits']['sol_low_and_haiku_default']) + '/8. With sol medium: ' + str(result['combined_misfits']['plus_sol_medium']) + '/8.', '', f"Total including approximate probe cost: ${result['cost']['total_usd_including_approx_probes']:.2f}.", 'Probe and image costs are documented totals; raw probe usage is unavailable.'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results')
    args = parser.parse_args()
    data, output = args.data.resolve(), args.output.resolve()
    if output == data or data in output.parents:
        parser.error('output must not be inside the input data directory')
    result = analyze(data)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = tables(result)
    (output / 'tables.md').write_text(report, encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
