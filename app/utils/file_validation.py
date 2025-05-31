"""
# ---------------------------------------------------------------------
# file_validation.py
# app/utils/file_validation.py
# Validates uploaded files by type and size for Grylli.
# ---------------------------------------------------------------------
"""

import os

from flask import current_app
from werkzeug.datastructures import FileStorage


# ---------------------------------------------------------------------
# is_file_allowed
# ---------------------------------------------------------------------
def is_file_allowed(file: FileStorage) -> bool:
    """
    Checks whether the uploaded file is allowed based on its extension and MIME type.

    Args:
        file: Flask FileStorage object.

    Returns:
        True if allowed, False otherwise.
    """
    filename = file.filename
    content_type = file.content_type

    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = current_app.config.get("ALLOWED_UPLOAD_EXTENSIONS", set())
    allowed_mime = current_app.config.get("ALLOWED_UPLOAD_MIME_TYPES", set())

    if ext not in allowed_exts:
        return False

    if content_type not in allowed_mime:
        return False

    return True


# ---------------------------------------------------------------------
# is_file_size_valid
# ---------------------------------------------------------------------
def is_file_size_valid(file: FileStorage) -> bool:
    """
    Checks whether the uploaded file is within the allowed size limit.

    Args:
        file: Flask FileStorage object.

    Returns:
        True if file size is valid, False otherwise.
    """
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)  # Reset pointer

    max_mb = current_app.config.get("MAX_UPLOAD_SIZE_MB", 10)
    return size_mb <= max_mb


# ---------------------------------------------------------------------
# End of file: app/utils/file_validation.py
# ---------------------------------------------------------------------
