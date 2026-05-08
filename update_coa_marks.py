import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Marksheet_SY4_SEM-IV_COA_T2_2026.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

SKIP_PATTERNS = [
    r'^L J INSTITUTE',
    r'^SY-4 Engineering',
    r'^CST/CS&IT/CSE-CS/MA&CP',
    r'^Subject Name',
    r'^Subject Code',
    r'^N\.B',
    r'^Short',
    r'^Sr No',
    r'^No',
    r'^---',
    r'^Mentors'
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
            
            # For fees pending, it might appear as "FEES PENDING" at the end
            # Let's just find the enrollment
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue
                
            enrollment = m.group(1)
            
            # The last token or two tokens might be marks or "FEES PENDING"
            tokens = line.split()
            if tokens[-1] == 'PENDING' and tokens[-2] == 'FEES':
                mark = 0.0
            else:
                last = tokens[-1].strip()
                mark = parse_mark(last)
                
            pdf_records[enrollment] = mark

print(f"Parsed {len(pdf_records)} student records from T2 COA PDF")

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
        
        # update coa
        student['coa'] = round(float(existing_coa) + t2, 1)
        
        # Update coa2 to keep track of t2 marks? The user said "add to coa column". 
        # For dm they also saved dm2 as t2 marks. I'll save coa2 as well just in case.
        student['coa2'] = t2
        
        # Re-calculate total
        # student['total'] = student['dm'] + student['coa'] + student['toc'] + student['fcsp'] + student['fsd2']
        total = float(student.get('dm', 0)) + student['coa'] + float(student.get('toc', 0)) + float(student.get('fcsp', 0)) + float(student.get('fsd2', 0))
        student['total'] = round(total, 1)
        
        updated += 1
    else:
        if student.get('dept') == 'SY4':
            not_found.append(f"  {enrollment} - {student.get('name','?')}")

# ── Write back ────────────────────────────────────────────────────────────────
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Updated {updated} students (coa = T1 + T2 combined, coa2 added)")
print(f"{len(not_found)} SY4 students NOT found in T2 COA PDF (unchanged)")
if not_found:
    for s in not_found[:20]:
        print(s)
    if len(not_found) > 20:
        print(f"  ... and {len(not_found)-20} more")
