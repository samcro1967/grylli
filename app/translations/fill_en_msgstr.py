from pathlib import Path

po_path = Path("app/translations/en/LC_MESSAGES/messages.po")
output = []

with po_path.open(encoding="utf-8") as f:
    lines = f.readlines()

in_msgid = False
msgid = ""

for line in lines:
    if line.startswith('msgid "') and not line.startswith('msgid ""'):
        msgid = line.strip().split('msgid ')[1]
        in_msgid = True
        output.append(line)
    elif line.startswith('msgstr ""') and in_msgid:
        output.append(f'msgstr {msgid}\n')
        in_msgid = False
    else:
        output.append(line)

po_path.write_text("".join(output), encoding="utf-8")
print("✅ Filled empty English msgstr fields only where safe.")
