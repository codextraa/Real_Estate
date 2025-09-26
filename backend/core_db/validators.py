# core_db/validators.py

import re
from django.core.exceptions import ValidationError

def validate_password_complexity(password): # pylint: disable=inconsistent-return-statements
    """
    Checks if the password meets complexity requirements:
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    """
    if not password:
        return

    if (
        len(password) < 8
        or not re.search(r"[a-z]", password)
        or not re.search(r"[A-Z]", password)
        or not re.search(r"[0-9]", password)
        or not re.search(r"[!@#$%^&*(),.?\":{}|<>[\]~/\\']", password)
    ):
        raise ValidationError(
            "Password must contain at least 8 characters, "
            "including an uppercase letter, a lowercase letter, "
            "a number, and a special character."
        )

    return password
