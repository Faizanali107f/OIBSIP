"""Unit tests for the password logic. Run: python -m unittest test_generator.py"""

import string
import unittest

from generator import (
    AMBIGUOUS,
    CHARACTER_SETS,
    PasswordError,
    generate_password,
    parse_length,
    password_strength,
)

ALL = list(CHARACTER_SETS)


class TestGeneration(unittest.TestCase):
    def test_length_is_exact(self):
        for length in (8, 12, 16, 32, 64):
            self.assertEqual(len(generate_password(length, ALL)), length)

    def test_every_selected_type_is_present(self):
        # Short passwords are where a naive generator fails, so repeat many times
        for _ in range(500):
            pwd = generate_password(8, ALL)
            for name, chars in CHARACTER_SETS.items():
                self.assertTrue(any(c in chars for c in pwd), f"{name} missing in {pwd}")

    def test_only_selected_types_used(self):
        for _ in range(200):
            pwd = generate_password(12, ["upper", "digits"])
            self.assertTrue(all(c in string.ascii_uppercase + string.digits for c in pwd))

    def test_exclude_ambiguous(self):
        for _ in range(300):
            pwd = generate_password(20, ALL, exclude_ambiguous=True)
            self.assertFalse(set(pwd) & AMBIGUOUS, pwd)

    def test_passwords_differ(self):
        self.assertEqual(len({generate_password(16, ALL) for _ in range(100)}), 100)


class TestValidation(unittest.TestCase):
    def test_bad_lengths(self):
        for bad in ("", "abc", "5", "7", "65", "12.5"):
            with self.assertRaises(PasswordError):
                parse_length(bad)

    def test_good_length(self):
        self.assertEqual(parse_length(" 16 "), 16)

    def test_needs_two_types(self):
        with self.assertRaises(PasswordError):
            generate_password(12, ["lower"])
        with self.assertRaises(PasswordError):
            generate_password(12, [])


class TestStrength(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(password_strength("abcdefgh")[0], "Weak")
        self.assertEqual(password_strength("abcd1234")[0], "Weak")
        self.assertEqual(password_strength("Abcd1234!xyz")[0], "Medium")
        self.assertEqual(password_strength("Abcd1234!xyzQRS9")[0], "Strong")


if __name__ == "__main__":
    unittest.main()
