# Multi-Agent AI System

**Created by: Udit Pardeshi & Mrunal Bhavsar**

> A flexible multi-agent orchestration platform that enables AI agents to work together in different execution modes to solve complex tasks more effectively than single-agent systems.

## 🎯 Problem Statement

Traditional single-agent AI systems face significant limitations:
- **Limited perspective**: One agent can only approach a problem from one angle
- **Sequential bottlenecks**: Complex tasks requiring multiple steps are slow
- **No specialization**: A single agent can't be expert in everything
- **Poor scalability**: Adding more complexity to one agent makes it less effective

**Real-world impact**: Businesses need AI systems that can handle complex workflows, provide multiple perspectives, and scale efficiently. Current solutions either use single agents (limited capability) or require manual orchestration (time-consuming and error-prone).

## 💡 Solution

A multi-agent system with **four distinct execution modes** that can be selected based on task requirements:

1. **Concierge Mode** - Single specialized agent for focused tasks
2. **Parallel Mode** - Multiple agents work simultaneously for diverse perspectives
3. **Sequential Mode** - Agents process in pipeline stages for complex workflows
4. **Loop Mode** - Iterative refinement until optimal results are achieved

**Why Agents?** Agents provide autonomous decision-making, can use tools, maintain context, and communicate with each other. By orchestrating multiple agents, we achieve:
- Better results through diverse perspectives (parallel)
- Efficient complex workflows (sequential)
- Continuous improvement (loop)
- Specialized expertise (dedicated agents)

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface Layer                      │
│  ┌──────────────────┐              ┌────────────────────┐  │
│  │  Main Chat UI    │              │  Admin Dashboard   │  │
│  │  - Mode Selector │              │  - Agent Manager   │  │
│  │  - Chat Export   │              │  - Metrics View    │  │
│  └──────────────────┘              └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Multi-Agent Orchestrator                 │  │
│  │  - Execution Mode Router (Single/Parallel/Seq/Loop)  │  │
│  │  - Agent Registry & Lifecycle Management             │  │
│  │  - Message Routing & A2A Communication               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Agent 1    │    │   Agent 2    │    │   Agent N    │
│              │    │              │    │              │
│ - LLM Core   │    │ - LLM Core   │    │ - LLM Core   │
│ - Tools      │    │ - Tools      │    │ - Tools      │
│ - Memory     │    │ - Memory     │    │ - Memory     │
│ - State      │    │ - State      │    │ - State      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Supporting Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Session    │  │     Tool     │  │ Observability│     │
│  │   Memory     │  │  Integration │  │   & Metrics  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Execution Modes

**1. Concierge Mode (Single Agent)**
```
User Input → Agent → Response
```
Best for: Simple queries, personal assistance

**2. Parallel Mode**
```
                  ┌─→ Agent 1 ─┐
User Input ───────┼─→ Agent 2 ─┼──→ Aggregated Response
                  └─→ Agent 3 ─┘
```
Best for: Multiple perspectives, faster processing

**3. Sequential Mode**
```
User Input → Agent 1 → Agent 2 → Agent 3 → Final Response
```
Best for: Multi-step workflows, pipeline processing

**4. Loop Mode**
```
User Input → Agent → Evaluate → [Converged?] ─No─→ Refine → Agent
                                      │
                                     Yes
                                      ↓
                                  Response
```
Best for: Optimization, iterative improvement

## 🔑 Key Agent Concepts Implemented

### 1. **Multi-Agent Orchestration**
- **Implementation**: `MultiAgentSystem` class in `multi_agent_system.py`
- **Features**: 
  - Dynamic agent registration and lifecycle management
  - Four execution modes (single, parallel, sequential, loop)
  - Agent-to-agent (A2A) communication protocol
  - Message routing and coordination
- **Code**: Lines 200-450 in `multi_agent_system.py`

### 2. **Tool Integration & Use**
- **Implementation**: Tool system with MCP protocol support
- **Features**:
  - Google Search tool for real-time information
  - Code execution tool for computational tasks
  - Custom tool registration framework
  - OpenAPI tool integration for external APIs
- **Code**: Lines 50-150 in `multi_agent_system.py`

### 3. **Memory & State Management**
- **Implementation**: `InMemorySessionService` class
- **Features**:
  - Long-term memory storage across sessions
  - Episodic memory for conversation history
  - Context compaction for large conversations
  - Session persistence and retrieval
- **Code**: Lines 500-650 in `multi_agent_system.py`

### 4. **Agent Evaluation & Monitoring**
- **Implementation**: `ObservabilityManager` class in `observability.py`
- **Features**:
  - Performance metrics tracking (response time, success rate)
  - Distributed tracing with span correlation
  - Health monitoring and alerting
  - Agent leaderboard system
- **Code**: Full `observability.py` file

### 5. **Pause/Resume & Long-Running Operations**
- **Implementation**: Agent state management with pause/resume
- **Features**:
  - Graceful agent pause without losing state
  - Resume from exact checkpoint
  - State persistence across operations
