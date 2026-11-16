"""
BMI logic: input validation, calculation and category classification.

Kept separate from the GUI so it can be tested on its own.
"""

# (upper_limit_exclusive, name, colour) — WHO adult BMI categories
CATEGORIES = [
    (18.5, "Underweight", "#3b82f6"),   # blue
    (25.0, "Normal", "#16a34a"),        # green
    (30.0, "Overweight", "#f59e0b"),    # amber
    (float("inf"), "Obese", "#dc2626"), # red
]

# Sensible limits so typos like 1750 (cm typed as m) are caught
WEIGHT_RANGE = (2.0, 500.0)   # kg
HEIGHT_RANGE = (0.5, 2.75)    # metres


class InputError(ValueError):
    """Raised when the user's weight or height input is not valid."""


def parse_positive_number(raw, field_name, valid_range):
    """Convert text input into a float and check it's inside a valid range."""
    text = str(raw).strip()
    if not text:
        raise InputError(f"Please enter your {field_name}.")
    try:
        value = float(text)
    except ValueError:
        raise InputError(f"{field_name.capitalize()} must be a number (e.g. 70 or 1.75).")
    if value <= 0:
        raise InputError(f"{field_name.capitalize()} must be greater than zero.")
    low, high = valid_range
    if not low <= value <= high:
        raise InputError(
            f"{field_name.capitalize()} should be between {low:g} and {high:g}. "
            "Please check your input."
        )
    return value


def calculate_bmi(weight_kg, height_m):
    """BMI = weight (kg) / height (m)^2, rounded to 2 decimal places."""
    if weight_kg <= 0 or height_m <= 0:
        raise InputError("Weight and height must be greater than zero.")
    return round(weight_kg / (height_m ** 2), 2)


def classify_bmi(bmi):
    """Return (category_name, colour) for a BMI value."""
    for upper, name, colour in CATEGORIES:
        if bmi < upper:
            return name, colour
    return CATEGORIES[-1][1], CATEGORIES[-1][2]


if __name__ == "__main__":
    # Simple command-line mode (Beginner tier)
    print("=== BMI Calculator (CLI) ===")
    while True:
        try:
            w = parse_positive_number(input("Weight (kg): "), "weight", WEIGHT_RANGE)
            h = parse_positive_number(input("Height (m): "), "height", HEIGHT_RANGE)
        except InputError as err:
            print(f"Error: {err}\n")
            continue
        value = calculate_bmi(w, h)
        category, _ = classify_bmi(value)
        print(f"Your BMI is {value:.2f} — {category}\n")
        if input("Calculate again? (y/n): ").strip().lower() != "y":
            break
