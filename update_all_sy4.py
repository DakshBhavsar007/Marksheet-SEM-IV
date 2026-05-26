import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compiled_Marksheet_Sem 4_T1+T2.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

def parse_mark(val):
    val = val.strip()
    if val in ('AB', 'UFM', '', '-', 'Fees Pending', 'Pending'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

# 1. Parse all pages of the PDF
pdf_records = {}

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            # Match 14 digit enrollment
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue
            enrollment = m.group(1)
            
            idx = line.find(enrollment)
            after_enroll = line[idx + len(enrollment):].strip()
            
            if "Fees Pending" in after_enroll or "Pending" in after_enroll:
                pdf_records[enrollment] = {
                    "is_pending": True,
                    "dm_t1": 0.0, "dm_t2": 0.0, "dm_total": 0.0,
                    "coa_t1": 0.0, "coa_t2": 0.0, "coa_total": 0.0,
                    "toc_t1": 0.0, "toc_t2": 0.0, "toc_total": 0.0,
                    "fcsp_t1": 0.0, "fcsp_t2": 0.0, "fcsp_total": 0.0,
                    "fsd_t1": 0.0, "fsd_t2": 0.0, "fsd_total": 0.0,
                }
                continue
                
            tokens = after_enroll.split()
            if len(tokens) < 15:
                print(f"Warning: Student {enrollment} has less than 15 mark tokens.")
                continue
                
            mark_tokens = tokens[-15:]
            
            dm_t1 = parse_mark(mark_tokens[0])
            dm_t2 = parse_mark(mark_tokens[1])
            dm_total = parse_mark(mark_tokens[2])
            
            coa_t1 = parse_mark(mark_tokens[3])
            coa_t2 = parse_mark(mark_tokens[4])
            coa_total = parse_mark(mark_tokens[5])
            
            toc_t1 = parse_mark(mark_tokens[6])
            toc_t2 = parse_mark(mark_tokens[7])
            toc_total = parse_mark(mark_tokens[8])
            
            fcsp_t1 = parse_mark(mark_tokens[9])
            fcsp_t2 = parse_mark(mark_tokens[10])
            fcsp_total = parse_mark(mark_tokens[11])
            
            fsd_t1 = parse_mark(mark_tokens[12])
            fsd_t2 = parse_mark(mark_tokens[13])
            fsd_total = parse_mark(mark_tokens[14])
            
            pdf_records[enrollment] = {
                "is_pending": False,
                "dm_t1": dm_t1, "dm_t2": dm_t2, "dm_total": dm_total,
                "coa_t1": coa_t1, "coa_t2": coa_t2, "coa_total": coa_total,
                "toc_t1": toc_t1, "toc_t2": toc_t2, "toc_total": toc_total,
                "fcsp_t1": fcsp_t1, "fcsp_t2": fcsp_t2, "fcsp_total": fcsp_total,
                "fsd_t1": fsd_t1, "fsd_t2": fsd_t2, "fsd_total": fsd_total,
            }

print(f"Parsed {len(pdf_records)} records from PDF.")

# 2. Load JS file
with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

# 3. Update records
updated_count = 0
not_found_count = 0
subject_updated_count = 0

for student in data:
    if student.get("dept") != "SY4":
        continue
        
    enroll = student.get("enrollment")
    if enroll in pdf_records:
        pdf_m = pdf_records[enroll]
        
        # Check if subject marks have actually changed
        has_changes = (
            student.get("dm") != pdf_m["dm_total"] or
            student.get("dm2") != pdf_m["dm_t2"] or
            student.get("coa") != pdf_m["coa_total"] or
            student.get("coa2") != pdf_m["coa_t2"] or
            student.get("toc") != pdf_m["toc_total"] or
            student.get("toc2") != pdf_m["toc_t2"] or
            student.get("python2") != pdf_m["fcsp_total"] or
            student.get("python22") != pdf_m["fcsp_t2"] or
            student.get("fcsp") != pdf_m["fcsp_t1"] or
            student.get("fsd2") != pdf_m["fsd_total"] or
            student.get("fsd22") != pdf_m["fsd_t2"]
        )
        
        if has_changes:
            subject_updated_count += 1
            
        # Perform update
        student["dm"] = pdf_m["dm_total"]
        student["dm2"] = pdf_m["dm_t2"]
        student["coa"] = pdf_m["coa_total"]
        student["coa2"] = pdf_m["coa_t2"]
        student["toc"] = pdf_m["toc_total"]
        student["toc2"] = pdf_m["toc_t2"]
        student["python2"] = pdf_m["fcsp_total"]
        student["python22"] = pdf_m["fcsp_t2"]
        student["fcsp"] = pdf_m["fcsp_t1"]
        student["fsd2"] = pdf_m["fsd_total"]
        student["fsd22"] = pdf_m["fsd_t2"]
        
        # Recalculate total accurately
        total = round(student["dm"] + student["coa"] + student["toc"] + student["python2"] + student["fsd2"], 1)
        student["total"] = total
        
        updated_count += 1
    else:
        # For those not in PDF, just recalculate their total to ensure accuracy
        total = round(
            float(student.get("dm", 0.0)) +
            float(student.get("coa", 0.0)) +
            float(student.get("toc", 0.0)) +
            float(student.get("python2", 0.0)) +
            float(student.get("fsd2", 0.0)),
            1
        )
        student["total"] = total
        not_found_count += 1

# 4. Write back to new_datamarksheet.js
new_content = 'const data = ' + json.dumps(data, indent=2, ensure_ascii=False) + ';\n'

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Update Summary:")
print(f"- Total SY4 records updated matching PDF: {updated_count}")
print(f"  - SY4 records with actual subject mark changes: {subject_updated_count}")
print(f"- SY4 records not in PDF (only recalculated total): {not_found_count}")
print(f"Successfully wrote updates back to {JS_PATH}.")
