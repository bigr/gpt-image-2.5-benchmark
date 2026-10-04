"""Unit tests for the pure scoring functions, on tiny hand-made inputs."""

import unittest

from benchmark import scoring as sc


def reading(answers, inventions=()):
    return {"answers": dict(answers), "inventions": list(inventions)}


class RoundOrder(unittest.TestCase):
    def test_later_round_overrides_earlier_per_item(self):
        r1 = {"img/a/0": {"x": True, "y": True}}
        r2 = {"img/a/0": {"x": False}}
        self.assertEqual(sc.merge_rounds([r1, r2]), {"img/a/0": {"x": False, "y": True}})

    def test_order_matters(self):
        r1 = {"img/a/0": {"x": True}}
        r2 = {"img/a/0": {"x": False}}
        self.assertTrue(sc.merge_rounds([r2, r1])["img/a/0"]["x"])
        self.assertFalse(sc.merge_rounds([r1, r2])["img/a/0"]["x"])

    def test_inputs_are_not_modified(self):
        r1 = {"img/a/0": {"x": True}}
        r2 = {"img/a/0": {"x": False}}
        sc.merge_rounds([r1, r2])
        self.assertEqual(r1, {"img/a/0": {"x": True}})

    def test_settlement_overrides_reference_and_additions_pseudo_item(self):
        ref = {"img/a/0": reading({"x": True, "y": False}, ["a tree"])}
        truth = sc.build_truth(ref, {"img/a/0": {"y": True, "inventions": False}})
        self.assertEqual(truth["img/a/0"]["answers"], {"x": True, "y": True})
        self.assertFalse(truth["img/a/0"]["has_addition"])

    def test_unsettled_reference_answer_survives(self):
        ref = {"img/a/0": reading({"x": True}, ["a tree"])}
        truth = sc.build_truth(ref, {})
        self.assertTrue(truth["img/a/0"]["answers"]["x"])
        self.assertTrue(truth["img/a/0"]["has_addition"])


class UnknownAnswers(unittest.TestCase):
    def setUp(self):
        self.ref = {
            "img/a/0": reading({"x": True, "y": False}),
            "img/a/1": reading({"x": True, "y": True}),
        }

    def test_key_is_removed_never_none_or_false(self):
        truth = sc.build_truth(self.ref, {}, {"img/a/0": ["y"]})
        self.assertNotIn("y", truth["img/a/0"]["answers"])
        self.assertIn("y", truth["img/a/1"]["answers"])

    def test_removal_wins_over_a_settled_answer(self):
        truth = sc.build_truth(self.ref, {"img/a/0": {"y": True}}, {"img/a/0": ["y"]})
        self.assertNotIn("y", truth["img/a/0"]["answers"])

    def test_unknown_is_skipped_in_numerator_and_denominator(self):
        prompts = {"img": {"items": [{"id": "y", "expect": "present"}]}}
        judge = {"img/a/0": reading({"y": True}), "img/a/1": reading({"y": True})}
        truth = sc.build_truth(self.ref, {}, {"img/a/0": ["y"]})
        m = sc.metrics(sc.confusion(sc.checklist_pairs(prompts, judge, truth, set())))
        self.assertEqual(m["n"], 1)
        # if the unknown had been stored as False the judge would have a false positive
        self.assertEqual(m["fp"], 0)
        self.assertEqual(m["precision"], 1.0)

    def test_confusion_skips_none_on_either_side(self):
        c = sc.confusion([(True, None), (None, True), (None, None), (True, True)])
        self.assertEqual(c, {"tp": 1, "fp": 0, "tn": 0, "fn": 0})


class Exclusions(unittest.TestCase):
    def test_excluded_item_is_not_counted(self):
        prompts = {
            "p": {"items": [{"id": "x", "expect": "present"}, {"id": "t", "expect": "present"}]}
        }
        truth = {"p/a/0": {"answers": {"x": True, "t": True}, "has_addition": False}}
        judge = {"p/a/0": reading({"x": True, "t": False})}
        full = sc.metrics(sc.confusion(sc.checklist_pairs(prompts, judge, truth, set())))
        cut = sc.metrics(sc.confusion(sc.checklist_pairs(prompts, judge, truth, {("p", "t")})))
        self.assertEqual((full["n"], full["fn"]), (2, 1))
        self.assertEqual((cut["n"], cut["fn"]), (1, 0))

    def test_excluded_set_reads_prompt_item_pairs(self):
        ex = {"excluded_items": [{"prompt": "p", "item": "t", "reason": "r"}]}
        self.assertEqual(sc.excluded_set(ex), {("p", "t")})

    def test_generator_rates_skip_excluded_and_unknown(self):
        prompts = {
            "p": {
                "test": "how-much-it-keeps",
                "elements": 8,
                "items": [
                    {"id": "a", "expect": "present"},
                    {"id": "b", "expect": "present"},
                    {"id": "c", "expect": "present"},
                    {"id": "f", "expect": "absent"},
                ],
            }
        }
        truth = {
            "p/v/0": {
                "answers": {"a": True, "b": False, "f": False},
                "has_addition": True,
            },  # c unknown
        }
        r = sc.generator_rates(prompts, truth, {("p", "b")})
        g = ("how-much-it-keeps", 8, "v")
        self.assertEqual(r["required"][g], [1, 1])  # only "a": b excluded, c unknown
        self.assertEqual(r["forbidden"][g], [0, 1])
        self.assertEqual(r["additions"][g], [1, 1])


