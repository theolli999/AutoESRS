import os
import json
from pinecone import Pinecone, ServerlessSpec
import askQuestion
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

pinecone = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

from openai import OpenAI
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def findUniqueSources(chunks):
    sources = []
    for chunk in chunks:
        if chunk['metadata']['source'] not in sources:
            sources.append(chunk['metadata']['source'])
    return sources

def checkSources(answer, question, sources):
    index = pinecone.Index("test2")

    # Generera embedding för svaret
    embedding_response = openai.embeddings.create(
        input=answer,
        model="text-embedding-ada-002"
    )
    answer_vector = embedding_response.data[0].embedding
    combinedText = ""
    for source in sources:
        # Utför en likhetssökning i Pinecone-indexen för varje källa
        query_response = index.query(vector=answer_vector, top_k=5, include_metadata=True, filter={"source": source})
        if query_response.matches:
            for match in query_response.matches:
                combinedText += match.metadata['text'] + "\n\n"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Your job is to review the generated answer and see if there are any more information relevant to extract to answer the question. You are going to answer with a score of 1 to 10 where 1 is that all the information needs to be extracted and 10 is no extra context needs to be distracted. A 10 does not mean that the sentences match perfectly, but that all the relevant information from the provided document is included in the answer. Give a brief motivation to what is missing in the answer that could be provided from the origin source and what could be better. Do not reason about how the text could be written better, only judge if there are more information that needs to be extracted. Keep your answers short, especially of you give a high score."},
            {"role": "user", "content": f"This is an generated answer: {answer} to the question: {question}. I want you to look into this information: {combinedText} and see if there are any more information relevant to extract to answer the question. You are going to answer with a score of 1 to 10 where 1 is that all the information needs to be extracted and 10 is no extra context needs to be distracted. A 10 does not mean that the sentences match perfectly, but that all the relevant information from the provided document is included in the answer. Give a brief motivation to what is missing in the answer that could be provided from the origin source and what could be better. Do not reason about how the text could be written better, only judge if there are more information that needs to be extracted"}
        ],
        max_tokens=200
    )

    return response.choices[0].message.content

def import_questions_from_csv(filepath):
    df = pd.read_csv(filepath)
    questions = df.iloc[:, 1].tolist()  # Assuming the second column contains the questions
    return questions

def run_multiple_questions(questions):
    results = {}
    for idx, question in enumerate(questions):
        try:
            result = askQuestion.ask_question(question)
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            else:
                result = result.__dict__
            sources = findUniqueSources(result['matches'])
            filtered_chunks, providedSources = askQuestion.filter_chunks(result['matches'], question)
            print("Provided sources: ", providedSources)
            answer = askQuestion.generate_response(filtered_chunks, question)
            sourcesReview = checkSources(answer, question, sources)
            results[question] = {'answer': answer, 'sourcesReview': sourcesReview, "sources": providedSources}
        except Exception as e:
            results[question] = {'error': str(e)}
    return results

if __name__ == '__main__':
    #questions = import_questions_from_csv("./data.csv")
    questions = [
        "Can I bring my dog to work?",
        "Does the company have a workplace accident prevention policy or management system?"
       ]
    

    #questions = ["Does the company have a transition plan?"]
    #print(questions)
    
    results = run_multiple_questions(questions)
    print(json.dumps(results, indent=4))

    # for question, result in results.items():
    #     if 'error' in result:
    #         print(f"Question: {question}\nError: {result['error']}\n")
    #     else:
    #         print(f"Question: {question}\nAnswer: {result['answer']}\n")
    #         #print("Sources Review: ", result['sourcesReview'])
