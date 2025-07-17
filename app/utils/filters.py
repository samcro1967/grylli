"""
# ---------------------------------------------------------------------
# filters.py
# app/utils/filters.py
# Custom Jinja filter for formatting file sizes.
# ---------------------------------------------------------------------
"""


def filesizeformat(value):
    """
    Format a file size (in bytes) as a human-readable string (KB, MB, etc.).

    Args:
        value: File size in bytes.

    Returns:
        Human-readable file size string.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return "0 bytes"
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if value < 1024.0 or unit == "TB":
            return f"{value:3.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"
