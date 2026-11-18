"""
Password generation logic: validation, secure generation and strength rating.

Kept separate from the GUI so it can be tested on its own.
Uses the `secrets` module (cryptographically secure), never `random`.
"""

import secrets
import string

# Character groups the user can choose from
CHARACTER_SETS = {
    "upper": string.ascii_uppercase,
    "lower": string.ascii_lowercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?/",
}

LABELS = {
    "upper": "Uppercase (A-Z)",
    "lower": "Lowercase (a-z)",
    "digits": "Numbers (0-9)",
    "symbols": "Symbols (!@#$...)",
}

# Characters that are easy to confuse when reading or typing a password
AMBIGUOUS = set("0Oo1lI|")

MIN_LENGTH = 8
MAX_LENGTH = 64
MIN_TYPES = 2

_rng = secrets.SystemRandom()


class PasswordError(ValueError):
    """Raised when the requested password settings are not valid."""


def parse_length(raw):
    """Convert user input into a valid password length."""
    text = str(raw).strip()
    if not text:
        raise PasswordError("Please enter a password length.")
    try:
        length = int(text)
    except ValueError:
        raise PasswordError("Length must be a whole number (e.g. 16).")
    if length < MIN_LENGTH:
        raise PasswordError(f"Length must be at least {MIN_LENGTH} characters.")
    if length > MAX_LENGTH:
        raise PasswordError(f"Length can be at most {MAX_LENGTH} characters.")
    return length


def build_sets(selected, exclude_ambiguous=False):
    """Return the character strings for the selected groups."""
    selected = [name for name in selected if name in CHARACTER_SETS]
    if len(selected) < MIN_TYPES:
        raise PasswordError(f"Select at least {MIN_TYPES} character types.")
    sets = []
    for name in selected:
        chars = CHARACTER_SETS[name]
        if exclude_ambiguous:
            chars = "".join(c for c in chars if c not in AMBIGUOUS)
        sets.append(chars)
    return sets


def generate_password(length, selected, exclude_ambiguous=False):
    """
    Generate a secure password.

    Guarantees at least one character from every selected group, fills the
    rest from the combined pool, then shuffles so the guaranteed characters
    are not always at the start.
    """
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise PasswordError(f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")
    sets = build_sets(selected, exclude_ambiguous)

    chars = [secrets.choice(group) for group in sets]      # one from each group
    pool = "".join(sets)
    chars += [secrets.choice(pool) for _ in range(length - len(chars))]
    _rng.shuffle(chars)                                     # secure shuffle
    return "".join(chars)


def password_strength(password):
    """
    Rate a password as Weak / Medium / Strong.

    Score: +1 for length >= 12, +1 for length >= 16, +1 for each character
    group present (max 4).  0-3 Weak, 4-5 Medium, 6 Strong.
    Returns (label, score, colour).
    """
    score = 0
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    for group in CHARACTER_SETS.values():
        if any(c in group for c in password):
            score += 1

    if score <= 3:
        return "Weak", score, "#dc2626"
    if score <= 5:
        return "Medium", score, "#f59e0b"
    return "Strong", score, "#16a34a"


if __name__ == "__main__":
    # Simple command-line mode (Beginner tier)
    print("=== Random Password Generator (CLI) ===")
    while True:
        try:
            length = parse_length(input(f"Length ({MIN_LENGTH}-{MAX_LENGTH}): "))
            chosen = [name for name in CHARACTER_SETS
                      if input(f"Include {LABELS[name]}? (y/n): ").strip().lower() == "y"]
            pwd = generate_password(length, chosen)
        except PasswordError as err:
            print(f"Error: {err}\n")
            continue
        label, _, _ = password_strength(pwd)
        print(f"\nPassword: {pwd}\nStrength: {label}\n")
        if input("Generate another? (y/n): ").strip().lower() != "y":
            break
