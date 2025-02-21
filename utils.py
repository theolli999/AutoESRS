from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
)


def send_gpt4o_prompt(system_prompt, user_prompt, max_tokens):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens
        )
    return response.choices[0].message.content

def send_o3_prompt(system_prompt, user_prompt):
    response = openai.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response

def embed_sentences(sentences):
    embeddings = []
    for sentence in sentences:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=sentence
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def send_to_pinecone(index_str, embeddings, sentences, source, id):
    index = pc.Index(index_str)
    vectors = [{"id": str(id + i), "values": embedding, "metadata": {"text": sentence, "source": source}} for i, (embedding, sentence) in enumerate(zip(embeddings, sentences))]
    batch_size = 200 

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(batch)
    
    #index.upsert(vectors) 
    return vectors[-1]["id"]