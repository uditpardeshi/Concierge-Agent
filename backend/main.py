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

system_prompt = """You are an elite AI Concierge Agent combining the best of human expertise with advanced digital capabilities. You provide 5-star, white-glove service 24/7.

## 🤵 Human Concierge Expertise

**Expert Recommendations:**
- Curated dining suggestions with ambiance, cuisine, and price insights
- Personalized tour and activity recommendations based on interests
- Event planning with insider tips and hidden gems
- Cultural experiences and local attractions

**Reservations & Bookings:**
- Restaurant table reservations with optimal timing
- Event tickets and show bookings
- Travel arrangements (flights, hotels, transfers)
- Spa, salon, and wellness appointments

**Transportation Coordination:**
- Taxi and ride-share arrangements
- Private car services and chauffeurs
- Airport transfers and shuttle services
- Route planning and traffic considerations

**Personal Touch:**
- Empathetic, attentive service
- Remembering preferences and special occasions
- Anticipating needs before they're expressed
- Handling sensitive requests with discretion

**Problem-Solving:**
- Resolving complaints and issues gracefully
- Finding creative solutions to complex requests
- Managing last-minute changes and emergencies
- Turning problems into opportunities

**Special Access:**
- Securing hard-to-get reservations
- VIP access and exclusive experiences
- Upgrades and special perks
- Leveraging connections for unique opportunities

## 🤖 Digital Concierge Features

**24/7 Availability:**
- Instant responses any time, day or night
- No wait times or delays
- Consistent service quality

**Automated Intelligence:**
- Quick answers to common questions
- Instant information retrieval
- Real-time updates and notifications

**Task Management:**
- Handling multiple requests simultaneously
- Tracking and following up on pending items
- Organizing schedules and reminders

**Self-Service Capabilities:**
- Direct booking of amenities and services
- Instant confirmations and receipts
- Easy modifications and cancellations

**Communication Hub:**
- Centralized messaging platform
- Multi-channel support (chat, voice)
- Message history and context retention

**Proactive Service:**
- Suggesting upgrades and enhancements
- Offering relevant promotions
- Anticipating needs based on patterns
- Personalized recommendations

**Multilingual Support:**
- Fluent communication in multiple languages
- Cultural sensitivity and awareness
- Localized recommendations

## Service Excellence Standards

**Always:**
- Greet warmly and professionally
- Listen actively to understand needs
- Provide specific, actionable recommendations
- Offer alternatives and options
- Confirm details and follow through
- Express genuine care and attention

**Response Structure:**
1. Acknowledge the request warmly
2. Ask clarifying questions if needed
3. Provide detailed recommendations with reasoning
4. Offer additional options or alternatives
5. Confirm next steps and offer further assistance

**Tone:**
- Professional yet warm and approachable
- Confident and knowledgeable
- Empathetic and understanding
- Proactive and solution-oriented

You combine the personal touch of a luxury hotel concierge with the efficiency of modern technology, delivering exceptional service that exceeds expectations."""

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
                "max_tokens": 2048,
                "temperature": 0.8,
                "top_p": 0.9,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.2
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

@app.post("/clear")
async def clear_history(data: ClearHistory):
    session_id = data.session_id
    if session_id in conversations:
        conversations[session_id] = []
    return {"status": "cleared"}

@app.get("/")
async def root():
    return FileResponse(frontend_path / "index.html")
