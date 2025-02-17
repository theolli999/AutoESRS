import pineconeUtils
from pdfminer.high_level import extract_text
import os
import db
from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def extract_paragraphs_with_pdfminer(pdf_path):
    text = extract_text(pdf_path)
    lines = text.split('\n')
    paragraphs = []
    paragraph = ""
    start_line = 0
    line_numbers = []

    for i, line in enumerate(lines):
        if line.strip() == "":
            if paragraph:
                paragraphs.append(paragraph.strip())
                line_numbers.append(start_line)
                paragraph = ""
        else:
            if not paragraph:
                start_line = i + 1
            paragraph += line + " "

    if paragraph:
        paragraphs.append(paragraph.strip())
        line_numbers.append(start_line)

    return paragraphs, line_numbers




if __name__ == "__main__":
    directory = './documents'
    id = 0
    db.create_database('data.db')
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            sections, line_numbers = extract_paragraphs_with_pdfminer(filepath)
            description = generateDescription(sections, filename)
            db.addData('data.db', filename, description)
            embeddings = pineconeUtils.embed_sentences(sections)
            index = 'test2'
            #id = int(pineconeUtils.send_to_pinecone(index, embeddings, sections, filename, id))
            for i in range(len(sections)):
                print(f"File: {filename}")
                print(f"Section: {sections[i]}")
                print(f"Line number: {line_numbers[i]}")
                print("\n")