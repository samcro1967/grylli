# ---------------------------------------------------------------------
# file_validation.py
# Validates uploaded files by type and size for Grylli
# ---------------------------------------------------------------------

import os
from werkzeug.datastructures import FileStorage

# ---------------------------------------------------------------------
# Configuration: Allowed extensions and MIME types
# ---------------------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".docx", ".xlsx", ".pptx", ".jpg", ".jpeg", ".png", ".csv"
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg",
    "image/png",
    "text/csv",
}

MAX_FILE_SIZE_MB = 10  # 10 MB max file size

# ---------------------------------------------------------------------
# Function: is_file_allowed
# ---------------------------------------------------------------------

def is_file_allowed(file: FileStorage) -> bool:
    """
    Checks whether the uploaded file is allowed based on its extension and MIME type.

    Args:
        file (FileStorage): The uploaded file object from Flask.

    Returns:
        bool: True if file is valid, False otherwise.
    """
    filename = file.filename
    content_type = file.content_type

    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # Check MIME type
    if content_type not in ALLOWED_MIME_TYPES:
        return False

    return True

# ---------------------------------------------------------------------
# Function: is_file_size_valid
# ---------------------------------------------------------------------

def is_file_size_valid(file: FileStorage) -> bool:
    """
    Checks whether the uploaded file is within the allowed size limit.

    Args:
        file (FileStorage): The uploaded file object.

    Returns:
        bool: True if size is acceptable, False if too large.
    """
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)  # Reset pointer for downstream use

    return size_mb <= MAX_FILE_SIZE_MB
