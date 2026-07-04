import re
import json

PDF_DUMP_PATH = 'pdf_text_dump.txt'
JS_PATH = 'new_datamarksheet.js'

# 1. Parse PDF dump
pdf_enrollments = set()
with open(PDF_DUMP_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        m = re.search(r'\b(\d{14})\b', line)
        if m:
            pdf_enrollments.add(m.group(1))

print(f"Total enrollments in PDF dump: {len(pdf_enrollments)}")

# 2. Load JS file
with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Strip JS wrapper
start_idx = js_content.find('[')
end_idx = js_content.rfind(']') + 1
json_str = js_content[start_idx:end_idx]
data = json.loads(json_str)

js_sy4_enrollments = {s.get('enrollment'): s.get('name') for s in data if s.get('dept') == 'SY4'}
print(f"Total SY4 enrollments in JS: {len(js_sy4_enrollments)}")

# 3. Compare
not_in_pdf = {enroll: name for enroll, name in js_sy4_enrollments.items() if enroll not in pdf_enrollments}
not_in_js = {enroll for enroll in pdf_enrollments if enroll not in js_sy4_enrollments}

print(f"JS SY4 students NOT in PDF: {len(not_in_pdf)}")
for enroll, name in not_in_pdf.items():
    print(f"  - {enroll}: {name}")

print(f"PDF students NOT in JS SY4: {len(not_in_js)}")
for enroll in not_in_js:
    print(f"  - {enroll}")
