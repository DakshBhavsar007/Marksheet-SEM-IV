import PyPDF2
import re
import json
import os

pdf_path = "Compile_Marksheet_SEM_IV_CE_IT_2026_T1_DM.pdf"
js_path = "new_datamarksheet.js"

# 1. Extract marks from PDF
enrollment_marks = {}
try:
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            for line in text.split('\n'):
                line = line.strip()
                match = re.search(r'(\d{14})', line)
                if match:
                    enroll = match.group(1)
                    tokens = line.split()
                    mark_str = tokens[-1]
                    if mark_str.upper() in ['AB', 'ABS']:
                        mark_val = 0.0
                    else:
                        try:
                            # It's possible the mentor name and mark are joined if mentor is missing, but usually tokens are split by space.
                            mark_val = float(mark_str)
                        except ValueError:
                            continue
                    enrollment_marks[enroll] = mark_val
    print(f"Extracted {len(enrollment_marks)} distinct records from PDF.")
except Exception as e:
    print(f"Error reading PDF: {e}")
    exit(1)

# 2. Read JS file
try:
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    
    # Extract JSON part
    start_idx = js_content.find('[')
    end_idx = js_content.rfind(']') + 1
    
    if start_idx == -1 or end_idx == 0:
        print("Could not find JSON array in JS file.")
        exit(1)
        
    json_str = js_content[start_idx:end_idx]
    data = json.loads(json_str)
    
except Exception as e:
    print(f"Error reading/parsing JS: {e}")
    exit(1)

# 3. Update data
updated_count = 0
for student in data:
    enroll = student.get("enrollment")
    if enroll in enrollment_marks:
        student["dm"] = enrollment_marks[enroll]
        # update total
        student["total"] = student.get("dm", 0) + student.get("coa", 0) + student.get("fsd2", student.get("fsd-ii", 0)) + student.get("python2", 0) + student.get("toc", 0)
        updated_count += 1
    else:
        # If not present, maybe leave it as 0 or don't change
        pass

print(f"Updated {updated_count} students in JSON data.")

# 4. Write back JS file
try:
    new_json_str = json.dumps(data, indent=2)
    # The original file starts with 'const data = ' and we just append the JSON array
    new_js_content = js_content[:start_idx] + new_json_str + js_content[end_idx:]
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(new_js_content)
    print("Successfully updated the JavaScript file.")
except Exception as e:
    print(f"Error writing JS file: {e}")
    exit(1)
