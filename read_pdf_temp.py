import pdfplumber

PDF_PATH = r'c:\Users\parul\Desktop\marksheet\marksheet_SEM-IV\Compile _Marksheet_COA_SEM_IV_CE_IT_2026_T2.pdf'

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages[:3]:
        text = page.extract_text()
        if text:
            print(f"--- PAGE ---")
            for line in text.splitlines()[:20]:
                print(line)
