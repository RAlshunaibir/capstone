# app.py
from flask import Flask, request, jsonify, render_template
from groq import Groq
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")

# Set Groq API key from environment variable
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=groq_api_key)


def clean_response(text):
    """Remove thinking process from AI response"""
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Remove other thinking markers like <|>...</|>
    text = re.sub(r'<\|>.*?</\|>', '', text, flags=re.DOTALL)
    
    # Remove any text that starts with "Okay," and ends before the actual response
    text = re.sub(r'Okay,.*?(?=\n\n|\n[A-Z]|$)', '', text, flags=re.DOTALL)
    
    # Remove lines that start with common thinking words
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip lines that are clearly thinking process
        if (line.startswith('Okay,') or 
            line.startswith('<think>') or 
            line.startswith('</think>') or
            line.startswith('<|') or
            line.startswith('|>') or
            'thinking' in line.lower() and len(line) < 50):
            continue
        cleaned_lines.append(line)
    
    # Join lines back together
    text = '\n'.join(cleaned_lines)
    
    # Remove extra spaces and return clean text
    return text.strip()

def generate_chat_response(user_msg, history=None):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if history:
        messages += history
    messages.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="qwen-qwq-32b",
        messages=messages,
        temperature=0.7,
        max_completion_tokens=256
    )
    # Clean the response before returning
    return clean_response(response.choices[0].message.content)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    response = generate_chat_response(user_input)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
