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

with open(JS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

json_str = content.strip()
if json_str.startswith('const data ='):
    json_str = json_str[len('const data ='):].strip()
if json_str.endswith(';'):
    json_str = json_str[:-1].strip()

data = json.loads(json_str)

subject_discrepancies = []

for student in data:
    enroll = student.get("enrollment")
    if student.get("dept") != "SY4":
        continue
    if enroll not in pdf_records:
        continue
        
    pdf_m = pdf_records[enroll]
    js_m = {
        "dm": student.get("dm", 0.0),
        "dm2": student.get("dm2", 0.0),
        "coa": student.get("coa", 0.0),
        "coa2": student.get("coa2", 0.0),
        "toc": student.get("toc", 0.0),
        "toc2": student.get("toc2", 0.0),
        "python2": student.get("python2", 0.0),
        "python22": student.get("python22", 0.0),
        "fsd2": student.get("fsd2", 0.0),
        "fsd22": student.get("fsd22", 0.0),
        "fcsp": student.get("fcsp", 0.0),
    }
    
    diffs = {}
    if abs(js_m["dm"] - pdf_m["dm_total"]) > 0.01:
        diffs["dm"] = (js_m["dm"], pdf_m["dm_total"])
    if abs(js_m["dm2"] - pdf_m["dm_t2"]) > 0.01:
        diffs["dm2"] = (js_m["dm2"], pdf_m["dm_t2"])
        
    if abs(js_m["coa"] - pdf_m["coa_total"]) > 0.01:
        diffs["coa"] = (js_m["coa"], pdf_m["coa_total"])
    if abs(js_m["coa2"] - pdf_m["coa_t2"]) > 0.01:
        diffs["coa2"] = (js_m["coa2"], pdf_m["coa_t2"])
        
    if abs(js_m["toc"] - pdf_m["toc_total"]) > 0.01:
        diffs["toc"] = (js_m["toc"], pdf_m["toc_total"])
    if abs(js_m["toc2"] - pdf_m["toc_t2"]) > 0.01:
        diffs["toc2"] = (js_m["toc2"], pdf_m["toc_t2"])
        
    if abs(js_m["python2"] - pdf_m["fcsp_total"]) > 0.01:
        diffs["python2"] = (js_m["python2"], pdf_m["fcsp_total"])
    if abs(js_m["python22"] - pdf_m["fcsp_t2"]) > 0.01:
        diffs["python22"] = (js_m["python22"], pdf_m["fcsp_t2"])
    if abs(js_m["fcsp"] - pdf_m["fcsp_t1"]) > 0.01:
        diffs["fcsp"] = (js_m["fcsp"], pdf_m["fcsp_t1"])
        
    if abs(js_m["fsd2"] - pdf_m["fsd_total"]) > 0.01:
        diffs["fsd2"] = (js_m["fsd2"], pdf_m["fsd_total"])
    if abs(js_m["fsd22"] - pdf_m["fsd_t2"]) > 0.01:
        diffs["fsd22"] = (js_m["fsd22"], pdf_m["fsd_t2"])
        
    if diffs:
        subject_discrepancies.append((student.get("name"), enroll, diffs))

print(f"Found {len(subject_discrepancies)} students with real subject mark discrepancies:")
for name, enroll, diffs in subject_discrepancies:
    print(f"- {name} ({enroll}): {diffs}")
