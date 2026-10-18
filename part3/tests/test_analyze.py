import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('part3_analyze', HERE / 'analyze.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fetch_spec = importlib.util.spec_from_file_location('part3_fetch', HERE / 'fetch.py')
fetch = importlib.util.module_from_spec(fetch_spec)
fetch_spec.loader.exec_module(fetch)


class PublishedResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.errors = module.analyze(HERE / 'data')

    def test_shared_counts_and_full_set(self):
        c = self.report['datasets']['countqa']
        h = self.report['datasets']['holocount']
        self.assertEqual([(c['shared'][j]['n'], c['shared'][j]['exact']) for j in module.JUDGES], [(400, 289), (400, 233), (400, 183)])
        self.assertEqual([c['all'][j]['exact'] for j in module.JUDGES], [289, 972, 683])
        self.assertEqual([h['shared'][j]['exact'] for j in module.JUDGES], [240, 242, 204])
        self.assertEqual(c['shared_photo_rows'], 258)
        self.assertEqual(len(h['subset_questions']), 20)
        self.assertEqual((min(h['subset_questions'].values()), max(h['subset_questions'].values())), (8, 27))

    def test_all_bucket_numerators(self):
        expected = {'countqa': [[68, 60, 51], [104, 84, 73], [91, 71, 47], [26, 18, 12]], 'holocount': [[176, 179, 161], [33, 30, 20], [19, 20, 15], [12, 13, 8]]}
        for dataset, rows in expected.items():
            ds = self.report['datasets'][dataset]
            self.assertEqual([[group[j]['exact'] for j in module.JUDGES] for group in ds['buckets'].values()], rows)

    def test_near_misses_zero_cases_and_shared_disagreements(self):
        c = self.report['datasets']['countqa']; h = self.report['datasets']['holocount']
        self.assertEqual([c['shared'][j]['within1'] for j in module.JUDGES], [344, 325, 286])
        self.assertEqual([h['shared'][j]['within1'] for j in module.JUDGES], [280, 284, 263])
        self.assertEqual([h['shared'][j]['positive_when_key_zero'] for j in module.JUDGES], [6, 2, 5])
        self.assertEqual(h['shared'][module.JUDGES[0]]['key_zero'], 32)
        self.assertEqual(c['all'][module.JUDGES[1]]['zero_when_key_positive'], 37)
        self.assertEqual([len(x['all_agree_against_key']) for x in (c, h)], [6, 10])
        self.assertEqual((c['shared'][module.JUDGES[0]]['over'], c['shared'][module.JUDGES[0]]['under']), (84, 27))

    def test_costs_interval_and_recompression(self):
        c = self.report['datasets']['countqa']; h = self.report['datasets']['holocount']
        self.assertAlmostEqual(self.report['cost']['scored_run_usd'], 7.930178)
        self.assertAlmostEqual(self.report['cost']['total_usd'], 8.0981943)
        self.assertEqual([round(c['cost_per1000_usd'][j], 2) for j in module.JUDGES], [12.10, .70, .70])
        self.assertEqual([round(h['cost_per1000_usd'][j], 2) for j in module.JUDGES], [2.80, .23, .16])
        self.assertEqual([round(x, 1) for x in c['shared'][module.JUDGES[0]]['wilson95_percent']], [67.7, 76.4])
        self.assertEqual((c['recompressed_calls'], h['recompressed_calls']), (5, 0))

    def test_within_one_includes_exact_and_both_directions(self):
        s = module.statistics([(4, 4), (4, 3), (4, 5), (4, 6), (0, 1)])
        self.assertEqual((s['exact'], s['within1'], s['over'], s['under']), (1, 4, 3, 1))

    def test_errors_are_not_relabeled(self):
        errors = {r['key']: r for r in self.errors['countqa'][module.JUDGES[0]]}
        self.assertEqual((errors['531-0']['answer_key'], errors['531-0']['count']), (8, 0))
        self.assertEqual((errors['358-0']['answer_key'], errors['358-0']['count']), (33, 0))


class CorruptInput(unittest.TestCase):
    def test_duplicate_and_incomplete_journal_rejected(self):
        row = {'key': '1-0', 'kind': 'answer', 'count': 3, 'cost': .1}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'run.jsonl'
            path.write_text(json.dumps(row) + '\n' + json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                module.read_answers(path, ['1-0'])
            path.write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'differ from the plan'):
                module.read_answers(path, ['1-0', '2-0'])

    def test_invalid_count_or_cost_rejected(self):
        for count, cost in [(True, .1), (-1, .1), (1.2, .1), (1, -1), (1, float('nan'))]:
            with self.subTest(count=count, cost=cost), tempfile.TemporaryDirectory() as d:
                path = Path(d) / 'run.jsonl'
                path.write_text(json.dumps({'key': '1-0', 'kind': 'answer', 'count': count, 'cost': cost}) + '\n')
                with self.assertRaises(ValueError):
                    module.read_answers(path, ['1-0'])

    def test_changed_key_detected_against_upstream(self):
        item = {'row': 0, 'q': 0, 'question': 'How many?', 'answer': 4, 'image': {'row': 0}, 'meta': {}}
        fetch.verify_questions({'0-0': item}, {'0-0': item})
        with self.assertRaisesRegex(ValueError, 'field answer'):
            fetch.verify_questions({'0-0': item}, {'0-0': dict(item, answer=5)})

    def test_corrupt_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'x.jpg'; path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                fetch.verify_image(path, '0' * 64)

    def test_path_traversal_rejected(self):
        for name in ['../image.jpg', '/tmp/image.jpg', '..', 'sub\\image.jpg']:
            with self.assertRaises(ValueError):
                fetch.safe_name(name)


if __name__ == '__main__':
    unittest.main()
