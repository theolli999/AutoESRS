import os
import json
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load API keys and configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")  # Name of your existing Pinecone index


# Initialize APIs
pinecone = Pinecone(api_key=PINECONE_API_KEY)

def ask_question(user_input):
    # Generate embedding for the user input
    embedding_response = openai.embeddings.create(
        input=user_input,
        model="text-embedding-ada-002"
    )
    # Use attribute access instead of subscription
    vector = embedding_response.data[0].embedding

    # Perform similarity search in the provided Pinecone index
    index = pinecone.Index(INDEX_NAME)
    query_response = index.query(vector=vector, top_k=5, include_metadata=True)
    return query_response

def checkRelevance(chunk, user_input):
    # Check if the chunk is relevant
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"This is a chunk extracted from a document: {chunk['metadata']['text']}. Is this chunk provide information relevant to the question: {user_input}? Only answer with a binary score of '1' or '0', remember to only answer with these values."}
        ],
        max_tokens=50
    )
    print(response.choices[0].message.content)
    if(response.choices[0].message.content == "1"):
        print(chunk['metadata']['text'])
    return response.choices[0].message.content == "1"

def genereate_response(chunks, user_input):
    chunk_snippet = ""
    for chunk in chunks:
        chunk_snippet += chunk['metadata']['text'] + "\n\n"

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you do not know the answer, say that you don't have information on that topic."},
            {"role": "user", "content": f"Here are the chunks extracted from the document that are relevant to the question: {user_input}. Please provide a an of the relevant information. Only answer the question based on this information: {chunk_snippet}"}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content

def filter_chunks(chunks, user_input):
    relevant_chunks = []
    for chunk in chunks:
        if(checkRelevance(chunk, user_input)):
            relevant_chunks.append(chunk)

    return relevant_chunks


def main():
    print("Type your question (or 'exit' to quit):")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "exit":
            break
        if not user_input:
            print("Please enter a valid question.")
            continue

        try:
            result = ask_question(user_input)
            # Convert result to dict if it has a to_dict() method, otherwise use __dict__
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            else:
                result = result.__dict__
            result = filter_chunks(result['matches'], user_input)
            answer = genereate_response(result, user_input)
            print(answer)
            #checkIfFactual(answer, result)
            print("Found in these documents:")
            for chunk in result:
                print(chunk['metadata']['source'])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()