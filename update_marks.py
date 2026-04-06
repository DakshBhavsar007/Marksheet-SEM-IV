import PyPDF2
import re
import json

def extract_marks(pdf_path):
    marks = {}
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split('\n'):
                    line = line.strip()
                    match = re.search(r'(\d{14})', line)
                    if match:
                        enroll = match.group(1)
                        tokens = line.split()
                        if not tokens:
                            continue
                        mark_str = tokens[-1]
                        if mark_str.upper() in ['AB', 'ABS', 'X']:
                            mark_val = 0.0
                        else:
                            try:
                                mark_val = float(mark_str)
                            except ValueError:
                                float_match = re.search(r'(\d+\.?\d*)', mark_str)
                                if float_match:
                                    mark_val = float(float_match.group(1))
                                else:
                                    continue
                        marks[enroll] = mark_val
        print(f"Extracted {len(marks)} records from {pdf_path}")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return marks

coa_pdf = "Compile_Marksheet_SEM_IV_CE_IT_2026_T1_COA.pdf"
toc_pdf = "Compile_Marksheet_SEM_IV_CE_IT_2026_T1_TOC.pdf"
js_path = "new_datamarksheet.js"

coa_marks = extract_marks(coa_pdf)
toc_marks = extract_marks(toc_pdf)

try:
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    
    start_idx = js_content.find('[')
    end_idx = js_content.rfind(']') + 1
    
    if start_idx == -1 or end_idx == 0:
        print("Could not find JSON array in JS file.")
        exit(1)
        
    json_str = js_content[start_idx:end_idx]
    data = json.loads(json_str)
    
    updated_coa = 0
    updated_toc = 0
    for student in data:
        enroll = student.get("enrollment")
        if enroll in coa_marks:
            student["coa"] = coa_marks[enroll]
            updated_coa += 1
        if enroll in toc_marks:
            student["toc"] = toc_marks[enroll]
            updated_toc += 1
        
        dm = float(student.get("dm", 0))
        coa = float(student.get("coa", 0))
        toc = float(student.get("toc", 0))
        fsd2 = float(student.get("fsd2", student.get("fsd-ii", 0)))
        python2 = float(student.get("python2", 0))
        
        student["total"] = dm + coa + toc + fsd2 + python2

    print(f"Updated COA marks for {updated_coa} students.")
    print(f"Updated TOC marks for {updated_toc} students.")

    new_json_str = json.dumps(data, indent=2)
    new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]
    
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(new_js_content)
    print("Successfully updated new_datamarksheet.js")

except Exception as e:
    print(f"An error occurred: {e}")
