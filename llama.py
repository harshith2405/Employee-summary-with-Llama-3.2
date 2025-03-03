from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables from .env
import os
load_dotenv()
# Groq API Config
GROQ_API_KEY=os.getenv('GROQ_API_KEY')
GROQ_API_URL=os.getenv('GROQ_API_URL')
def call_groq_llama(input_text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",  # Change model name if needed
        "messages": [{"role": "user", "content": input_text}]
    }
    
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.json()}"

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Llama-3 Flask API!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("input", "")

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    output = call_groq_llama(user_input)
    return jsonify({"input": user_input, "output": output})

if __name__ == "__main__":
    app.run(debug=True)

