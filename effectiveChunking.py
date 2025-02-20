import os
import utils
import numpy as np
from numpy.linalg import norm
from pdfminer.high_level import extract_text
import nltk
from nltk.tokenize import sent_tokenize
import db
from openai import OpenAI
import concurrent.futures

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def calculate_similarity(vec1, vec2):
    vec1 = np.ravel(vec1)
    vec2 = np.ravel(vec2)
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def generate_description(sections, filename):
    text = ""
    for section in sections:
        text += section + "\n"

    system_prompt="You are a text analyzer."
    user_prompt=f"This is the document: {filename}. Generate a description of what the document is about {text}"
    return utils.send_gpt4o_prompt(system_prompt, user_prompt, 500)
        
def checkIfSentenceShouldBeRemoved(sentence, chunk):
    if(sentence == chunk or len(sentence) < 5):
        return True
    
    system_prompt="You are a text analyzer."
    user_prompt=f"This is sentence from a text: {sentence}. Determine if the sentence fulfills any of these requirements: 1. The text only contains a time or a date. 2. The text only contains contact information such as email, phone number, name, etc. Only answer with a binary score of '1' or '0', remember to only answer with these values."

    if(utils.send_gpt4o_prompt(system_prompt, user_prompt, 50) == "1"):
        return True
    return False

def embed_sentences(filepath, filename):
    text = extract_text(filepath)
    sentences = sent_tokenize(text)
    chunks = []
    chunk = sentences[0]
    lastEmbedding = utils.embed_sentences([chunk])

    for sentence in sentences:
        if(checkIfSentenceShouldBeRemoved(sentence, chunk)):
            continue

        embedding = utils.embed_sentences([sentence])
        if(calculate_similarity(embedding, lastEmbedding) > 0.8 and len(chunk) < 500):
            chunk += " " + sentence
        else:
            chunks.append(chunk)
            chunk = sentence
        lastEmbedding = embedding

    if chunk:
        chunks.append(chunk)    
    
    description = generate_description(chunks, filename)
    print("Description: ", description)
    # Ensure only one thread writes to the database at a time
    db.addData('descriptions.db', filename, description)
    return chunks

if __name__ == "__main__":
    directory = './documents'
    id = 0
    futures = []
    db.clear_data('descriptions.db')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                futures.append((filename, executor.submit(embed_sentences, filepath, filename)))
    
    for filename, future in futures:
        chunks = future.result()  # Get chunks from the future
        embeddings = utils.embed_sentences(chunks)
        id = int(utils.send_to_pinecone(os.getenv("PINECONE_INDEX_NAME"), embeddings, chunks, filename, id))