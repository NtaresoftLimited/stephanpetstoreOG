import PyPDF2
import sys

pdf_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Grooming PriceList.pdf"

try:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(text)
except Exception as e:
    print(f"Error reading PDF with PyPDF2: {e}")
    # Fallback or check if file exists
    import os
    if os.path.exists(pdf_path):
        print("File exists but could not be read.")
    else:
        print("File not found.")
