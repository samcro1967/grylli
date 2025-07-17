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

from app.utils.logging import log_exception_with_traceback, log_info_message


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
    try:
        filename = file.filename
        content_type = file.content_type

        ext = os.path.splitext(filename)[1].lower()
        allowed_exts = current_app.config.get("ALLOWED_UPLOAD_EXTENSIONS", set())
        allowed_mime = current_app.config.get("ALLOWED_UPLOAD_MIME_TYPES", set())

        if ext not in allowed_exts:
            log_info_message(f"Upload blocked: Extension '{ext}' not allowed.")
            return False

        if content_type not in allowed_mime:
            log_info_message(f"Upload blocked: MIME type '{content_type}' not allowed.")
            return False

        return True

    except Exception as e:
        log_exception_with_traceback("Error during file extension or MIME type validation", e)
        return False


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
    try:
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)  # Reset pointer

        max_mb = current_app.config.get("MAX_UPLOAD_SIZE_MB", 10)
        if size_mb > max_mb:
            log_info_message(f"Upload blocked: File size {size_mb:.2f}MB exceeds {max_mb}MB limit.")
            return False

        return True

    except Exception as e:
        log_exception_with_traceback("Error checking uploaded file size", e)
        return False
