"""
# ---------------------------------------------------------------------
# duration.py# app/utils/duration.py
# Utilities for working with duration fields (form <-> minutes).
# ---------------------------------------------------------------------
"""


def total_minutes_from_form_parts(form, prefix):
    """
    Compute total minutes from a form's duration fields with the given prefix.

    Args:
        form: Form object containing fields like <prefix>_years, <prefix>_months, etc.
        prefix: Field prefix as string.

    Returns:
        Total minutes as integer.
    """
    fields = [
        ("years", 60 * 24 * 365),
        ("months", 60 * 24 * 30),
        ("weeks", 60 * 24 * 7),
        ("days", 60 * 24),
        ("hours", 60),
        ("minutes", 1),
    ]

    total = 0
    for name, factor in fields:
        value = getattr(form, f"{prefix}_{name}").data or 0
        total += value * factor

    return total


# ---------------------------------------------------------------------
def load_minutes_into_form_parts(form, prefix, total_minutes):
    """
    Populate form fields (with prefix) from total minutes value.

    Args:
        form: Form object containing fields like <prefix>_days, <prefix>_hours, etc.
        prefix: Field prefix as string.
        total_minutes: Total minutes as integer.

    This sets .data on each form field with the decomposed value.
    """
    remainder = total_minutes
    units = {
        "years": 60 * 24 * 365,
        "months": 60 * 24 * 30,
        "weeks": 60 * 24 * 7,
        "days": 60 * 24,
        "hours": 60,
        "minutes": 1,
    }

    for unit, multiplier in units.items():
        value = remainder // multiplier
        field = getattr(form, f"{prefix}_{unit}", None)
        if field:
            field.data = value
        remainder %= multiplier

# ---------------------------------------------------------------------
def format_minutes_as_duration_parts(total_minutes):
    """
    Convert total minutes to a human-readable duration string
    in terms of years, months, weeks, days, hours, and minutes.

    Args:
        total_minutes: Total minutes to format.

    Returns:
        A string like "1 day, 3 hours" (omits zero units).
    """
    if total_minutes is None:
        return "—"
    remainder = total_minutes
    parts = []
    units = [
        ("year", 60 * 24 * 365),
        ("month", 60 * 24 * 30),
        ("week", 60 * 24 * 7),
        ("day", 60 * 24),
        ("hour", 60),
        ("minute", 1),
    ]

    for label, factor in units:
        amount = remainder // factor
        if amount:
            parts.append(f"{amount} {label}{'s' if amount != 1 else ''}")
        remainder %= factor

    return ", ".join(parts) if parts else "0 minutes"
