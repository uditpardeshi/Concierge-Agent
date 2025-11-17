from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from typing import Dict, List, Any, Optional

# Import multi-agent system components
try:
    from .multi_agent_system import (
        MultiAgentSystem, LLMAgent, Message as AgentMessage,
        create_multi_agent_system
    )
    from .agent_deployment import (
        AgentDeploymentManager, DeploymentConfig, AgentRegistry, HealthChecker
    )
    from .observability import ObservabilityManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from multi_agent_system import (
        MultiAgentSystem, LLMAgent, Message as AgentMessage,
        create_multi_agent_system
    )
    from agent_deployment import (
        AgentDeploymentManager, DeploymentConfig, AgentRegistry, HealthChecker
    )
    from observability import ObservabilityManager

load_dotenv()

app = FastAPI(title="Multi-Agent System API", version="1.0.0")

frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Initialize multi-agent system
# This takes a while to load on first run
mas = create_multi_agent_system()
deployment_manager = AgentDeploymentManager()
agent_registry = AgentRegistry()
health_checker = HealthChecker(deployment_manager)
observability = ObservabilityManager()

# TODO: Move this to a proper config file
# For now just hardcoded defaults

# Legacy conversation storage for backward compatibility
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
    execution_mode: str = "single"  # single, parallel, sequential, loop

class ClearHistory(BaseModel):
    session_id: str

class AgentConfig(BaseModel):
    agent_id: str
    name: str
    system_prompt: str
    model: str = "llama-3.3-70b-versatile"

class DeploymentRequest(BaseModel):
    agent_id: str
    image: str = "python:3.9-slim"
    replicas: int = 1
    resources: Dict[str, Any] = {"memory": "512Mi", "cpu": "0.5"}
    environment: Dict[str, str] = {}
    ports: List[int] = []

class ScaleRequest(BaseModel):
    agent_id: str
    replicas: int

# Multi-Agent System Endpoints
@app.post("/chat")
async def chat(message: Message):
    """Enhanced chat endpoint with multi-agent support
    
    This got complicated fast with all the execution modes.
    Might need to refactor this later.
    """
    try:
        # Create agent message
        agent_message = AgentMessage(
            content=message.content,
            sender="user",
            recipient="system"
        )
        
        # Process with multi-agent system
        with observability.tracer.trace("chat_request", session_id=message.session_id) as span:
            span.add_tag("execution_mode", message.execution_mode)
            
            result = await mas.process_message(
                message.session_id, 
                agent_message, 
                message.execution_mode
            )
            
            # Handle different result types
            # This is messy but works for now
            if isinstance(result, list):
                # Multiple agents responded
                responses = [r.content for r in result if hasattr(r, 'content')]
                response_text = "\n\n---\n\n".join(responses)
            else:
                # Single agent response
                response_text = result.content if hasattr(result, 'content') else str(result)
            
            # Record metrics
            observer = observability.get_agent_observer("system")
            observer.record_metric("chat.requests", 1, "counter")
            
            # Keep old conversation format so frontend doesn't break
            # Should probably migrate this to the new session system
            if message.session_id not in conversations:
                conversations[message.session_id] = []
            
            conversations[message.session_id].extend([
                {"role": "user", "content": message.content},
                {"role": "assistant", "content": response_text}
            ])
            
            return {"response": response_text}
            
    except Exception as e:
        observability.get_agent_observer("system").log("error", f"Chat error: {str(e)}")
        return {"response": f"Error: {str(e)}"}

@app.post("/clear")
async def clear_history(data: ClearHistory):
    """Clear conversation history"""
    session_id = data.session_id
    if session_id in conversations:
        conversations[session_id] = []
    
    # Clear multi-agent system session
    session = mas.session_service.get_session(session_id)
    if session:
        session["messages"] = []
        memory_bank = mas.session_service.get_memory_bank(session_id)
        if memory_bank:
            memory_bank.episodic_memory = []
    
    return {"status": "cleared"}