- **Code**: Lines 100-200 in `multi_agent_system.py`

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- GROQ API key ([Get one here](https://console.groq.com))

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd kaggle
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

⚠️ **Important**: Never commit your `.env` file. It's already in `.gitignore`.

4. **Start the server**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

5. **Access the application**
- Main Interface: http://localhost:8000
- Admin Dashboard: http://localhost:8000/admin
- API Documentation: http://localhost:8000/docs

## 📖 Usage Guide

### Web Interface

**Main Chat Interface**
1. Select your desired agent mode from the top-right dropdown
2. Type your message and press Send
3. Save conversations using the 💾 button
4. Access chat history from the sidebar

**Admin Dashboard**
1. Click "Admin" link or navigate to `/admin`
2. Manage agents (create, pause, resume)
3. View system metrics and health
4. Monitor deployments and scaling
5. Inspect session memory

### API Usage

**Send a message**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Analyze market trends",
    "session_id": "session_001",
    "execution_mode": "parallel"
  }'
```

**Create a new agent**
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "analyst_001",
    "name": "Market Analyst",
    "system_prompt": "You are a financial market analyst",
    "model": "llama-3.3-70b-versatile"
  }'
```

**Get system metrics**
```bash
curl http://localhost:8000/metrics
```

## 🛠️ Configuration

Edit `backend/config/agent_config.json` to customize:

```json
{
  "default_agents": [
    {
      "agent_id": "concierge_001",
      "name": "AI Concierge",
      "system_prompt": "You are a helpful AI assistant...",
      "model": "llama-3.3-70b-versatile",
      "tools": ["google_search"]
    }
  ],
  "system_config": {
    "max_agents": 50,
    "max_parallel_agents": 5,
    "observability": {
      "log_level": "INFO",
      "enable_tracing": true
    }
  }
}
```

## 📁 Project Structure

```
kaggle/
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   └── agent_config.json      # Agent configurations
│   ├── __init__.py
│   ├── main.py                    # FastAPI application & endpoints
│   ├── multi_agent_system.py     # Core multi-agent orchestration
│   ├── observability.py           # Metrics, logging, tracing
│   ├── agent_deployment.py        # Agent deployment management
│   └── utils.py                   # Utility functions
├── frontend/
│   ├── index.html                 # Main chat interface
│   └── admin.html                 # Admin dashboard
├── .env                           # Environment variables (create this)
├── .env.example                   # Example environment file
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
└── requirements.txt               # Python dependencies
```

## 🎨 Features Showcase

### 1. Dynamic Mode Switching
Switch between execution modes on-the-fly based on task complexity:
- Simple question? Use Concierge mode
- Need multiple perspectives? Use Parallel mode
- Complex workflow? Use Sequential mode
- Need optimization? Use Loop mode

### 2. Tool Integration
Agents can use external tools to enhance capabilities:
- **Google Search**: Real-time information retrieval
- **Code Execution**: Run Python code for calculations
- **Custom Tools**: Easily add your own tools

### 3. Session Memory
Conversations persist across sessions with intelligent memory management:
- Long-term memory for important information
- Episodic memory for conversation context
- Automatic context compaction for efficiency

### 4. Real-time Monitoring
Track system performance and agent behavior:
- Response time metrics
- Success/error rates
- Agent health status
- System resource usage

## 🔧 Technical Details

### Technologies Used
- **Backend**: FastAPI (Python)
- **LLM Provider**: GROQ (Llama 3.3 70B)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Architecture**: Multi-agent orchestration with A2A protocol

### Design Decisions

**Why FastAPI?**
- Async support for concurrent agent execution
- Automatic API documentation
- High performance and easy to use

**Why GROQ?**
- Fast inference times
- Cost-effective
- Good model quality (Llama 3.3)

**Why Multiple Execution Modes?**
- Different tasks require different approaches
- Flexibility for users to choose optimal strategy
- Demonstrates agent orchestration capabilities

## 🐛 Troubleshooting

**Server won't start**
- Check that your GROQ_API_KEY is set in `.env`
- Verify Python version is 3.8+
- Ensure all dependencies are installed

**Agents not responding**
- Verify your GROQ API key is valid
- Check that you have API credits
- Look at server logs for error messages

**UI not updating**
- Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Try incognito/private mode

**Import errors**
- Make sure you're in the `backend` directory when running uvicorn
- Reinstall dependencies: `pip install -r requirements.txt`

## 📊 Performance Considerations

- **Parallel mode**: Faster for independent tasks, uses more API calls
- **Sequential mode**: Slower but better for dependent tasks
- **Loop mode**: Variable time based on convergence criteria
- **Memory**: Context compaction prevents memory bloat

## 🔐 Security Notes

- Never commit API keys or secrets
- Use environment variables for sensitive data
- The `.env` file is gitignored by default
- Validate all user inputs in production

## 📝 License

MIT License - feel free to use this project however you'd like.

## 👥 Authors

**Udit Pardeshi & Mrunal Bhavsar**

Built as a learning project to explore multi-agent systems and orchestration patterns. The system demonstrates practical applications of agent coordination, tool use, and memory management.

## 📧 Contact

For questions or feedback about this project, please open an issue on GitHub.

---

**Note**: This project was built for educational purposes to demonstrate multi-agent system concepts and agent orchestration patterns.
