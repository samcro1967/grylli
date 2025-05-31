# ---------------------------------------------------------------------
# save_languages.py
# Extracts SUPPORTED_LANGUAGES from config.py and saves to language_list.txt
# ---------------------------------------------------------------------

import os
from pathlib import Path
from app.config import SUPPORTED_LANGUAGES

output_file = Path(__file__).parent / "language_list.txt"

with open("app/translations/language_list.txt", "w") as f:
    for lang in SUPPORTED_LANGUAGES.keys():
        f.write(f"{lang}\n")

print(f"✅ Language list saved to: {output_file}")
