"""Tests for the ISO 286-2 tolerance calculator.

Expected limits are taken from the ISO 286-2:2010 tables shipped in
iso286/tables.json (cross-checked against the geometry-verified PDF
extraction); the verdict cases follow the inspection-sheet rules.
"""

import unittest

from iso286 import (
    covered_classes,
    deviations,
    go_nogo,
    limits,
    tolerance_width,
    verdict,
    verdict_one,
)


class TestLimits(unittest.TestCase):
    def test_hole_h7(self):
        self.assertEqual(limits(22, "H7"), (22.0, 22.021))
        self.assertEqual(limits(195, "H7"), (195.0, 195.046))
        self.assertEqual(limits(50, "H7"), (50.0, 50.025))

    def test_hole_f(self):
        self.assertEqual(limits(220, "F8"), (220.05, 220.122))
        self.assertEqual(limits(40, "F7"), (40.025, 40.05))

    def test_shaft(self):
        self.assertEqual(limits(220, "j7"), (219.979, 220.025))
        self.assertEqual(limits(150, "g6"), (149.961, 149.986))
        self.assertEqual(limits(22, "h7"), (21.979, 22.0))
        self.assertEqual(limits(80, "p6"), (80.032, 80.051))

    def test_half_micron_js(self):
        # js classes are symmetric with half-micrometre deviations.
        self.assertEqual(limits(22, "js6"), (21.9935, 22.0065))
        self.assertEqual(limits(30, "JS7"), (29.9895, 30.0105))

    def test_hole_p7(self):
        self.assertEqual(limits(120, "P7"), (119.941, 119.976))

    def test_deviations_um(self):
        self.assertEqual(deviations(22, "H7"), (21, 0))
        self.assertEqual(deviations(220, "F8"), (122, 50))

    def test_width(self):
        self.assertAlmostEqual(tolerance_width(22, "H7"), 0.021)


class TestGoNoGo(unittest.TestCase):
    def test_hole_go_is_lower(self):
        self.assertEqual(go_nogo(22, "H7"), (22.0, 22.021))

    def test_shaft_go_is_upper(self):
        self.assertEqual(go_nogo(22, "h7"), (22.0, 21.979))


class TestVerdict(unittest.TestCase):
    def test_single_value(self):
        # 22 H7: limits 22.000-22.021, width 0.021, near-limit band 0.0021.
        self.assertEqual(verdict_one(22.011, 22.0, 22.021), "OK")
        self.assertEqual(verdict_one(22.001, 22.0, 22.021), "Hati-Hati")
        self.assertEqual(verdict_one(22.021, 22.0, 22.021), "Hati-Hati")
        self.assertEqual(verdict_one(21.999, 22.0, 22.021), "Not OK")
        self.assertEqual(verdict_one(22.022, 22.0, 22.021), "Not OK")

    def test_row_verdict(self):
        # 220 F8: limits 220.050-220.122, width 0.072, near-limit band 0.0072.
        # Both ends well inside -> OK overall.
        self.assertEqual(
            verdict(220, "F8", go=220.08, nogo=220.09)["overall"], "OK"
        )
        # NO-GO actual above the upper limit -> Not OK overall.
        self.assertEqual(
            verdict(220, "F8", go=220.08, nogo=220.2)["overall"], "Not OK"
        )
        # GO actual 0.001 above the lower limit -> Hati-Hati overall.
        self.assertEqual(
            verdict(220, "F8", go=220.051, nogo=220.09)["overall"], "Hati-Hati"
        )


class TestCoverage(unittest.TestCase):
    def test_known_classes(self):
        classes = covered_classes()
        self.assertEqual(len(classes["shaft"]), 37)
        self.assertEqual(len(classes["hole"]), 35)
        self.assertIn("H7", classes["hole"])
        self.assertIn("h7", classes["shaft"])

    def test_out_of_range_nominal(self):
        with self.assertRaises(ValueError):
            limits(3, "H7")  # first step is over 3
        with self.assertRaises(ValueError):
            limits(400.5, "H7")
        with self.assertRaises(ValueError):
            limits(0, "H7")

    def test_uncovered_class(self):
        # D10, e8 and f8 are real ISO classes but not in the shipped tables.
        for cls in ("D10", "e8", "f8"):
            with self.assertRaises(ValueError, msg=cls):
                limits(22, cls)

    def test_bad_class_format(self):
        with self.assertRaises(ValueError):
            limits(22, "H")
        with self.assertRaises(ValueError):
            limits(22, "h7x")
        with self.assertRaises(ValueError):
            limits(22, "Hh7")


if __name__ == "__main__":
    unittest.main()
