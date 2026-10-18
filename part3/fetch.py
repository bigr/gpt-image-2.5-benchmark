"""Fetch pinned public datasets and verify every question, key and original image.

Only the CountQA parquet reader needs pyarrow. Downloaded images stay in --out,
never in this repository by default. This script makes no model/API-key calls.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def safe_name(name):
    if not name or Path(name).name != name or name in ('.', '..') or '\\' in name:
        raise ValueError(f'Unsafe dataset filename: {name!r}')
    return name


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(source, remote, target):
    if target.exists():
        return target
    url = f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}/" + urllib.parse.quote(remote, safe='/')
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.partial')
    try:
        with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as stream:
            for chunk in iter(lambda: response.read(1024 * 1024), b''):
                stream.write(chunk)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return target


def cached_or_download(cache, relative, source, remote, target):
    cached = cache / relative if cache else None
    return cached if cached and cached.is_file() else download(source, remote, target)


def verify_questions(actual, expected):
    if actual.keys() != expected.keys():
        raise ValueError('Dataset question keys differ from the published manifest')
    for key, item in actual.items():
        for field in ('row', 'q', 'question', 'answer', 'image', 'meta'):
            if item[field] != expected[key][field]:
                raise ValueError(f'Dataset differs at {key}, field {field}')


def verify_image(path, expected):
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f'Original image SHA-256 mismatch: {path.name}')


def countqa(out, cache, expected, hashes):
    import pyarrow.parquet as pq
    source = expected['source']
    items = {}
    image_names = {int(Path(name).stem): name for name in hashes}
    row = 0
    for shard in range(13):
        name = f'test-{shard:05d}-of-00013.parquet'
        path = cached_or_download(cache, Path('countqa/raw') / name, source, 'data/' + name, out / 'countqa/raw' / name)
        for record in pq.read_table(path).to_pylist():
            image_name = safe_name(image_names[row])
            image = record['image']['bytes']
            if hashlib.sha256(image).hexdigest() != hashes[image_name]:
                raise ValueError(f'CountQA image differs at row {row}')
            local = out / 'countqa/images' / image_name
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(image)
            if len(record['questions']) != len(record['answers']):
                raise ValueError(f'CountQA question/answer length mismatch at row {row}')
            for q, (question, answer) in enumerate(zip(record['questions'], record['answers'])):
                key = f'{row}-{q}'
                items[key] = {'key': key, 'row': row, 'q': q, 'question': question, 'answer': int(answer), 'image': {'row': row}, 'meta': {'categories': record.get('categories') or [], 'is_focused': record.get('is_focused')}}
            row += 1
    verify_questions(items, expected['items'])
    return {'dataset': 'countqa', 'source': source, 'items': items}


def holocount(out, cache, expected, hashes):
    source = expected['source']
    path = download(source, 'data/metadata.jsonl', out / 'holocount/metadata.jsonl')
    items = {}
    for row, line in enumerate(path.read_text(encoding='utf-8').splitlines()):
        record = json.loads(line)
        name = safe_name(Path(record['file_name']).name)
        if record['file_name'] != 'images/' + name:
            raise ValueError(f'Unexpected HoloCount file path: {record["file_name"]!r}')
        local = cached_or_download(cache, Path('holocount/images') / name, source, 'data/images/' + name, out / 'holocount/images' / name)
        verify_image(local, hashes[name])
        key = f'{row}-0'
        items[key] = {'key': key, 'row': row, 'q': 0, 'question': record['question'], 'answer': int(record['answer']), 'image': {'sample_id': record['sample_id'], 'file_name': name}, 'meta': {'split': record['split']}}
    verify_questions(items, expected['items'])
    # With --cache, image files remain at their cache location; verification is identical.
    return {'dataset': 'holocount', 'source': source, 'items': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Local dataset directory outside the repository')
    parser.add_argument('--cache', type=Path, help='Optional read-only prior download containing countqa/raw and holocount/images')
    parser.add_argument('--dataset', choices=['all', 'countqa', 'holocount'], default='all')
    args = parser.parse_args()
    hashes = load(HERE / 'data/image-sha256.json')
    try:
        for dataset, fetch in [('countqa', countqa), ('holocount', holocount)]:
            if args.dataset not in ('all', dataset):
                continue
            expected = load(HERE / f'data/{dataset}.manifest.json')
            manifest = fetch(args.out, args.cache, expected, hashes[dataset])
            target = args.out / dataset / 'manifest.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(f'{dataset}: verified {len(manifest["items"])} questions and {len(hashes[dataset])} original image hashes')
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.exit(1, f'Fetch/verification failed: {exc}\n')


if __name__ == '__main__':
    main()
