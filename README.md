# AI Concierge Agent

Professional AI-powered concierge assistant built with FastAPI and Groq API.

## Features

- **Intelligent Conversation** - Context-aware responses with memory
- **Multi-Domain Expertise** - Travel, scheduling, research, recommendations
- **Voice Input** - Speak your requests naturally
- **Chat History** - Save and resume conversations
- **Mobile Responsive** - Works seamlessly on all devices
- **Real-time Processing** - Fast, accurate responses

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

3. Run locally:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open browser: `http://localhost:8000`

## Deploy on Render

1. Push to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. New Web Service → Connect your repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variable: `GROQ_API_KEY`
6. Deploy

## Tech Stack

- **Backend:** FastAPI, Python 3.10+
- **AI:** Groq API (Llama 3.3 70B)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Deployment:** Render

## License

MIT
