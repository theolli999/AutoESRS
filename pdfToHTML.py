import os
import io
import glob
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

pdf_dir = './documents'
pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))

print(f"Found {len(pdf_files)} PDF files in {pdf_dir}.")

for pdf_path in pdf_files:
    print(f"Starting conversion for: {pdf_path}")
    output = io.BytesIO()  # Use BytesIO for HTML output
    with open(pdf_path, 'rb') as in_file:
        extract_text_to_fp(in_file, output, laparams=LAParams(), output_type='html')
    html_content = output.getvalue().decode('utf-8')  # Decode bytes to string
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    html_file = os.path.join(pdf_dir, base_name + '.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Converted {pdf_path} to {html_file}")

print("PDF to HTML conversion process completed.")