# Architecture Documentation

## System Architecture Overview

This document provides detailed technical architecture of the Multi-Agent System.

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  ┌──────────────────────┐         ┌──────────────────────┐        │
│  │   Web Browser UI     │         │   API Clients        │        │
│  │   - Chat Interface   │         │   - REST API         │        │
│  │   - Admin Dashboard  │         │   - Webhooks         │        │
│  └──────────────────────┘         └──────────────────────┘        │
└────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Server                             │ │
│  │  - Request Routing                                            │ │
│  │  - Authentication & Validation                                │ │
│  │  - Response Formatting                                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              MultiAgentSystem (Core Orchestrator)             │ │
│  │                                                                │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │ │
│  │  │ Agent Registry │  │ Message Router │  │ Execution Mode │ │ │
│  │  │  - Register    │  │  - Route msgs  │  │  - Single      │ │ │
│  │  │  - Discover    │  │  - A2A comm    │  │  - Parallel    │ │ │
│  │  │  - Lifecycle   │  │  - Broadcast   │  │  - Sequential  │ │ │
│  │  └────────────────┘  └────────────────┘  │  - Loop        │ │ │
│  │                                            └────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Agent 1    │  │   Agent 2    │  │   Agent N    │            │
│  │              │  │              │  │              │            │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │
│  │ │ LLM Core │ │  │ │ LLM Core │ │  │ │ LLM Core │ │            │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │
│  │ │  Tools   │ │  │ │  Tools   │ │  │ │  Tools   │ │            │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │
│  │ │  Memory  │ │  │ │  Memory  │ │  │ │  Memory  │ │            │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │
│  │ │  State   │ │  │ │  State   │ │  │ │  State   │ │            │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      SERVICES LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Session    │  │     Tool     │  │Observability │            │
│  │   Service    │  │  Integration │  │   Manager    │            │
│  │              │  │              │  │              │            │
│  │ - Memory     │  │ - Google     │  │ - Logging    │            │
│  │ - Context    │  │ - Code Exec  │  │ - Tracing    │            │
│  │ - History    │  │ - Custom     │  │ - Metrics    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  GROQ API    │  │ Google Search│  │  Other APIs  │            │
│  │  (LLM)       │  │              │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
```

## Execution Mode Details

### 1. Single Agent Mode (Concierge)

```
┌─────────┐
│  User   │
└────┬────┘
     │ Message
     ▼
┌─────────────────┐
│ MultiAgentSystem│
└────┬────────────┘
     │ Route to Agent
     ▼
┌─────────────────┐
│   Agent 1       │
│  ┌───────────┐  │
│  │ Process   │  │
│  │ Message   │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Use Tools │  │
│  │ (optional)│  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Generate  │  │
│  │ Response  │  │
│  └───────────┘  │
└────┬────────────┘
     │ Response
     ▼
┌─────────┐
│  User   │
└─────────┘
```

### 2. Parallel Mode

```
                    ┌─────────────────┐
                    │   Agent 1       │
                    │  - Perspective A│
                    └────┬────────────┘
                         │ Response A
                         │
┌─────────┐         ┌────▼────────────┐
│  User   │─Message─┤ MultiAgentSystem│
└─────────┘         └────┬────────────┘
     ▲                   │
     │                   │
     │              ┌────▼────────────┐
     │              │   Agent 2       │
     │              │  - Perspective B│
     │              └────┬────────────┘
     │                   │ Response B
     │                   │
     │              ┌────▼────────────┐
     │              │   Agent 3       │
     │              │  - Perspective C│
     │              └────┬────────────┘
     │                   │ Response C
     │                   │
     │              ┌────▼────────────┐
     │              │   Aggregator    │
     │              │  - Combine      │
     │              │  - Synthesize   │
     └──────────────┤  - Format       │
       Aggregated   └─────────────────┘
       Response
```

### 3. Sequential Mode

```
┌─────────┐
│  User   │
└────┬────┘
     │ Initial Message
     ▼
┌─────────────────┐
│   Agent 1       │
│  (Researcher)   │
│  - Gather data  │
└────┬────────────┘
     │ Research Results
     ▼
