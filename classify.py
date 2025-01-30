import os
from PyPDF2 import PdfReader
import fitz
from openai import OpenAI
from pdfminer.high_level import extract_text
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
)

def analyze_sentences(sentences, maxSentences = 30):
    analyzed_sentences = []
    i = 0
    for sentence in sentences:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du är en textanalysator."},
                {"role": "user", "content": f"Kategorisera om denna mening utifrån om frågan berör någon av följande områden: Enviroment, Social, Neither: {sentence}"}
            ],
            max_tokens=50
        )
        analyzed_sentences.append(response.choices[0].message['content'])
        i += 1
        if(i >= maxSentences):
            break
    return analyzed_sentences


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

def embed_sentences(sentences):
    embeddings = []
    for sentence in sentences:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=sentence
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def send_to_pinecone(embeddings, sentences, source, id):
    index = pc.Index("test")  # Replace "your-index-name" with your actual index name
    vectors = [{"id": str(id + i), "values": embedding, "metadata": {"text": sentence, "source": source}} for i, (embedding, sentence) in enumerate(zip(embeddings, sentences))]
    index.upsert(vectors) 
    return vectors[-1]["id"]

if __name__ == "__main__":
    directory = './documents'
    id = 0
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            sections, line_numbers = extract_paragraphs_with_pdfminer(filepath)
            embeddings = embed_sentences(sections)
            id = int(send_to_pinecone(embeddings, sections, filename, id))
            for i in range(len(sections)):
                print(f"File: {filename}")
                print(f"Section: {sections[i]}")
                print(f"Line number: {line_numbers[i]}")
                print("\n")

    #extracted_texts = extract_text_from_pdfs(directory)
    #extracted_texts = extract_paragraphs_from_pdfs(directory)
    #print(extracted_texts)
    #for filename, sentences in extracted_texts.items():
    #    print(f"Text from {filename}:")
        #for sentence in sentences:
            #print(sentence)
        #print("\n")