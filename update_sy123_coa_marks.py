import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compile _Marksheet_COA_SEM_IV_CE_IT_2026_T2.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

SKIP_PATTERNS = [
    r'^L J INSTITUTE',
    r'^CE/IT-',
    r'^MARKSHEET',
    r'^For Absent',
    r'^MENTOR',
    r'^RANK',
    r'^NO\.',
    r'^---'
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

pdf_records = {}   # enrollment -> T2 COA mark

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or should_skip(line):
                continue
            
            # Extract enrollment (14 digits)
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue
                
            enrollment = m.group(1)
            
            # The line looks like:
            # 1 SY-1 AIDS 61 24002170510031 A2 PATEL MAHI SAMIR DKU 25.0
            tokens = line.split()
            
            # dept could be SY-1, SY-2, SY-3, SY-4
            # We want to skip SY-4 if the prompt specifically said SY1, SY2, SY3
            # Or we can just extract all and filter later. Let's filter later, or filter here.
            # actually checking the token that starts with SY-
            is_sy4 = False
            for t in tokens:
                if t == 'SY-4':
                    is_sy4 = True
                    break
            
            if is_sy4:
                continue # The user asked to add for SY1, SY2, SY3
                
            if tokens[-1] == 'PENDING' and tokens[-2] == 'FEES':
                mark = 0.0
            else:
                last = tokens[-1].strip()
                mark = parse_mark(last)
                
            pdf_records[enrollment] = mark

print(f"Parsed {len(pdf_records)} student records for SY1, SY2, SY3 from T2 COA PDF")

# ── Load JS file ─────────────────────────────────────────────────────────────
with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

# ── ADD T2 COA marks to existing coa field, and update total ─────────────────
updated  = 0
not_found = []

for student in data:
    enrollment = student.get('enrollment', '')
    if enrollment in pdf_records:
        t2 = pdf_records[enrollment]
        existing_coa = student.get('coa', 0) or 0
        
        # In new_datamarksheet.js, existing_coa is likely T1 marks.
        # But wait, did they already have some coa marks?
        # In the previous conversation, `update_coa_marks.py` added `t2` to `existing_coa`.
        student['coa'] = round(float(existing_coa) + t2, 1)
        student['coa2'] = t2
        
        # Re-calculate total
        total = float(student.get('dm', 0)) + student['coa'] + float(student.get('toc', 0)) + float(student.get('fcsp', 0)) + float(student.get('fsd2', 0))
        student['total'] = round(total, 1)
        
        updated += 1
    else:
        # Check if they are SY1, SY2, SY3 and not found
        if student.get('dept') in ['SY1', 'SY2', 'SY3']:
            not_found.append(f"  {enrollment} - {student.get('name','?')}")

# ── Write back ────────────────────────────────────────────────────────────────
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Updated {updated} students (coa = T1 + T2 combined, coa2 added)")
print(f"{len(not_found)} SY1/SY2/SY3 students NOT found in T2 COA PDF (unchanged)")