# Agent Management Endpoints
@app.post("/agents")
async def create_agent(config: AgentConfig):
    """Create a new agent"""
    try:
        agent = LLMAgent(
            agent_id=config.agent_id,
            name=config.name,
            system_prompt=config.system_prompt,
            model=config.model
        )
        
        mas.register_agent(agent)
        
        # Register in agent registry
        agent_registry.register_agent_definition(
            config.agent_id,
            {
                "name": config.name,
                "system_prompt": config.system_prompt,
                "model": config.model,
                "created_at": "2024-01-01T00:00:00Z"
            }
        )
        
        return {"status": "created", "agent_id": config.agent_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all agents"""
    agents = []
    for agent_id, agent in mas.orchestrator.agents.items():
        metrics = mas.get_agent_metrics(agent_id)
        agents.append({
            "agent_id": agent_id,
            "name": agent.name,
            "state": agent.state.value,
            "metrics": metrics
        })
    return {"agents": agents}

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if agent_id not in mas.orchestrator.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = mas.orchestrator.agents[agent_id]
    metrics = mas.get_agent_metrics(agent_id)
    
    return {
        "agent_id": agent_id,
        "name": agent.name,
        "state": agent.state.value,
        "system_prompt": agent.system_prompt,
        "tools": list(agent.tools.keys()),
        "metrics": metrics
    }

@app.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str):
    """Pause an agent"""
    if agent_id not in mas.orchestrator.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await mas.orchestrator.agents[agent_id].pause()
    return {"status": "paused"}

@app.post("/agents/{agent_id}/resume")
async def resume_agent(agent_id: str):
    """Resume an agent"""
    if agent_id not in mas.orchestrator.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await mas.orchestrator.agents[agent_id].resume()
    return {"status": "resumed"}

# Deployment Endpoints
@app.post("/deploy")
async def deploy_agent(request: DeploymentRequest):
    """Deploy an agent"""
    try:
        config = DeploymentConfig(
            agent_id=request.agent_id,
            image=request.image,
            replicas=request.replicas,
            resources=request.resources,
            environment=request.environment,
            ports=request.ports
        )
        
        deployment_info = await deployment_manager.deploy_agent(config)
        
        return {
            "status": deployment_info.status.value,
            "agent_id": request.agent_id,
            "replicas": len(deployment_info.container_ids),
            "endpoints": deployment_info.endpoints
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/scale")
async def scale_agent(request: ScaleRequest):
    """Scale an agent"""
    try:
        deployment_info = await deployment_manager.scale_agent(
            request.agent_id, 
            request.replicas
        )
        
        return {
            "status": deployment_info.status.value,
            "agent_id": request.agent_id,
            "replicas": len(deployment_info.container_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/deployments")
async def list_deployments():
    """List all deployments"""
    deployments = deployment_manager.list_deployments()
    return {
        "deployments": [
            {
                "agent_id": d.config.agent_id,
                "status": d.status.value,
                "replicas": len(d.container_ids),
                "endpoints": d.endpoints,
                "created_at": d.created_at.isoformat()
            }
            for d in deployments
        ]
    }

@app.get("/deployments/{agent_id}")
async def get_deployment(agent_id: str):
    """Get deployment details"""
    deployment_info = deployment_manager.get_deployment_info(agent_id)
    if not deployment_info:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return {
        "agent_id": agent_id,
        "status": deployment_info.status.value,
        "config": {
            "image": deployment_info.config.image,
            "replicas": deployment_info.config.replicas,
            "resources": deployment_info.config.resources,
            "environment": deployment_info.config.environment,
            "ports": deployment_info.config.ports
        },
        "runtime": {
            "container_ids": deployment_info.container_ids,
            "endpoints": deployment_info.endpoints,
            "created_at": deployment_info.created_at.isoformat(),
            "updated_at": deployment_info.updated_at.isoformat()
        },
        "logs": deployment_info.logs[-50:]  # Last 50 log entries
    }

# Observability Endpoints
@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return observability.metrics.get_all_metrics()

@app.get("/metrics/export")
async def export_metrics(format: str = "json"):
    """Export metrics in various formats"""
    try:
        exported = observability.export_metrics(format)
        if format == "prometheus":
            return {"content": exported, "content_type": "text/plain"}
        else:
            return {"content": exported, "content_type": "application/json"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get trace details"""
    trace_analysis = observability.get_trace_analysis(trace_id)
    if not trace_analysis:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    return trace_analysis

@app.get("/health")
async def health_check():
    """System health check"""
    system_health = observability.get_system_health()
    agent_health = await health_checker.check_all_agents()
    
    return {
        "system": system_health,
        "agents": agent_health,
        "status": mas.get_system_status()
    }

@app.get("/dashboards/{name}")
async def get_dashboard(name: str):
    """Get dashboard data"""
    dashboard_data = observability.get_dashboard_data(name)
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return dashboard_data

# Session Management
@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = mas.session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    memory_bank = mas.session_service.get_memory_bank(session_id)
    
    return {
        "session": session,
        "memory": {
            "long_term_memory": memory_bank.long_term_memory if memory_bank else {},
            "episodic_count": len(memory_bank.episodic_memory) if memory_bank else 0,
            "semantic_memory": memory_bank.semantic_memory if memory_bank else {}
        }
    }

@app.get("/")
async def root():
    return FileResponse(frontend_path / "index.html")

@app.get("/admin")
async def admin():
    """Admin dashboard for multi-agent system management"""
    return FileResponse(frontend_path / "admin.html")

@app.get("/test")
async def test_page():
    """Test page for UI components"""
    return FileResponse(frontend_path / "test.html")
