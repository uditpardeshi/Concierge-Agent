from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = FastAPI()

frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

conversations = {}
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

system_prompt = """You are an elite AI Concierge providing 5-star service. Be warm, professional, and CONCISE.

**Your Expertise:**
- Dining, travel, events, and activity recommendations
- Reservations and bookings
- Transportation and logistics
- Problem-solving and special requests
- 24/7 availability with instant responses

**Response Style:**
- Keep answers SHORT and to the point (2-4 sentences max)
- Use bullet points for lists (max 3-4 items)
- Be direct and actionable
- Skip lengthy explanations unless asked
- Offer to elaborate if they want more details

**Tone:** Professional, warm, efficient - like a skilled concierge who values your time."""

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
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"response": "Error: GEMINI_API_KEY not found in .env file"}
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={
                'temperature': 0.8,
                'top_p': 0.9,
                'max_output_tokens': 512,
            },
            system_instruction=system_prompt
        )
        
        chat_session = model.start_chat(history=conversations[session_id])
        response = chat_session.send_message(message.content)
        
        conversations[session_id].append({"role": "user", "parts": [message.content]})
        conversations[session_id].append({"role": "model", "parts": [response.text]})
        
        return {"response": response.text}
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