┌─────────────────┐
│   Agent 2       │
│  (Analyzer)     │
│  - Analyze data │
└────┬────────────┘
     │ Analysis
     ▼
┌─────────────────┐
│   Agent 3       │
│  (Writer)       │
│  - Create report│
└────┬────────────┘
     │ Final Report
     ▼
┌─────────┐
│  User   │
└─────────┘
```

### 4. Loop Mode

```
┌─────────┐
│  User   │
└────┬────┘
     │ Initial Message
     ▼
┌─────────────────┐
│   Agent         │
│  - Process      │◄─────┐
│  - Generate     │      │
└────┬────────────┘      │
     │ Output            │
     ▼                   │
┌─────────────────┐      │
│  Evaluator      │      │
│  - Check quality│      │
│  - Convergence? │      │
└────┬────────────┘      │
     │                   │
     ├─No─► Refine ──────┘
     │      Prompt
     │
     │ Yes
     ▼
┌─────────┐
│  User   │
└─────────┘
```

## Component Details

### MultiAgentSystem Class

**Responsibilities:**
- Agent lifecycle management (register, pause, resume, remove)
- Message routing between agents
- Execution mode coordination
- A2A (Agent-to-Agent) communication
- Tool integration management

**Key Methods:**
```python
register_agent(agent)           # Add new agent to system
process_message(session, msg, mode)  # Main entry point
_execute_parallel(agents, msg)  # Parallel execution
_execute_sequential(agents, msg) # Sequential execution
_execute_loop(agent, msg)       # Loop execution
```

### LLMAgent Class

**Responsibilities:**
- LLM interaction (GROQ API)
- Tool execution
- State management
- Message processing

**Key Attributes:**
```python
agent_id: str          # Unique identifier
name: str              # Human-readable name
system_prompt: str     # Agent's instructions
model: str             # LLM model to use
tools: List[Tool]      # Available tools
state: AgentState      # Current state (IDLE, BUSY, PAUSED, FAILED)
```

### Tool System

**Architecture:**
```
┌─────────────────┐
│   Tool Base     │
│   (Abstract)    │
└────┬────────────┘
     │
     ├──► GoogleSearchTool
     ├──► CodeExecutionTool
     ├──► MCPTool
     ├──► OpenAPITool
     └──► CustomTool (User-defined)
```

**Tool Interface:**
```python
class Tool:
    def __init__(self, name, description)
    async def execute(**kwargs) -> Dict
    def get_schema() -> Dict
```

### Session Memory System

**Memory Types:**

1. **Short-term Memory**: Current conversation context
2. **Long-term Memory**: Persistent facts and information
3. **Episodic Memory**: Conversation history
4. **Semantic Memory**: Knowledge graphs (future)

**Memory Flow:**
```
User Message
     │
     ▼
┌─────────────────┐
│ Session Service │
│  - Load context │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│     Agent       │
│  - Process with │
│    context      │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Session Service │
│  - Save memory  │
│  - Compact if   │
│    needed       │
└─────────────────┘
```

### Observability System

**Components:**

1. **Logger**: Structured logging with correlation IDs
2. **Tracer**: Distributed tracing with spans
3. **Metrics**: Counters, gauges, histograms, timers
4. **Alerting**: Rule-based alerts
5. **Dashboards**: Metric visualization

**Metrics Flow:**
```
Agent Action
     │
     ▼
┌─────────────────┐
│ Agent Observer  │
│  - Record metric│
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│ Metrics Manager │
│  - Aggregate    │
│  - Store        │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│   Dashboard     │
│  - Visualize    │
└─────────────────┘
```

## Data Flow

### Message Processing Flow

```
1. User sends message via Web UI
   │
   ▼
2. FastAPI receives POST /chat
   │
   ▼
3. MultiAgentSystem.process_message()
   │
   ├─► Load session context
   │
   ├─► Select execution mode
   │   │
   │   ├─► Single: Route to one agent
   │   ├─► Parallel: Fan out to multiple agents
   │   ├─► Sequential: Chain agents
   │   └─► Loop: Iterate until convergence
   │
   ▼
