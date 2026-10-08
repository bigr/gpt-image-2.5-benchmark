"""Integration checks against the article's independently reviewed results."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('part2_analyze', ROOT / 'analyze.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReviewedResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = MODULE.analyze(ROOT / 'data')

    def test_count_exclusions(self):
        for label, correct in [('gpt-6.1-sol', 418), ('gpt-6-luna', 397), ('claude-haiku-5.5', 386)]:
            self.assertEqual((self.results['count'][label]['all']['correct'], self.results['count'][label]['all']['n']), (correct, 434))
            self.assertEqual(self.results['count'][label]['sacks']['n'], 58)

    def test_new_counts_and_efforts(self):
        expected = {'gpt-6.1-sol': 139, 'gpt-6-luna': 129, 'gpt-6-luna@medium': 136, 'gpt-6-luna@high': 137, 'claude-haiku-5.5': 125, 'claude-haiku-5.5@low': 111, 'claude-haiku-5.5@medium': 122, 'claude-haiku-5.5@high': 133}
        for label, correct in expected.items():
            self.assertEqual(self.results['tally'][label]['all']['correct'], correct)
            self.assertEqual(self.results['tally'][label]['all']['n'], 144)

    def test_misfits_and_scoped_exclusions(self):
        for label, expected in [('gpt-6.1-sol', (5, 7, 8, 69)), ('gpt-6-luna', (0, 5, 15, 61)), ('gpt-6.1-sol@medium', (5, 7, 8, 68)), ('claude-haiku-5.5', (3, 7, 16, 66)), ('claude-haiku-5.5@low', (1, 13, 23, 75)), ('claude-haiku-5.5@medium', (3, 3, 7, 60)), ('claude-haiku-5.5@high', (2, 7, 11, 61))]:
            row = self.results['misfit'][label]
            self.assertEqual((row['model_added']['correct'], row['false_alarms']['correct'], row['rejected']['correct'], row['rejected']['n']), expected)
            self.assertEqual(row['model_added']['n'], 8)
            self.assertEqual(row['false_alarms']['n'], 40)
            self.assertEqual(row['unresolved_items'], [])
        self.assertEqual(self.results['combined_misfits'], {'sol_low_and_haiku_default': 7, 'plus_sol_medium': 8})

    def test_no_double_billing_of_strict_archive(self):
        extra = self.results['cost']['discarded_format_calls']
        self.assertEqual(extra['n'], 19)
        self.assertAlmostEqual(extra['usd'], 0.0071841)
        self.assertEqual(round(self.results['cost']['total_usd_including_approx_probes'], 2), 4.64)


if __name__ == '__main__':
    unittest.main()
