import os
import json
import traceback
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
load_dotenv()
import traceback
from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import db

# Load API keys and configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")  # Name of your existing Pinecone index
 
# Initialize APIs
pinecone = Pinecone(api_key=PINECONE_API_KEY)

def rewriteQuestion(user_input):

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"Rewrite the question: {user_input}"}
        ],
        max_tokens=50
    )
    print("Rewritten question: ", response.choices[0].message.content)

def ask_question(user_input):
    # Generate embedding for the user input
    embedding_response = openai.embeddings.create(
        input=user_input,
        model="text-embedding-ada-002"
    )
    vector = embedding_response.data[0].embedding

    # Perform similarity search in the provided Pinecone index
    index = pinecone.Index(INDEX_NAME)
    query_response = index.query(vector=vector, top_k=5, include_metadata=True)
    return query_response

def fetch_chunk_from_pinecone(chunk_id):
    index = pinecone.Index(INDEX_NAME)
    query_response = index.fetch(ids=[chunk_id])
    chunk = index.query(vector=query_response.vectors[str(chunk_id)].values, top_k=1, include_metadata=True)
    return chunk.matches[0]


def checkChunk(chunk, user_input, direction, chunk_snippet, visited_chunks):
    chunk_id = int(chunk['id'])
    if chunk_id in visited_chunks:
        return chunk_snippet
    else:
        visited_chunks.add(chunk_id)


    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"This is a chunk extracted from a document: {chunk['metadata']['text']}. Does this chunk provide information relevant to understand the context better of the question: {user_input}? Only answer with a binary score of '1' or '0', remember to only answer with these values."}
        ],
        max_tokens=50
    )
    if response.choices[0].message.content == "1":
        print("Found surrounding chunk:", chunk_id)
        if direction == "upper":
            next_chunk = fetch_chunk_from_pinecone(str(chunk_id - 1))
            updated_snippet = next_chunk['metadata']['text'] + "\n\n" + chunk_snippet
            chunk_snippet = updated_snippet
            chunk_snippet = checkChunk(next_chunk, user_input, "upper", chunk_snippet, visited_chunks)
        elif direction == "lower":
            prev_chunk = fetch_chunk_from_pinecone(str(chunk_id + 1))
            updated_snippet = chunk_snippet + "\n\n" + prev_chunk['metadata']['text']
            chunk_snippet = updated_snippet
            chunk_snippet = checkChunk(prev_chunk, user_input, "lower", chunk_snippet, visited_chunks)
    else:
        return chunk_snippet

    return chunk_snippet

def lookAroundChunk(chunk, user_input, visited_chunks):
    chunk_id = int(chunk['id'])
    chunk_snippet = chunk['metadata']['text']
    chunk_snippet = checkChunk(fetch_chunk_from_pinecone(chunk_id + 1), user_input, "upper", chunk_snippet, visited_chunks)
    chunk_snippet = checkChunk(fetch_chunk_from_pinecone(chunk_id - 1), user_input, "lower", chunk_snippet, visited_chunks)
    return chunk_snippet


def rewriteChunk(chunk, user_input):
    description = db.getDescription('data.db', chunk['metadata']['source'])
    newChunk = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"This is a chunk extracted from a document: {chunk['metadata']['text']}. This is the description of the source: {description}. Rewrite the chunk to provide information relevant to the question: {user_input}"}
        ],
        max_tokens=200
    )
    return newChunk.choices[0].message.content

def checkRelevance(chunk, chunks, user_input, visited_chunks, sources):
    # Check if the chunk is relevant
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a text analyzer."},
            {"role": "user", "content": f"This is a chunk extracted from a document: {chunk['metadata']['text']}. Is this chunk provide information relevant to the question: {user_input}? Only answer with a binary score of '1' or '0', remember to only answer with these values."}
        ],
        max_tokens=50
    )
    if(response.choices[0].message.content == "0"):
        print("Chunk is not relevant")
    else:
        print("Chunk is relevant: " + chunk['metadata']['source'])
        newChunk = rewriteChunk(chunk, user_input)
        #print(chunk['metadata']['text'] + "\n\n")
        sources.append(chunk['metadata']['source']) 
        print("Found this information: ", chunk['metadata']['text'], "\n\n")
        #return lookAroundChunk(chunk, user_input, visited_chunks)
        return newChunk, chunk['metadata']['source']
    return "", None

def generate_response(context, user_input):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you do not know the answer, say that you don't have information on that topic."},
            {"role": "user", "content": f"Here are the chunks extracted from the document that are relevant to the question: {user_input}. Please provide a an of the relevant information. Only answer the question based on this information: {context}"}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content

def filter_chunks(chunks, user_input):
    visited_chunks = set()
    context = ""
    sources = []
    for chunk in chunks:
        text, source = checkRelevance(chunk, chunks, user_input, visited_chunks, sources)
        context += text
        if source:
            sources.append(source)
    
    return context, list(set(sources))


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
            result, sources = filter_chunks(result['matches'], user_input)
            answer = generate_response(result, user_input)
            output = {"Question": user_input, "Answer": answer, "Source(s)": sources}
            print(json.dumps(output, indent=4))

            #print("\n\n Answer: ")
            #print(answer)
            #checkIfFactual(answer, result)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    main()