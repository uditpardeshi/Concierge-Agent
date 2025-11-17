"""
Multi-Agent System with comprehensive features:
- Agent powered by LLM
- Parallel/Sequential/Loop agents
- Tools (MCP, custom, built-in, OpenAPI)
- Long-running operations
- Sessions & Memory
- Observability
- Agent evaluation
- A2A Protocol
- Agent deployment
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Logging and Observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentMetrics:
    agent_id: str
    start_time: float
    end_time: Optional[float] = None
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time

@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    sender: str = ""
    recipient: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentContext:
    session_id: str
    agent_id: str
    state: AgentState = AgentState.IDLE
    memory: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    metrics: Optional[AgentMetrics] = None

# Memory Management
class MemoryBank:
    def __init__(self):
        self.long_term_memory: Dict[str, Any] = {}
        self.episodic_memory: List[Dict[str, Any]] = []
        self.semantic_memory: Dict[str, Any] = {}
    
    def store_long_term(self, key: str, value: Any):
        self.long_term_memory[key] = value
    
    def retrieve_long_term(self, key: str) -> Any:
        return self.long_term_memory.get(key)
    
    def add_episode(self, episode: Dict[str, Any]):
        episode['timestamp'] = datetime.now()
        self.episodic_memory.append(episode)
    
    def compact_context(self, max_size: int = 1000) -> str:
        """Context compaction for large memory"""
        recent_episodes = self.episodic_memory[-max_size:]
        return json.dumps(recent_episodes, default=str)

class InMemorySessionService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.memory_banks: Dict[str, MemoryBank] = {}
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now(),
            'agents': {},
            'messages': [],
            'state': {}
        }
        self.memory_banks[session_id] = MemoryBank()
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)
    
    def get_memory_bank(self, session_id: str) -> Optional[MemoryBank]:
        return self.memory_banks.get(session_id)

# Tools System
class Tool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

class GoogleSearchTool(Tool):
    def __init__(self):
        super().__init__("google_search", "Search the web using Google")
    
    async def execute(self, query: str) -> Dict[str, Any]:
        # Simulated Google Search
        return {
            "query": query,
            "results": [
                {"title": f"Result for {query}", "url": "https://example.com", "snippet": f"Information about {query}"}
            ]
        }

class CodeExecutionTool(Tool):
    def __init__(self):
        super().__init__("code_execution", "Execute Python code")
    
    async def execute(self, code: str) -> Dict[str, Any]:
        try:
            # Safe code execution (in production, use sandboxing)
            result = eval(code) if code.strip() else None
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}

class MCPTool(Tool):
    """Model Context Protocol Tool"""
    def __init__(self, server_url: str):
        super().__init__("mcp_tool", "MCP Protocol Tool")
        self.server_url = server_url
    
    async def execute(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # MCP protocol implementation
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params
        }
        try:
            response = requests.post(self.server_url, json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

class OpenAPITool(Tool):
    def __init__(self, api_spec: Dict[str, Any]):
        super().__init__("openapi_tool", "OpenAPI Tool")
        self.api_spec = api_spec
    
    async def execute(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        # OpenAPI tool implementation
        base_url = self.api_spec.get("servers", [{}])[0].get("url", "")
        url = f"{base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Agent System
class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, system_prompt: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.system_prompt = system_prompt
        self.tools: Dict[str, Tool] = {}
        self.state = AgentState.IDLE
        self.context: Optional[AgentContext] = None
        self.metrics: Optional[AgentMetrics] = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Start unpaused
    
    def add_tool(self, tool: Tool):
        self.tools[tool.name] = tool
    
    async def pause(self):
        self.state = AgentState.PAUSED
        self.pause_event.clear()
        logger.info(f"Agent {self.agent_id} paused")
    
    async def resume(self):
        self.state = AgentState.RUNNING
        self.pause_event.set()
        logger.info(f"Agent {self.agent_id} resumed")
    
    @abstractmethod
    async def process(self, message: Message) -> Message:
        pass

class LLMAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, system_prompt: str = "", model: str = "llama-3.3-70b-versatile"):
        super().__init__(agent_id, name, system_prompt)
        self.model = model
        self.api_key = os.getenv('GROQ_API_KEY')
    
    async def process(self, message: Message) -> Message:
        await self.pause_event.wait()  # Wait if paused
        
        self.state = AgentState.RUNNING
        if not self.metrics:
            self.metrics = AgentMetrics(self.agent_id, time.time())
        
        try:
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message.content}
            ]
            
            # Add tool descriptions
            if self.tools:
                tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools.values()])
                messages[0]["content"] += f"\n\nAvailable tools:\n{tool_descriptions}"
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Check for tool usage
                if "use_tool:" in content:
                    content = await self._handle_tool_usage(content)
                
                self.metrics.success_count += 1
                self.metrics.total_tokens += result.get("usage", {}).get("total_tokens", 0)
                
                return Message(
                    content=content,
                    sender=self.agent_id,
                    recipient=message.sender,
                    metadata={"model": self.model, "tokens": result.get("usage", {})}
                )
            else:
                raise Exception(f"LLM API error: {response.text}")
                
        except Exception as e:
            self.metrics.error_count += 1
            self.state = AgentState.FAILED
            logger.error(f"Agent {self.agent_id} failed: {e}")
            return Message(
                content=f"Error: {str(e)}",
                sender=self.agent_id,
                recipient=message.sender
            )
        finally:
            self.metrics.execution_count += 1
            if self.state != AgentState.FAILED:
                self.state = AgentState.COMPLETED
    
    async def _handle_tool_usage(self, content: str) -> str:
        # Simple tool usage parser
        lines = content.split('\n')
        result_lines = []
        
        for line in lines:
            if line.startswith("use_tool:"):
                tool_call = line.replace("use_tool:", "").strip()
                try:
                    tool_data = json.loads(tool_call)
                    tool_name = tool_data.get("name")
                    tool_params = tool_data.get("params", {})
                    
                    if tool_name in self.tools:
                        tool_result = await self.tools[tool_name].execute(**tool_params)
                        result_lines.append(f"Tool result: {json.dumps(tool_result)}")
                    else:
                        result_lines.append(f"Tool '{tool_name}' not found")
                except Exception as e:
                    result_lines.append(f"Tool execution error: {str(e)}")
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)

# Agent Orchestration
class AgentOrchestrator:
    def __init__(self, session_service: InMemorySessionService):
        self.agents: Dict[str, BaseAgent] = {}
        self.session_service = session_service
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")
    
    async def run_parallel_agents(self, agent_ids: List[str], message: Message) -> List[Message]:
        """Run multiple agents in parallel"""
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self.agents:
                task = asyncio.create_task(self.agents[agent_id].process(message))
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Message)]
    
    async def run_sequential_agents(self, agent_ids: List[str], initial_message: Message) -> Message:
        """Run agents sequentially, passing output to next agent"""
        current_message = initial_message
        
        for agent_id in agent_ids:
            if agent_id in self.agents:
                current_message = await self.agents[agent_id].process(current_message)
        
        return current_message
    
    async def run_loop_agents(self, agent_ids: List[str], message: Message, max_iterations: int = 5) -> List[Message]:
        """Run agents in a loop until convergence or max iterations"""
        results = []
        current_message = message
        
        for i in range(max_iterations):
            iteration_results = []
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    result = await self.agents[agent_id].process(current_message)
                    iteration_results.append(result)
                    current_message = result
            
            results.extend(iteration_results)
            
            # Check for convergence (simplified)
            if len(iteration_results) > 0 and "CONVERGED" in iteration_results[-1].content:
                break
        
        return results

# A2A Protocol (Agent-to-Agent Communication)
class A2AProtocol:
    def __init__(self):
        self.message_queue: Dict[str, List[Message]] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> agent_ids
    
    def subscribe(self, agent_id: str, topic: str):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(agent_id)
    
    async def publish(self, topic: str, message: Message):
        if topic in self.subscriptions:
            for agent_id in self.subscriptions[topic]:
                if agent_id not in self.message_queue:
                    self.message_queue[agent_id] = []
                self.message_queue[agent_id].append(message)
    
    def get_messages(self, agent_id: str) -> List[Message]:
        messages = self.message_queue.get(agent_id, [])
        self.message_queue[agent_id] = []  # Clear after retrieval
        return messages

# Agent Evaluation
class AgentEvaluator:
    def __init__(self):
        self.evaluation_metrics: Dict[str, Dict[str, float]] = {}
    
    def evaluate_agent(self, agent: BaseAgent, test_cases: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate agent performance"""
        if not agent.metrics:
            return {"error": 1.0}
        
        metrics = {
            "success_rate": agent.metrics.success_count / max(agent.metrics.execution_count, 1),
            "error_rate": agent.metrics.error_count / max(agent.metrics.execution_count, 1),
            "avg_response_time": agent.metrics.duration() / max(agent.metrics.execution_count, 1),
            "total_executions": agent.metrics.execution_count
        }
        
        self.evaluation_metrics[agent.agent_id] = metrics
        return metrics
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get agent performance leaderboard"""
        leaderboard = []
        for agent_id, metrics in self.evaluation_metrics.items():
            leaderboard.append({
                "agent_id": agent_id,
                "score": metrics.get("success_rate", 0) * 100,
                **metrics
            })
        return sorted(leaderboard, key=lambda x: x["score"], reverse=True)

# Main Multi-Agent System
class MultiAgentSystem:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.orchestrator = AgentOrchestrator(self.session_service)
        self.a2a_protocol = A2AProtocol()
        self.evaluator = AgentEvaluator()
        self.tools_registry: Dict[str, Tool] = {}
        
        # Initialize built-in tools
        self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self):
        """Initialize built-in tools"""
        self.tools_registry["google_search"] = GoogleSearchTool()
        self.tools_registry["code_execution"] = CodeExecutionTool()
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        return self.session_service.create_session(session_id)
    
    def register_agent(self, agent: BaseAgent):
        self.orchestrator.register_agent(agent)
    
    def register_tool(self, tool: Tool):
        self.tools_registry[tool.name] = tool
    
    def add_tool_to_agent(self, agent_id: str, tool_name: str):
        if agent_id in self.orchestrator.agents and tool_name in self.tools_registry:
            self.orchestrator.agents[agent_id].add_tool(self.tools_registry[tool_name])
    
    async def process_message(self, session_id: str, message: Message, execution_mode: str = "single") -> Union[Message, List[Message]]:
        """Process message with different execution modes"""
        session = self.session_service.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        # Store message in session
        session["messages"].append(message)
        
        # Get memory bank for context
        memory_bank = self.session_service.get_memory_bank(session_id)
        if memory_bank:
            memory_bank.add_episode({
                "type": "user_message",
                "content": message.content,
                "session_id": session_id
            })
        
        # Execute based on mode
        if execution_mode == "parallel":
            agent_ids = list(self.orchestrator.agents.keys())
            return await self.orchestrator.run_parallel_agents(agent_ids, message)
        elif execution_mode == "sequential":
            agent_ids = list(self.orchestrator.agents.keys())
            return await self.orchestrator.run_sequential_agents(agent_ids, message)
        elif execution_mode == "loop":
            agent_ids = list(self.orchestrator.agents.keys())
            return await self.orchestrator.run_loop_agents(agent_ids, message)
        else:
            # Single agent execution
            if self.orchestrator.agents:
                agent = list(self.orchestrator.agents.values())[0]
                result = await agent.process(message)
                
                # Store result in memory
                if memory_bank:
                    memory_bank.add_episode({
                        "type": "agent_response",
                        "content": result.content,
                        "agent_id": agent.agent_id,
                        "session_id": session_id
                    })
                
                return result
            else:
                return Message(content="No agents available", sender="system")
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for specific agent"""
        if agent_id in self.orchestrator.agents:
            agent = self.orchestrator.agents[agent_id]
            if agent.metrics:
                return {
                    "agent_id": agent_id,
                    "state": agent.state.value,
                    "execution_count": agent.metrics.execution_count,
                    "success_count": agent.metrics.success_count,
                    "error_count": agent.metrics.error_count,
                    "total_tokens": agent.metrics.total_tokens,
                    "duration": agent.metrics.duration()
                }
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "total_agents": len(self.orchestrator.agents),
            "active_sessions": len(self.session_service.sessions),
            "total_tools": len(self.tools_registry),
            "agent_states": {
                agent_id: agent.state.value 
                for agent_id, agent in self.orchestrator.agents.items()
            }
        }

# Factory for easy setup
def create_multi_agent_system() -> MultiAgentSystem:
    """Factory function to create a fully configured multi-agent system"""
    system = MultiAgentSystem()
    
    # Create default agents
    concierge_agent = LLMAgent(
        "concierge_001",
        "AI Concierge",
        "You are an elite AI Concierge providing 5-star service. Be warm, professional, and helpful."
    )
    
    assistant_agent = LLMAgent(
        "assistant_001", 
        "AI Assistant",
        "You are a helpful AI assistant. Provide accurate and useful information."
    )
    
    # Register agents
    system.register_agent(concierge_agent)
    system.register_agent(assistant_agent)
    
    # Add tools to agents
    system.add_tool_to_agent("concierge_001", "google_search")
    system.add_tool_to_agent("assistant_001", "code_execution")
    
    return system