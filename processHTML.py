import pineconeUtils
from bs4 import BeautifulSoup
import html5lib
import os

def extract_paragraphs_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html5lib')
    paragraphs = soup.find_all('p')
    sections = [p.get_text(strip=True) for p in paragraphs]
    line_numbers = list(range(1, len(sections) + 1))
    
    return sections, line_numbers


if __name__ == "__main__":
    directory = './background'
    id = 0
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            filepath = os.path.join(directory, filename)
            sections, line_numbers = extract_paragraphs_from_html(filepath)
            embeddings = pineconeUtils.embed_sentences(sections)
            index = 'esrs'
            id = int(pineconeUtils.send_to_pinecone(index, embeddings, sections, filename, id))
            for i in range(len(sections)):
                print(f"File: {filename}")
                print(f"Section: {sections[i]}")
                print(f"Line number: {line_numbers[i]}")
                print("\n")