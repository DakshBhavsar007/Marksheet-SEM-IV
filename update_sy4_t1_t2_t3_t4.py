import pdfplumber
import re
import json

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compiled_Marksheet_T1+T2+T3+T4.pdf'
JS_PATH  = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\new_datamarksheet.js'

def parse_mark(val):
    val = val.strip()
    if val.upper() in ('AB', 'ABS', 'UFM', '', '-', 'PENDING', 'FEES PENDING', 'DETAIN'):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

pdf_records = {}

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line = line.strip()
            m = re.search(r'\b(\d{14})\b', line)
            if not m:
                continue
            enrollment = m.group(1)
            
            idx = line.find(enrollment)
            after_enroll = line[idx + len(enrollment):].strip()
            
            tokens = after_enroll.split()
            
            if "Fees Pending" in after_enroll or "Pending" in after_enroll or "Detain" in after_enroll or len(tokens) < 30:
                pdf_records[enrollment] = {
                    "dm_t1": 0.0, "dm_t2": 0.0, "dm_t3": 0.0, "dm_t4": 0.0, "dm_total": 0.0,
                    "coa_t1": 0.0, "coa_t2": 0.0, "coa_t3": 0.0, "coa_t4": 0.0, "coa_total": 0.0,
                    "toc_t1": 0.0, "toc_t2": 0.0, "toc_t3": 0.0, "toc_t4": 0.0, "toc_total": 0.0,
                    "fcsp_t1": 0.0, "fcsp_t2": 0.0, "fcsp_t3": 0.0, "fcsp_t4": 0.0, "fcsp_total": 0.0,
                    "fsd_t1": 0.0, "fsd_t2": 0.0, "fsd_t3": 0.0, "fsd_t4": 0.0, "fsd_total": 0.0,
                }
            else:
                mark_tokens = tokens[-30:]
                pdf_records[enrollment] = {
                    "dm_t1": parse_mark(mark_tokens[0]),
                    "dm_t2": parse_mark(mark_tokens[1]),
                    "dm_t3": parse_mark(mark_tokens[2]),
                    "dm_t4": parse_mark(mark_tokens[3]),
                    "dm_total": parse_mark(mark_tokens[5]),
                    
                    "coa_t1": parse_mark(mark_tokens[6]),
                    "coa_t2": parse_mark(mark_tokens[7]),
                    "coa_t3": parse_mark(mark_tokens[8]),
                    "coa_t4": parse_mark(mark_tokens[9]),
                    "coa_total": parse_mark(mark_tokens[11]),
                    
                    "toc_t1": parse_mark(mark_tokens[12]),
                    "toc_t2": parse_mark(mark_tokens[13]),
                    "toc_t3": parse_mark(mark_tokens[14]),
                    "toc_t4": parse_mark(mark_tokens[15]),
                    "toc_total": parse_mark(mark_tokens[17]),
                    
                    "fcsp_t1": parse_mark(mark_tokens[18]),
                    "fcsp_t2": parse_mark(mark_tokens[19]),
                    "fcsp_t3": parse_mark(mark_tokens[20]),
                    "fcsp_t4": parse_mark(mark_tokens[21]),
                    "fcsp_total": parse_mark(mark_tokens[23]),
                    
                    "fsd_t1": parse_mark(mark_tokens[24]),
                    "fsd_t2": parse_mark(mark_tokens[25]),
                    "fsd_t3": parse_mark(mark_tokens[26]),
                    "fsd_t4": parse_mark(mark_tokens[27]),
                    "fsd_total": parse_mark(mark_tokens[29]),
                }

print(f"Parsed {len(pdf_records)} records from PDF.")

with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

start_idx = js_content.find('[')
end_idx = js_content.rfind(']') + 1
json_str = js_content[start_idx:end_idx]
data = json.loads(json_str)

updated_count = 0
for student in data:
    if student.get("dept") != "SY4":
        continue
    
    enroll = student.get("enrollment")
    if enroll in pdf_records:
        pdf_m = pdf_records[enroll]
        
        student["dm"] = pdf_m["dm_total"]
        student["dm2"] = pdf_m["dm_t2"]
        student["dm3"] = pdf_m["dm_t3"]
        student["dm4"] = pdf_m["dm_t4"]
        
        student["coa"] = pdf_m["coa_total"]
        student["coa2"] = pdf_m["coa_t2"]
        student["coa3"] = pdf_m["coa_t3"]
        student["coa4"] = pdf_m["coa_t4"]
        
        student["toc"] = pdf_m["toc_total"]
        student["toc2"] = pdf_m["toc_t2"]
        student["toc3"] = pdf_m["toc_t3"]
        student["toc4"] = pdf_m["toc_t4"]
        
        student["python2"] = pdf_m["fcsp_total"]
        student["python22"] = pdf_m["fcsp_t2"]
        student["python23"] = pdf_m["fcsp_t3"]
        student["python24"] = pdf_m["fcsp_t4"]
        student["fcsp"] = pdf_m["fcsp_t1"]
        
        student["fsd2"] = pdf_m["fsd_total"]
        student["fsd22"] = pdf_m["fsd_t2"]
        student["fsd23"] = pdf_m["fsd_t3"]
        student["fsd24"] = pdf_m["fsd_t4"]
        
        total = round(student["dm"] + student["coa"] + student["toc"] + student["python2"] + student["fsd2"], 1)
        student["total"] = total
        
        updated_count += 1

new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]

with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(new_js_content)

print(f"Successfully updated {updated_count} SY4 records in {JS_PATH}.")
