import concurrent.futures
import os
from pdfminer.high_level import extract_text
import utils
import json

if __name__ == "__main__":
    directory = './documents'
    id = 0
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                futures.append((filename, executor.submit(extract_text, filepath)))

    all_documents = ""
    for filename, future in futures:
        text = future.result()
        all_documents += text + "\n"
        
    # Define multiple questions
    questions = [
        "Can i bring my dog to work?",
        "What is the company's policy on remote work?"
    ]
    
    # Prepare a system prompt that expects an array of JSON objects.
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the provided questions. "
        "You should answer concisely and not add extra information that is not available in the context. "
        "Answer in strict JSON format as an array of objects. Each object must have the keys: question, document, section, answer. "
        "If you do not know the answer for a given question, say that you don't have information on that topic."
    )
    
    # Prepare the user prompt listing all questions.
    questions_text = "\n".join(questions)
    user_prompt = (
        f"Here are the chunks extracted from the document that are relevant to the questions: {all_documents}\n"
        f"Please provide answers for the following questions based solely on this information:\n{questions_text}"
    )
    response = utils.send_o3_prompt(system_prompt, user_prompt)
    print(response)
    #json_response = json.loads(response.choices[0].message.content)

    #print(json.dumps(json_response, indent=4))
    #rint(json_response[0]['answer'])
