#!/bin/bash

# -----------------------------------------------------------------------------
# update_translations.sh
# Extract, update, and compile translation catalogs (excluding manual msgstr edits)
# -----------------------------------------------------------------------------

set -e

# Configuration
BABEL_CFG="app/babel.cfg"
TRANSLATIONS_DIR="app/translations"
POT_FILE="${TRANSLATIONS_DIR}/messages.pot"

# All supported languages
LANGUAGES=($(<app/translations/language_list.txt))

echo "📦 Updating Grylli translations"
echo "----------------------------------------"

# Step 1: Extract all translatable strings from Python + HTML
echo "🔍 Extracting messages..."
pybabel extract -F "$BABEL_CFG" -o "$POT_FILE" .

# Step 2: Initialize any new language catalogs that do not yet exist
echo "🛠️  Initializing missing languages..."
for lang in "${LANGUAGES[@]}"; do
  PO_PATH="${TRANSLATIONS_DIR}/${lang}/LC_MESSAGES/messages.po"
  if [[ ! -f "$PO_PATH" ]]; then
    echo "  → Initializing $lang"
    pybabel init -i "$POT_FILE" -d "$TRANSLATIONS_DIR" -l "$lang"
  else
    echo "  → $lang already exists"
  fi
done

# Step 3: Update all language catalogs with new strings
echo "🔄 Updating catalogs..."
pybabel update -i "$POT_FILE" -d "$TRANSLATIONS_DIR"

# ⬇️ NEW Step 3.5: Fill English msgstr fields if empty
echo "📝 Filling msgstr fields in English .po file..."
PYTHONPATH=. python3 app/translations/fill_en_msgstr.py || {
  echo "❌ Failed to run fill_en_msgstr.py"
  exit 1
}

# Step 4: Compile all .po files into .mo files
echo "⚙️  Compiling .mo files..."
pybabel compile -d "$TRANSLATIONS_DIR"

echo "✅ All translations extracted, updated, and compiled."
echo "✍️  Remember: Edit the .po files manually or with a translation tool to provide msgstr translations."
