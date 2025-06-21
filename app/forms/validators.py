"""
# ---------------------------------------------------------------------
# validators.py
# app/forms/validators.py
# Contains custom form field validators for Flask-WTForms.
# ---------------------------------------------------------------------
"""

# ------------------------ Imports (PEP8 order) -----------------------
import re

from flask_babel import lazy_gettext as _l
from wtforms.validators import ValidationError


# ---------------------------------------------------------------------
# validate_complex_password
# ---------------------------------------------------------------------
def validate_complex_password(form, field):
    """
    Validates that a password meets complexity requirements:
      - At least 8 characters.
      - Contains at least one uppercase letter.
      - Contains at least one lowercase letter.
      - Contains at least one digit.
      - Contains at least one special character.

    Args:
        form: The form instance.
        field: The field containing the password string.

    Raises:
        ValidationError: If the password does not meet requirements.
    """
    pw = field.data
    # Explanation: Each requirement increases password strength,
    # helping protect against brute-force attacks.
    if (
        len(pw) < 8
        or not re.search(r"[A-Z]", pw)
        or not re.search(r"[a-z]", pw)
        or not re.search(r"\d", pw)
        or not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", pw)
    ):
        raise ValidationError(
            _l(
                "Password must be 8+ characters and include upper, lower, number, and special character."
            )
        )
