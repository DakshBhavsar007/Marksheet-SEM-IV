import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\DM_Compile_Marksheet_SEM_IV_CE_IT_2026_T3.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

# ── 1. Parse T3 PDF and extract marks ────────────────────────────────────────

SKIP_PATTERNS = [
    r'^L J INSTITUTE',
    r'^L\. J\. INSTITUTE',
    r'^CE/IT',
    r'^MARKSHEET',
    r'^For Absent',
    r'^RANK',
    r'^NO\.',
    r'^---',
    r'^MENTOR',
    r'^ROLL',
    r'^DEPARTMENT'
]

def should_skip(line):
    for pat in SKIP_PATTERNS:
        if re.match(pat, line.strip(), re.IGNORECASE):
            return True
    return False

def parse_mark(val):
    val = val.strip()
    if val.upper() in ('AB', 'ABS', 'UFM', '', '-', 'PENDING', 'FEES PENDING'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}   # enrollment -> T3 DM mark

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or should_skip(line):
                continue

            # Find 14-digit enrollment
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue

            enrollment = m.group(1)
            tokens = line.split()
            
            # Check for fees pending
            if len(tokens) >= 2 and tokens[-1].upper() == 'PENDING' and tokens[-2].upper() == 'FEES':
                mark = 0.0
            else:
                last = tokens[-1].strip()
                mark = parse_mark(last)

            pdf_records[enrollment] = mark

print(f"Successfully parsed {len(pdf_records)} records from the T3 DM PDF.")

# ── 2. Load the JS file ──────────────────────────────────────────────────────

with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Strip JS wrapper
start_idx = js_content.find('[')
end_idx = js_content.rfind(']') + 1

if start_idx == -1 or end_idx == 0:
    print("Could not find JSON array in JS file.")
    exit(1)

json_str = js_content[start_idx:end_idx]
data = json.loads(json_str)

# ── 3. Update records ────────────────────────────────────────────────────────

updated_count = 0
not_found_in_pdf = []

for student in data:
    enroll = student.get("enrollment")
    dept = student.get("dept", "")
    
    if enroll in pdf_records:
        t3_mark = pdf_records[enroll]
        
        # Store individual T3 mark
        student["dm3"] = t3_mark
        
        # Add T3 mark to cumulative DM column
        existing_dm = student.get("dm", 0.0) or 0.0
        student["dm"] = round(float(existing_dm) + t3_mark, 1)
        
        # Recalculate total based on department rules:
        # - SY4: total = dm + coa + toc + python2 + fsd2
        # - SY1, SY2, SY3: total = dm + coa + toc + fcsp + fsd2
        dm = float(student.get("dm", 0.0))
        coa = float(student.get("coa", 0.0))
        toc = float(student.get("toc", 0.0))
        fsd2 = float(student.get("fsd2", 0.0))
        
        if dept == "SY4":
            python2 = float(student.get("python2", 0.0))
            total = dm + coa + toc + python2 + fsd2
        else:
            fcsp = float(student.get("fcsp", 0.0))
            total = dm + coa + toc + fcsp + fsd2
            
        student["total"] = round(total, 1)
        updated_count += 1
    else:
        not_found_in_pdf.append(student)

print(f"Updated {updated_count} students in JSON data.")
print(f"{len(not_found_in_pdf)} students from JS not found in PDF.")

# Print sample of not found students by department
depts_not_found = {}
for student in not_found_in_pdf:
    d = student.get("dept", "unknown")
    depts_not_found[d] = depts_not_found.get(d, 0) + 1

print("Summary of JS students not found in PDF by department:")
for d, count in depts_not_found.items():
    print(f"  - {d}: {count}")

# ── 4. Save the JS file ──────────────────────────────────────────────────────

new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_js_content)

print("Successfully wrote updates back to JS file.")
