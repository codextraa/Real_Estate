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
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")

    return {"password": errors}


def validate_property_integers(beds, baths, sqft):
    bed_error = ""
    bath_error = ""
    sqft_error = ""

    if beds is not None and isinstance(beds, int) and len(str(abs(beds))) > 5:
        bed_error = "Beds cannot exceed 5 digits."

    if baths is not None and isinstance(baths, int) and len(str(abs(baths))) > 5:
        bath_error = "Baths cannot exceed 5 digits."

    if sqft is not None and isinstance(sqft, int) and len(str(abs(sqft))) > 10:
        sqft_error = "Area square footage cannot exceed 10 digits."

    errors = {"beds": bed_error, "baths": bath_error, "area_sqft": sqft_error}

    return {k: v for k, v in errors.items() if v}
