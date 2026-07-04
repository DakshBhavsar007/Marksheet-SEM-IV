import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compiled Marksheet_T1+T2+T3.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

def parse_mark(val):
    val = val.strip()
    if val.upper() in ('AB', 'ABS', 'UFM', '', '-', 'PENDING', 'FEES PENDING'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

# 1. Parse the PDF and extract student marks
pdf_records = {}

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            # Match 14-digit enrollment
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue
            enrollment = m.group(1)
            
            idx = line.find(enrollment)
            after_enroll = line[idx + len(enrollment):].strip()
            
            tokens = after_enroll.split()
            
            if "Fees Pending" in after_enroll or "Pending" in after_enroll or len(tokens) < 20:
                pdf_records[enrollment] = {
                    "dm_t1": 0.0, "dm_t2": 0.0, "dm_t3": 0.0, "dm_total": 0.0,
                    "coa_t1": 0.0, "coa_t2": 0.0, "coa_t3": 0.0, "coa_total": 0.0,
                    "toc_t1": 0.0, "toc_t2": 0.0, "toc_t3": 0.0, "toc_total": 0.0,
                    "fcsp_t1": 0.0, "fcsp_t2": 0.0, "fcsp_t3": 0.0, "fcsp_total": 0.0,
                    "fsd_t1": 0.0, "fsd_t2": 0.0, "fsd_t3": 0.0, "fsd_total": 0.0,
                }
            else:
                mark_tokens = tokens[-20:]
                pdf_records[enrollment] = {
                    "dm_t1": parse_mark(mark_tokens[0]),
                    "dm_t2": parse_mark(mark_tokens[1]),
                    "dm_t3": parse_mark(mark_tokens[2]),
                    "dm_total": parse_mark(mark_tokens[3]),
                    
                    "coa_t1": parse_mark(mark_tokens[4]),
                    "coa_t2": parse_mark(mark_tokens[5]),
                    "coa_t3": parse_mark(mark_tokens[6]),
                    "coa_total": parse_mark(mark_tokens[7]),
                    
                    "toc_t1": parse_mark(mark_tokens[8]),
                    "toc_t2": parse_mark(mark_tokens[9]),
                    "toc_t3": parse_mark(mark_tokens[10]),
                    "toc_total": parse_mark(mark_tokens[11]),
                    
                    "fcsp_t1": parse_mark(mark_tokens[12]),
                    "fcsp_t2": parse_mark(mark_tokens[13]),
                    "fcsp_t3": parse_mark(mark_tokens[14]),
                    "fcsp_total": parse_mark(mark_tokens[15]),
                    
                    "fsd_t1": parse_mark(mark_tokens[16]),
                    "fsd_t2": parse_mark(mark_tokens[17]),
                    "fsd_t3": parse_mark(mark_tokens[18]),
                    "fsd_total": parse_mark(mark_tokens[19]),
                }

print(f"Successfully parsed {len(pdf_records)} student records from PDF.")

# 2. Load JS file
with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Extract the JSON array from const data = [...];
start_idx = js_content.find('[')
end_idx = js_content.rfind(']') + 1
json_str = js_content[start_idx:end_idx]
data = json.loads(json_str)

# 3. Update SY4 students
updated_count = 0
not_found_count = 0
changed_marks_count = 0

for student in data:
    if student.get("dept") != "SY4":
        continue
    
    enroll = student.get("enrollment")
    
    if enroll in pdf_records:
        pdf_m = pdf_records[enroll]
        
        # Check if subject marks actually changed
        has_changes = (
            student.get("dm") != pdf_m["dm_total"] or
            student.get("dm2") != pdf_m["dm_t2"] or
            student.get("dm3") != pdf_m["dm_t3"] or
            
            student.get("coa") != pdf_m["coa_total"] or
            student.get("coa2") != pdf_m["coa_t2"] or
            student.get("coa3") != pdf_m["coa_t3"] or
            
            student.get("toc") != pdf_m["toc_total"] or
            student.get("toc2") != pdf_m["toc_t2"] or
            student.get("toc3") != pdf_m["toc_t3"] or
            
            student.get("python2") != pdf_m["fcsp_total"] or
            student.get("python22") != pdf_m["fcsp_t2"] or
            student.get("python23") != pdf_m["fcsp_t3"] or
            student.get("fcsp") != pdf_m["fcsp_t1"] or
            
            student.get("fsd2") != pdf_m["fsd_total"] or
            student.get("fsd22") != pdf_m["fsd_t2"] or
            student.get("fsd23") != pdf_m["fsd_t3"]
        )
        
        if has_changes:
            changed_marks_count += 1
            
        # Update values
        student["dm"] = pdf_m["dm_total"]
        student["dm2"] = pdf_m["dm_t2"]
        student["dm3"] = pdf_m["dm_t3"]
        
        student["coa"] = pdf_m["coa_total"]
        student["coa2"] = pdf_m["coa_t2"]
        student["coa3"] = pdf_m["coa_t3"]
        
        student["toc"] = pdf_m["toc_total"]
        student["toc2"] = pdf_m["toc_t2"]
        student["toc3"] = pdf_m["toc_t3"]
        
        student["python2"] = pdf_m["fcsp_total"]
        student["python22"] = pdf_m["fcsp_t2"]
        student["python23"] = pdf_m["fcsp_t3"]
        student["fcsp"] = pdf_m["fcsp_t1"]
        
        student["fsd2"] = pdf_m["fsd_total"]
        student["fsd22"] = pdf_m["fsd_t2"]
        student["fsd23"] = pdf_m["fsd_t3"]
        
        # Recalculate total accurately (dm + coa + toc + python2 + fsd2)
        total = round(student["dm"] + student["coa"] + student["toc"] + student["python2"] + student["fsd2"], 1)
        student["total"] = total
        
        updated_count += 1
    else:
        # Recalculate total for students not in PDF to maintain correctness
        total = round(
            float(student.get("dm", 0.0) or 0.0) +
            float(student.get("coa", 0.0) or 0.0) +
            float(student.get("toc", 0.0) or 0.0) +
            float(student.get("python2", 0.0) or 0.0) +
            float(student.get("fsd2", 0.0) or 0.0),
            1
        )
        student["total"] = total
        not_found_count += 1

print("\nUpdate Summary:")
print(f"- Total SY4 records updated matching PDF: {updated_count}")
print(f"  - SY4 records with actual mark changes: {changed_marks_count}")
print(f"- SY4 records not in PDF (only recalculated total): {not_found_count}")

# 4. Write back to JS file
new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_js_content)

print(f"Successfully wrote updates back to {JS_PATH}.")
