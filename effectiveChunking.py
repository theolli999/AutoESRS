import os
import pineconeUtils
import numpy as np
from numpy.linalg import norm
from pdfminer.high_level import extract_text
import nltk
from nltk.tokenize import sent_tokenize
import db
from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def calculate_similarity(vec1, vec2):
    vec1 = np.ravel(vec1)
    vec2 = np.ravel(vec2)
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def generateDescription(sections, filename):
    text = ""
    for section in sections:
        text += section + "\n"
    description = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"This is the document: {filename}. Generate a description of what the document is about {text}"}
        ],
        max_tokens=200
    )
    return description.choices[0].message.content
        

def embed_sentences(filepath):
    text = extract_text(filepath)
    sentences = sent_tokenize(text)
    chunks = []
    chunk = sentences[0]
    lastEmbedding = pineconeUtils.embed_sentences([chunk])

    for sentence in sentences:
        if(sentence == chunk or len(sentence) < 5):
            continue
        embedding = pineconeUtils.embed_sentences([sentence])
        if(calculate_similarity(embedding, lastEmbedding)>0.8 and len(chunk) < 500):
            chunk += " " + sentence
        else:
            chunks.append(chunk)
            chunk = sentence
        lastEmbedding = embedding

    if chunk:
        chunks.append(chunk)    

    return chunks


if __name__ == "__main__":
    directory = './documents'
    id = 0
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            chunks = embed_sentences(filepath)
            description = generateDescription(chunks, filename)
            print("Description: ", description)
            db.addData('data.db', filename, description)
            #embeddings = pineconeUtils.embed_sentences(chunks)         
            #id = int(pineconeUtils.send_to_pinecone("test2", embeddings, chunks, filename, id))
  

    