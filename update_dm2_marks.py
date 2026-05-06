import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compile _Marksheet_DM_SEM_IV_CE_IT_2026_T2.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

# ── 1. Extract all student rows from PDF ────────────────────────────────────
# Format: RANK SY-X BRANCH ROLLNO ENROLLMENT DIV NAME... MENTOR MARK
# Example: 11 SY-4 CST 33 24002171310139 D1 RUTVI VASOYA PCS 23.0

SKIP_PATTERNS = [
    r'^L J INSTITUTE',
    r'^L\. J\. INSTITUTE',
    r'^CE/IT',
    r'^MARKSHEET',
    r'^For Absent',
    r'^---',
]

def should_skip(line):
    for pat in SKIP_PATTERNS:
        if re.match(pat, line.strip(), re.IGNORECASE):
            return True
    return False

def parse_mark(val):
    val = val.strip()
    if val in ('AB', 'UFM', '', '-'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}   # enrollment -> T2 DM mark

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or should_skip(line):
                continue

            # Must contain a 14-digit enrollment number
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue

            enrollment = m.group(1)

            # Mark is the last token on the line
            tokens = line.split()
            last = tokens[-1].strip()
            mark = parse_mark(last)

            pdf_records[enrollment] = mark

print(f"Parsed {len(pdf_records)} student records from T2 DM PDF")

# ── 2. Load JS file ──────────────────────────────────────────────────────────
with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

# ── 3. ADD T2 DM marks to existing dm field ──────────────────────────────────
updated  = 0
not_found = []

for student in data:
    enrollment = student.get('enrollment', '')
    if enrollment in pdf_records:
        t2 = pdf_records[enrollment]
        existing_dm = student.get('dm', 0) or 0
        student['dm'] = round(float(existing_dm) + t2, 1)
        updated += 1
    else:
        not_found.append(f"  {enrollment} - {student.get('name','?')}")

# ── 4. Write back ─────────────────────────────────────────────────────────────
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Updated {updated} students  (dm = T1 + T2 combined)")
print(f"{len(not_found)} students NOT found in T2 DM PDF (unchanged)")
if not_found:
    for s in not_found[:20]:
        print(s)
    if len(not_found) > 20:
        print(f"  ... and {len(not_found)-20} more")
