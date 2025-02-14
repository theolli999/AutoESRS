from flask import Flask, request, jsonify
from flask_cors import CORS
import runMultipleQuestions
import askQuestion

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['POST'])
def handle_question():
    # Fetch the payload sent from the frontend
    payload = request.get_json()
    
    # Extract questions from payload
    question = payload.get('question')
    
    # Optionally filter out empty questions

    result = askQuestion.ask_question(question)
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    else:
        result = result.__dict__
    filtered_chunks, providedSources = askQuestion.filter_chunks(result['matches'], question)
    answer = askQuestion.generate_response(filtered_chunks, question)
    return jsonify({'answer': answer, 'sources': providedSources})


if __name__ == "__main__":
    app.run(port=8080)