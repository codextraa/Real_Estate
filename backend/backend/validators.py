# core_db/validators.py

import re
from decimal import Decimal


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


def validate_property_integers(beds, baths, sqft, price):
    bed_error = ""
    bath_error = ""
    sqft_error = ""
    price_error = ""

    if beds is not None and isinstance(beds, int):
        if beds <= 0:
            bed_error += "Beds cannot be negative or zero. "
        if len(str(abs(beds))) > 5:
            bed_error += "Beds cannot exceed 5 digits."

    if baths is not None and isinstance(baths, int):
        if baths <= 0:
            bath_error += "Baths cannot be negative or zero. "
        if len(str(abs(baths))) > 5:
            bath_error += "Baths cannot exceed 5 digits."

    if sqft is not None and isinstance(sqft, int):
        if sqft <= 100:
            sqft_error += "Area square footage cannot be less than 100 sqft. "
        if len(str(abs(sqft))) > 10:
            sqft_error += "Area square footage cannot exceed 10 digits."

    if price is not None and isinstance(price, (int, Decimal)):
        if price <= 10000:
            price_error = "Price cannot be less than $10,000."

    errors = {
        "beds": bed_error,
        "baths": bath_error,
        "area_sqft": sqft_error,
        "price": price_error,
    }

    return {k: v for k, v in errors.items() if v}
