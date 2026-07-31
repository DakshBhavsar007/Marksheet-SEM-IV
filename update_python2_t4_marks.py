"""
Update Python-2 T4 marks from Combined_Marksheet_PYTHON-2_SemIV.pdf
into new_datamarksheet.js (adding 'python24' field).

Uses PyMuPDF (fitz) table extraction for accurate parsing.
"""

import fitz  # PyMuPDF
import re
import json
import os

PDF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Combined_Marksheet_PYTHON-2_SemIV.pdf')
JS_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_datamarksheet.js')

# ── 1. Parse PDF tables and extract T4 marks ─────────────────────────────────

def parse_mark(val):
    """Convert a mark value string to float. AB/ABS/Admin -> 0.0"""
    if val is None:
        return 0.0
    val = val.strip().replace('\n', ' ')
    if val.upper() in ('AB', 'ABS', 'UFM', '', '-', 'PENDING', 'FEES PENDING', 'ADMIN'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}  # enrollment -> T4 mark

doc = fitz.open(PDF_PATH)
print(f"Opened PDF: {PDF_PATH} ({len(doc)} pages)")

for page_num, page in enumerate(doc):
    tables = page.find_tables()
    if not tables:
        continue
    for table in tables:
        rows = table.extract()
        if not rows or len(rows) < 2:
            continue
        
        # Verify header structure (columns: RANK, BATCH, ROLL NO, ENROLLMENT NO, DEPT, NAME, T1, T2, T3, T4, TOTAL)
        header = rows[0]
        if len(header) < 11:
            continue
        
        # Process data rows (skip header row)
        for row in rows[1:]:
            if len(row) < 11:
                continue
            
            enrollment = row[3]
            if enrollment is None:
                continue
            enrollment = enrollment.strip().replace('\n', '')
            
            # Validate enrollment number (14 digits starting with 2)
            if not re.match(r'^2\d{13}$', enrollment):
                continue
            
            t4_val = row[9]  # T4 is at index 9
            t4_mark = parse_mark(t4_val)
            
            pdf_records[enrollment] = t4_mark

doc.close()

print(f"Successfully parsed {len(pdf_records)} T4 records from the Python-2 Combined Marksheet PDF.")

# Print sample records for verification
items = list(pdf_records.items())
print("\nFirst 5 records:")
for enr, mark in items[:5]:
    print(f"  {enr}: T4 = {mark}")
print("Last 5 records:")
for enr, mark in items[-5:]:
    print(f"  {enr}: T4 = {mark}")

# ── 2. Load the JS file ──────────────────────────────────────────────────────

with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Strip JS wrapper to load JSON array
start_idx = js_content.find('[')
end_idx = js_content.rfind(']') + 1

if start_idx == -1 or end_idx == 0:
    print("Could not find JSON array in JS file.")
    exit(1)

json_str = js_content[start_idx:end_idx]
data = json.loads(json_str)
print(f"\nLoaded {len(data)} students from JS database.")

# ── 3. Update records ────────────────────────────────────────────────────────

updated_count = 0
not_found_in_pdf = []
admin_skipped = 0

for student in data:
    enroll = student.get("enrollment")
    dept = student.get("dept", "SY4")

    if enroll in pdf_records:
        t4_mark = pdf_records[enroll]

        # Store individual T4 mark
        student["python24"] = t4_mark

        # Add T4 mark to cumulative Python2 column
        existing_python2 = student.get("python2", 0.0) or 0.0
        student["python2"] = round(float(existing_python2) + t4_mark, 1)

        # Recalculate total based on department rules:
        # - SY4: total = dm + coa + toc + python2 + fsd2
        # - SY1, SY2, SY3: total = dm + coa + toc + fcsp + fsd2
        dm   = float(student.get("dm",   0.0) or 0.0)
        coa  = float(student.get("coa",  0.0) or 0.0)
        toc  = float(student.get("toc",  0.0) or 0.0)
        fsd2 = float(student.get("fsd2", 0.0) or 0.0)

        if dept == "SY4":
            python2 = float(student.get("python2", 0.0) or 0.0)
            total = dm + coa + toc + python2 + fsd2
        else:
            fcsp = float(student.get("fcsp", 0.0) or 0.0)
            total = dm + coa + toc + fcsp + fsd2

        student["total"] = round(total, 1)
        updated_count += 1
    else:
        # For students not found in PDF, still recalculate total for consistency
        dm   = float(student.get("dm",   0.0) or 0.0)
        coa  = float(student.get("coa",  0.0) or 0.0)
        toc  = float(student.get("toc",  0.0) or 0.0)
        fsd2 = float(student.get("fsd2", 0.0) or 0.0)

        if dept == "SY4":
            python2 = float(student.get("python2", 0.0) or 0.0)
            total = dm + coa + toc + python2 + fsd2
        else:
            fcsp = float(student.get("fcsp", 0.0) or 0.0)
            total = dm + coa + toc + fcsp + fsd2

        student["total"] = round(total, 1)
        not_found_in_pdf.append(student)

print(f"\nUpdated {updated_count} students with Python-2 T4 marks.")
print(f"{len(not_found_in_pdf)} students from JS were not found in PDF.")

# Print summary of not-found students by department
depts_not_found = {}
for student in not_found_in_pdf:
    d = student.get("dept", "unknown")
    depts_not_found[d] = depts_not_found.get(d, 0) + 1

if depts_not_found:
    print("\nStudents NOT found in PDF by department:")
    for d, count in depts_not_found.items():
        print(f"  - {d}: {count}")

# Verify some key students
print("\n-- Verification Samples --")
daksh = None
for s in data:
    if s.get('enrollment') == '24002171410007' or ('DAKSH' in s.get('name','').upper() and 'BHAVSAR' in s.get('name','').upper()):
        daksh = s
        break
if daksh:
    print(f"  BHAVSAR DAKSH: python24={daksh.get('python24')}, python2={daksh.get('python2')}, total={daksh.get('total')}")

# Check a few SY4 students
sy4_samples = [s for s in data if s.get('dept') == 'SY4' and s.get('python24')][:5]
for s in sy4_samples:
    print(f"  {s['name'][:35]:35s} | enroll={s['enrollment']} | python24={s.get('python24')} | python2={s.get('python2')} | total={s.get('total')}")

# ── 4. Save the JS file ──────────────────────────────────────────────────────

# Create backup first
import shutil
backup_path = JS_PATH + '.python24bak'
shutil.copy2(JS_PATH, backup_path)
print(f"\nBackup created: {os.path.basename(backup_path)}")

new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_js_content)

print("Successfully wrote Python-2 T4 marks to JS file.")
print(f"\nTotal students with python24 field: {sum(1 for s in data if s.get('python24') is not None)}")
