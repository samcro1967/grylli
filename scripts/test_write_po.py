from babel.messages.pofile import read_po, write_po
from pathlib import Path

po_path = Path("app/translations/es/LC_MESSAGES/messages.po")
out_path = Path("app/translations/es/LC_MESSAGES/test_write.po")

with po_path.open("r", encoding="utf-8") as f:
    catalog = read_po(f)

with out_path.open("w", encoding="utf-8") as f:
    write_po(f, catalog)
