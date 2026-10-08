"""Verify full-resolution part 2 images, either flat assets or the extracted zip."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--require-anon', action='store_true')
    args = parser.parse_args()
    data = Path(__file__).resolve().parent / 'data'
    rows = json.loads((data / 'image-manifest.json').read_text())
    failures = []
    for row in rows:
        candidates = [args.directory / row['filename'], args.directory / row['archive_path']]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            failures.append(row['filename'])
    if args.require_anon:
        for row in json.loads((data / 'anonymous-tally.json').read_text()):
            path = args.directory / row['filename']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                failures.append(row['filename'])
    if failures:
        raise SystemExit('Missing or altered images: ' + ', '.join(failures))
    print(f'Verified {len(rows)} images' + (' and 144 anonymous copies.' if args.require_anon else '.'))


if __name__ == '__main__':
    main()
