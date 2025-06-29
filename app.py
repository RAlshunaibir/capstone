# app.py
# This is a FastAPI application for a chatbot using Groq API
# You can modify this file to change the chatbot behavior
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from groq import Groq
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Set Groq API key from environment variable
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=groq_api_key)

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    response = generate_chat_response(chat_request.message)
    return ChatResponse(response=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
