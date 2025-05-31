#!/bin/bash
set -e

# https://github.com/pescheckit/python-gpt-po
# pip install openai gpt_po translate
# export OPENAI_API_KEY=<YOUR_API_KEY>
# https://platform.openai.com/settings/organization/usage

# Step 1: Generate langs.tmp
PYTHONPATH=. python3 tools/print_langs.py

# Step 2: Read language codes from langs.tmp
LANGS=$(cat langs.tmp)

# Step 3: Show for debugging
echo "LANGS: $LANGS"

# Step 4: Run the translation command
gpt-po-translator \
    --folder ./app/translations \
    --lang "$LANGS" \
    --bulk \
    --bulksize 40 \
    --model gpt-4o

# Step 5: Clean up
rm -f langs.tmp
