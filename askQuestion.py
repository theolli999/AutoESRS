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
import concurrent.futures
import utils

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
    vector = embedding_response.data[0].embedding

    # Perform similarity search in the provided Pinecone index
    index = pinecone.Index(INDEX_NAME)
    query_response = index.query(vector=vector, top_k=20, include_metadata=True)
    return query_response

def fetch_chunk_from_pinecone(chunk_id):
    index = pinecone.Index(INDEX_NAME)
    query_response = index.fetch(ids=[chunk_id])
    chunk = index.query(vector=query_response.vectors[str(chunk_id)].values, top_k=1, include_metadata=True)
    return chunk.matches[0]

def rewriteChunk(chunk):
    description = db.getDescription('descriptions.db', chunk['metadata']['source'])

    system_prompt="You are a text analyzer."
    user_prompt=f"This a description of the document: {description}. Here is the chunk we want to situate within the whole document: {chunk['metadata']['text']}. This is the description of the source: {description}. Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. "
    return utils.send_gpt4o_prompt(system_prompt, user_prompt, 200)

def checkRelevance(chunk, user_input, sources):
    newChunk = rewriteChunk(chunk) +": " + chunk['metadata']['text']
    chunk['metadata']['text'] = newChunk
    system_prompt="You are a text analyzer."
    user_prompt=f"This is a chunk extracted from a document: {chunk['metadata']['text']}. Is this chunk provide information relevant to the question: {user_input}? Only answer with a binary score of '1' or '0', remember to only answer with these values."

    if(utils.send_gpt4o_prompt(system_prompt, user_prompt, 50) == "0"):
        print("Chunk is not relevant")
    else:
        print("Chunk is relevant: " + chunk['metadata']['source'])
        #print(chunk['metadata']['text'] + "\n\n")
        sources.append(chunk['metadata']['source']) 
        return chunk
    return "", None

def generate_response(context, user_input):
<<<<<<< HEAD
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "You should answer concisely and not add extra information that is not available in the context. "
        "If you do not know the answer, say that you don't have information on that topic."
    )
    user_prompt = (
        f"Here are the chunks extracted from the document that are relevant to the question: {context}. "
        f"Please provide an answer based on the relevant information. "
        f"Only answer the question based on this information: {user_input}"
    )
    return utils.send_gpt4o_prompt(system_prompt, user_prompt, 200)
=======
    response = openai.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "system", "content": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. You should answer conscisely and not add extra information that is not avaliable in the context. If you do not know the answer, say that you don't have information on that topic."},
            {"role": "user", "content": f"Here are the chunks extracted from the document that are relevant to the question: {user_input}. Please provide a an of the relevant information. Only answer the question based on this information: {context}"}
        ]    )
    return response.choices[0].message.content
>>>>>>> 767f2146d062de66fa6bb5d9480598ebbe1e9cd8

def filter_chunks(chunks, user_input):
    context = ""
    sources = []
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for chunk in chunks:
            futures.append(executor.submit(checkRelevance, chunk, user_input, sources))
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if not result or result == ("", None):
                continue  # skip non-relevant chunks
            context += result['metadata']['text'] + "\n\n"
            if result['metadata']['source'] not in sources:
                sources.append(result['metadata']['source'])
    
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
            output = {"Question": user_input, "Answer": answer, "Source(s)": sources, "Data": result}
            print(json.dumps(output, indent=4))

            #print("\n\n Answer: ")
            #print(answer)
            #checkIfFactual(answer, result)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    main()