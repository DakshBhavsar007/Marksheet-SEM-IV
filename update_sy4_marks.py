import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\SY4_SEM_IV_T1_MARKSHEET.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

# ── 1. Extract all student rows from PDF ────────────────────────────────────
# Header pattern to skip:  ROLL NO, DIV, BRANCH, Enrollment, NAME, Mentor, marks...
# Data row example:
#   187 D6 CST 24002171310111 PATEL DHRUMISH TUSHAR MVK 17 4 6.5 16 17

SKIP_PATTERNS = [
    r'^L\. J\. Institute',
    r'^SY4 DEPARTMENT',
    r'^Compiled Marksheet',
    r'^SUBJECT NAME',
    r'^ROLL',
    r'^DIV BRANCH',
    r'^NO\.',
    r'^---',
]

def should_skip(line):
    for pat in SKIP_PATTERNS:
        if re.match(pat, line.strip()):
            return True
    return False

# Mentors list helps us split NAME from MENTOR
MENTORS = {'SDP','ZPB','DVB','PCS','FRT','ZVB','MPH','PKP','MVK','SHG','SHP',
           'DAM','ZPB','ZVB','FRT','SDP'}

def parse_mark(val):
    val = val.strip()
    if val in ('AB', 'UFM', '', '-'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}   # enrollment -> {dm, coa, toc, fcsp, fsd2}

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or should_skip(line):
                continue

            # Try to match a data row
            # Format: ROLL DIV BRANCH ENROLLMENT NAME... MENTOR DM COA TOC FCSP FSD2
            # Numbers at end: 5 values (could be negative, AB, UFM)
            # Enrollment: 14-digit number
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue

            enrollment = m.group(1)

            # Extract 5 marks at the end of the line
            # Marks can be: number, AB, UFM, or negative number
            marks_pattern = r'([\d.]+|AB|UFM|-[\d.]+)\s+([\d.]+|AB|UFM|-[\d.]+)\s+([\d.]+|AB|UFM|-[\d.]+)\s+([\d.]+|AB|UFM|-[\d.]+)\s+([\d.]+|AB|UFM|-[\d.]+)\s*$'
            mm = re.search(marks_pattern, line)
            if not mm:
                continue

            dm   = parse_mark(mm.group(1))
            coa  = parse_mark(mm.group(2))
            toc  = parse_mark(mm.group(3))
            fcsp = parse_mark(mm.group(4))
            fsd2 = parse_mark(mm.group(5))

            pdf_records[enrollment] = {
                'dm':   dm,
                'coa':  coa,
                'toc':  toc,
                'fcsp': fcsp,
                'fsd2': fsd2,
            }

print(f"✅ Parsed {len(pdf_records)} student records from PDF")

# ── 2. Load JS file, update matching records ─────────────────────────────────
with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Strip the JS wrapper to get JSON
json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

updated = 0
not_found = []

for student in data:
    enrollment = student.get('enrollment', '')
    if enrollment in pdf_records:
        marks = pdf_records[enrollment]
        student['dm']     = marks['dm']
        student['coa']    = marks['coa']
        student['toc']    = marks['toc']
        student['fcsp']   = marks['fcsp']
        student['fsd2']   = marks['fsd2']

        # Recalculate total (dm + coa + toc + fcsp + fsd2)
        total = marks['dm'] + marks['coa'] + marks['toc'] + marks['fcsp'] + marks['fsd2']
        student['total'] = round(total, 1)

        updated += 1
    else:
        if student.get('dept') == 'SY4':
            not_found.append(f"  {enrollment} - {student.get('name','?')}")

# ── 3. Write back ─────────────────────────────────────────────────────────────
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Updated {updated} students in new_datamarksheet.js")
if not_found:
    print(f"⚠️  {len(not_found)} SY4 students NOT found in PDF:")
    for s in not_found:
        print(s)
else:
    print("✅ All SY4 students found and updated!")
