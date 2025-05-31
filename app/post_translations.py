"""
# ---------------------------------------------------------------------
# post_translations.py
# app/post_translations.py
# Cleans .po files (removes fuzzy flags) and compiles to .mo for each language.
# ---------------------------------------------------------------------
"""

import os

import polib

from app.utils.load_languages import import_supported_languages

APP_DIR = os.path.abspath(os.path.dirname(__file__))
TRANSLATIONS_DIR = os.path.join(APP_DIR, "../app/translations")

print(f"🔍 Post-processing translations in: {TRANSLATIONS_DIR}")

SUPPORTED_LANGUAGES = import_supported_languages(APP_DIR)

print("\n🔁 Cleaning and compiling translations...")

# ---------------------------------------------------------------------
# Process each language directory: clean and compile
# ---------------------------------------------------------------------
for lang in SUPPORTED_LANGUAGES:
    lang_dir = os.path.join(TRANSLATIONS_DIR, lang, "LC_MESSAGES")
    po_path = os.path.join(lang_dir, "messages.po")
    mo_path = os.path.join(lang_dir, "messages.mo")

    if not os.path.exists(po_path):
        print(f"⚠️  No .po file found for '{lang}', skipping...")
        continue

    po = polib.pofile(po_path)

    # Remove fuzzy flags from all entries
    for entry in po:
        if "fuzzy" in entry.flags:
            entry.flags.remove("fuzzy")

    po.save()
    print(f"✅ Cleaned .po file for '{lang}'")

    # Compile to .mo file for Flask-Babel
    po.save_as_mofile(mo_path)
    print(f"📦 Compiled .mo for '{lang}'")

print("\n✅ Post-translation step complete.")

# ---------------------------------------------------------------------
# End of file: app/post_translations.py
# ---------------------------------------------------------------------
