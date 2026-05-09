import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\TOC_Compile_Marksheet_SEM_IV_CE_IT_2026_T2.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

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
    if val in ('AB', 'UFM', '', '-', 'FEES PENDING', 'FEES'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}   # enrollment -> T2 TOC mark

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
            if tokens[-1] == 'PENDING' and tokens[-2] == 'FEES':
                mark = 0.0
            else:
                last = tokens[-1].strip()
                mark = parse_mark(last)

            pdf_records[enrollment] = mark

print(f"Parsed {len(pdf_records)} student records from T2 TOC PDF")

# ── Load JS file ──────────────────────────────────────────────────────────
with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

# ── ADD T2 TOC marks to existing toc field ──────────────────────────────────
updated  = 0
not_found = []

for student in data:
    enrollment = student.get('enrollment', '')
    if enrollment in pdf_records:
        t2 = pdf_records[enrollment]
        existing_toc = student.get('toc', 0) or 0
        
        student['toc'] = round(float(existing_toc) + t2, 1)
        student['toc2'] = t2
        
        # Re-calculate total
        total = float(student.get('dm', 0)) + float(student.get('coa', 0)) + student['toc'] + float(student.get('fcsp', 0)) + float(student.get('fsd2', 0))
        student['total'] = round(total, 1)
        
        updated += 1
    else:
        not_found.append(f"  {enrollment} - {student.get('name','?')}")

# ── Write back ─────────────────────────────────────────────────────────────
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Updated {updated} students (toc = T1 + T2 combined, toc2 added)")
print(f"{len(not_found)} students NOT found in T2 TOC PDF (unchanged)")
if not_found:
    for s in not_found[:20]:
        print(s)
    if len(not_found) > 20:
        print(f"  ... and {len(not_found)-20} more")
