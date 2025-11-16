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

system_prompt = """You are an elite AI Concierge providing 5-star service. Be warm, professional, and helpful.

**Your Expertise:**
- Dining, travel, events, and activity recommendations
- Reservations and bookings
- Transportation and logistics
- Problem-solving and special requests
- 24/7 availability with instant responses

**Response Style:**
- Provide clear, informative answers (4-6 sentences)
- Use bullet points when listing options or steps
- Be thorough but not overwhelming
- Include relevant details and context
- Offer additional help when appropriate

**Tone:** Professional, warm, knowledgeable - like a skilled concierge who provides complete assistance."""

class Message(BaseModel):
    content: str
    session_id: str = "default"

class ClearHistory(BaseModel):
    session_id: str

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
                "temperature": 0.8,
                "top_p": 0.9,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.2
            },
            timeout=30,
            verify=True
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

@app.post("/clear")
async def clear_history(data: ClearHistory):
    session_id = data.session_id
    if session_id in conversations:
        conversations[session_id] = []
    return {"status": "cleared"}

@app.get("/")
async def root():
    return FileResponse(frontend_path / "index.html")
