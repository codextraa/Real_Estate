# core_db/validators.py

import re


def validate_password_complexity(password):
    """
    Checks if the password meets complexity requirements:
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    Returns a dictionary of errors if any, else an empty dictionary.
    """
    errors = []

    # Password validation rules
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")

    return {"password": errors}
