"""Unit tests for the BMI logic and database. Run: python -m unittest test_bmi.py"""

import os
import tempfile
import unittest

from bmi import InputError, calculate_bmi, classify_bmi, parse_positive_number
from database import BMIDatabase, DatabaseError


class TestBMILogic(unittest.TestCase):
    def test_calculation_rounded(self):
        self.assertEqual(calculate_bmi(70, 1.75), 22.86)

    def test_categories(self):
        self.assertEqual(classify_bmi(18.4)[0], "Underweight")
        self.assertEqual(classify_bmi(18.5)[0], "Normal")
        self.assertEqual(classify_bmi(24.99)[0], "Normal")
        self.assertEqual(classify_bmi(25)[0], "Overweight")
        self.assertEqual(classify_bmi(29.99)[0], "Overweight")
        self.assertEqual(classify_bmi(30)[0], "Obese")

    def test_rejects_bad_input(self):
        for bad in ("", "abc", "-70", "0", "1750"):
            with self.assertRaises(InputError):
                parse_positive_number(bad, "height", (0.5, 2.75))

    def test_accepts_good_input(self):
        self.assertEqual(parse_positive_number(" 1.8 ", "height", (0.5, 2.75)), 1.8)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = BMIDatabase(os.path.join(self.tmp, "test.db"))

    def tearDown(self):
        self.db.close()

    def test_multi_user_records(self):
        self.db.add_record("Ali", 70, 1.75, 22.86, "Normal")
        self.db.add_record("Sara", 55, 1.6, 21.48, "Normal")
        self.db.add_record("ali", 72, 1.75, 23.51, "Normal")  # same user, case-insensitive
        self.assertEqual(self.db.get_users(), ["Ali", "Sara"])
        self.assertEqual(len(self.db.get_records("Ali")), 2)

    def test_delete(self):
        self.db.add_record("Ali", 70, 1.75, 22.86, "Normal")
        rec = self.db.get_records("Ali")[0]
        self.db.delete_record(rec["id"])
        self.assertEqual(self.db.get_records("Ali"), [])
        self.db.delete_user("Ali")
        self.assertEqual(self.db.get_users(), [])

    def test_empty_name_rejected(self):
        with self.assertRaises(DatabaseError):
            self.db.add_record("  ", 70, 1.75, 22.86, "Normal")

    def test_bad_path_raises(self):
        with self.assertRaises(DatabaseError):
            BMIDatabase("/nonexistent/folder/x.db")


if __name__ == "__main__":
    unittest.main()
