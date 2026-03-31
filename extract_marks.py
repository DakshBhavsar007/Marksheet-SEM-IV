import PyPDF2
import sys

try:
    with open("Compile_Marksheet_SEM_IV_CE_IT_2026_T1_DM.pdf", "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for i in range(min(5, len(reader.pages))):
            text += reader.pages[i].extract_text()
        print("Successfully extracted text:")
        print(text[:2000])
except Exception as e:
    print("Error:", e)