4. Agent(s) process message
   │
   ├─► Use tools if needed
   ├─► Query LLM
   └─► Generate response
   │
   ▼
5. Save to session memory
   │
   ▼
6. Record metrics
   │
   ▼
7. Return response to user
```

### Tool Execution Flow

```
1. Agent decides to use tool
   │
   ▼
2. Tool.execute() called
   │
   ├─► GoogleSearchTool
   │   └─► Query Google API
   │
   ├─► CodeExecutionTool
   │   └─► Execute Python code in sandbox
   │
   └─► CustomTool
       └─► User-defined logic
   │
   ▼
3. Tool returns result
   │
   ▼
4. Agent incorporates result
   │
   ▼
5. Agent continues processing
```

## State Management

### Agent States

```
┌──────────┐
│   IDLE   │ ◄─────────────┐
└────┬─────┘                │
     │ process_message()    │
     ▼                      │
┌──────────┐                │
│   BUSY   │                │
└────┬─────┘                │
     │                      │
     ├─► Success ───────────┘
     │
     ├─► pause() ──► ┌──────────┐
     │               │  PAUSED  │
     │               └────┬─────┘
     │                    │ resume()
     │                    └─────────┐
     │                              │
     └─► Error ──► ┌──────────┐    │
                   │  FAILED  │    │
                   └────┬─────┘    │
                        │ reset()  │
                        └──────────┘
```

### Session State

```
Session Created
     │
     ▼
┌─────────────────┐
│  Active Session │
│  - Messages     │
│  - Context      │
│  - Memory       │
└────┬────────────┘
     │
     ├─► User inactive ──► Persist to storage
     │
     ├─► User returns ───► Load from storage
     │
     └─► Timeout ────────► Archive session
```

## Security Considerations

1. **API Key Management**: Environment variables, never in code
2. **Input Validation**: All user inputs sanitized
3. **Rate Limiting**: Prevent API abuse
4. **Tool Sandboxing**: Code execution in isolated environment
5. **Session Isolation**: Each session has separate memory

## Performance Optimizations

1. **Async Processing**: All I/O operations are async
2. **Connection Pooling**: Reuse HTTP connections
3. **Context Compaction**: Reduce memory usage for long conversations
4. **Caching**: Cache tool results when appropriate
5. **Parallel Execution**: Utilize concurrent processing

## Scalability

**Current Limitations:**
- In-memory session storage (not distributed)
- Single server instance
- No load balancing

**Future Improvements:**
- Redis for distributed sessions
- Horizontal scaling with load balancer
- Message queue for async processing
- Database for persistent storage

## Technology Stack

- **Backend Framework**: FastAPI
- **LLM Provider**: GROQ (Llama 3.3 70B)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Python Version**: 3.8+
- **Key Libraries**:
  - `httpx`: Async HTTP client
  - `pydantic`: Data validation
  - `python-dotenv`: Environment management

## Deployment Architecture

```
┌─────────────────────────────────────┐
│         Load Balancer               │
│         (Future)                    │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐       ┌─────────┐
│ Server 1│       │ Server 2│
│         │       │         │
│ FastAPI │       │ FastAPI │
│ + Agents│       │ + Agents│
└─────────┘       └─────────┘
    │                 │
    └────────┬────────┘
             │
             ▼
    ┌────────────────┐
    │  Shared Redis  │
    │  (Sessions)    │
    └────────────────┘
```

## Monitoring & Observability

**Metrics Collected:**
- Request count and latency
- Agent response times
- Tool execution times
- Error rates
- Memory usage
- Active sessions

**Logging Levels:**
- DEBUG: Detailed execution flow
- INFO: Important events
- WARNING: Potential issues
- ERROR: Failures and exceptions

**Tracing:**
- Each request gets a trace ID
- Spans for each agent interaction
- Tool execution spans
- Database query spans (future)

---

This architecture is designed to be:
- **Modular**: Easy to add new agents, tools, or execution modes
- **Scalable**: Can grow from single server to distributed system
- **Observable**: Comprehensive logging and metrics
- **Maintainable**: Clear separation of concerns
- **Extensible**: Plugin architecture for tools and agents