class MetricMath(unittest.TestCase):
    def test_known_confusion(self):
        m = sc.metrics({"tp": 8, "fp": 2, "tn": 6, "fn": 4})
        self.assertEqual(m["n"], 20)
        self.assertAlmostEqual(m["precision"], 0.8)
        self.assertAlmostEqual(m["recall"], 8 / 12)
        self.assertAlmostEqual(m["specificity"], 0.75)
        self.assertAlmostEqual(m["accuracy"], 0.7)

    def test_zero_denominator_is_none(self):
        m = sc.metrics({"tp": 0, "fp": 0, "tn": 3, "fn": 0})
        self.assertIsNone(m["precision"])
        self.assertIsNone(m["recall"])
        self.assertEqual(m["specificity"], 1.0)

    def test_positive_means_visible_also_for_absent_items(self):
        prompts = {"p": {"items": [{"id": "d", "expect": "absent"}]}}
        truth = {"p/a/0": {"answers": {"d": False}, "has_addition": False}}
        judge = {"p/a/0": reading({"d": True})}
        m = sc.metrics(sc.confusion(sc.checklist_pairs(prompts, judge, truth, set())))
        self.assertEqual(m["fp"], 1)

    def test_blank_inventions_are_not_additions(self):
        self.assertFalse(sc.has_addition({"inventions": ["", "  "]}))
        self.assertTrue(sc.has_addition({"inventions": ["", "a tree"]}))
        self.assertEqual(sc.addition_count({"inventions": ["", "a tree", "x"]}), 2)


class Baseline(unittest.TestCase):
    def test_always_yes_equals_prevalence(self):
        m = sc.always_yes([True] * 93 + [False] * 7)
        self.assertEqual(m["n"], 100)
        self.assertAlmostEqual(m["accuracy"], 0.93)
        self.assertAlmostEqual(m["precision"], 0.93)
        self.assertEqual(m["recall"], 1.0)
        self.assertEqual(m["specificity"], 0.0)

    def test_judge_can_lose_to_baseline(self):
        truth = {f"p/a/{i}": {"answers": {}, "has_addition": i < 9} for i in range(10)}
        judge = {f"p/a/{i}": reading({}, ["x"] if i < 5 else []) for i in range(10)}  # misses 4
        acc = sc.metrics(sc.confusion(sc.addition_pairs(judge, truth)))["accuracy"]
        base = sc.always_yes(t["has_addition"] for t in truth.values())["accuracy"]
        self.assertLess(acc, base)


class SettledRows(unittest.TestCase):
    def test_rows_and_exclusions(self):
        st = {"p/a/0": {"x": True, "t": True}, "p/a/1": {"inventions": False}}
        self.assertEqual(len(sc.settled_rows(st, set())), 3)
        self.assertEqual(
            sc.settled_rows(st, {("p", "t")}), [("p/a/0", "x"), ("p/a/1", "inventions")]
        )

    def test_agreement_counts_unknown_as_disagreement_by_default(self):
        truth = {"p/a/0": {"answers": {}, "has_addition": False}}
        reader = {"p/a/0": reading({"x": True})}
        rows = [("p/a/0", "x")]
        self.assertEqual(sc.settled_agreement(reader, truth, rows), (0, 1))
        self.assertEqual(sc.settled_agreement(reader, truth, rows, skip_unknown=True), (0, 0))

    def test_additions_row_uses_has_addition(self):
        truth = {"p/a/0": {"answers": {}, "has_addition": True}}
        reader = {"p/a/0": reading({}, ["x"])}
        self.assertEqual(sc.settled_agreement(reader, truth, [("p/a/0", "inventions")]), (1, 1))


if __name__ == "__main__":
    unittest.main()
