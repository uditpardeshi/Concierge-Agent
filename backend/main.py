from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = FastAPI()

frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

conversations = {}

system_prompt = """You are a personal daily routine assistant. Your ONLY purpose is to help users create personalized daily routines.

You MUST ONLY:
1. Ask about their lifestyle, goals, sleep schedule, work hours, exercise preferences, meals, and hobbies
2. Create detailed personalized daily routines with specific times
3. Modify and improve existing routines

You MUST NOT:
- Answer questions unrelated to daily routines and scheduling
- Discuss topics outside of personal routine planning
- Help with general knowledge, coding, writing, or other tasks

If asked about anything else, politely say: "I can only help with creating personalized daily routines. Please ask me about your schedule, habits, or routine planning."

Be conversational and friendly. Ask one or two questions at a time."""

class Message(BaseModel):
    content: str
    session_id: str = "default"

@app.post("/chat")
async def chat(message: Message):
    try:
        session_id = message.session_id
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversations[session_id].append({
            "role": "user",
            "content": message.content
        })
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return {"response": "Error: GROQ_API_KEY not found in .env file"}
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_prompt}] + conversations[session_id],
                "max_tokens": 1024,
                "temperature": 0.7
            }
        )
        
        if response.status_code != 200:
            return {"response": f"API Error: {response.text}"}
        
        assistant_message = response.json()["choices"][0]["message"]["content"]
        conversations[session_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return {"response": assistant_message}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

@app.get("/")
async def root():
    return FileResponse(frontend_path / "index.html")
