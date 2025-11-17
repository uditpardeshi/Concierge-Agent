"""
Agent Deployment System
Handles deployment, scaling, and management of agents
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import docker
import yaml

logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    SCALING = "scaling"

@dataclass
class DeploymentConfig:
    agent_id: str
    image: str = "python:3.9-slim"
    replicas: int = 1
    resources: Dict[str, Any] = None
    environment: Dict[str, str] = None
    ports: List[int] = None
    volumes: List[str] = None
    
    def __post_init__(self):
        if self.resources is None:
            self.resources = {"memory": "512Mi", "cpu": "0.5"}
        if self.environment is None:
            self.environment = {}
        if self.ports is None:
            self.ports = []
        if self.volumes is None:
            self.volumes = []

@dataclass
class DeploymentInfo:
    config: DeploymentConfig
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
    container_ids: List[str] = None
    endpoints: List[str] = None
    logs: List[str] = None
    
    def __post_init__(self):
        if self.container_ids is None:
            self.container_ids = []
        if self.endpoints is None:
            self.endpoints = []
        if self.logs is None:
            self.logs = []

class AgentDeploymentManager:
    def __init__(self):
        self.deployments: Dict[str, DeploymentInfo] = {}
        self.docker_client = None
        self._init_docker()
    
    def _init_docker(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
    
    async def deploy_agent(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy an agent with the given configuration"""
        deployment_info = DeploymentInfo(
            config=config,
            status=DeploymentStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.deployments[config.agent_id] = deployment_info
        
        try:
            deployment_info.status = DeploymentStatus.DEPLOYING
            deployment_info.updated_at = datetime.now()
            
            if self.docker_client:
                await self._deploy_with_docker(deployment_info)
            else:
                await self._deploy_local(deployment_info)
            
            deployment_info.status = DeploymentStatus.RUNNING
            deployment_info.updated_at = datetime.now()
            
            logger.info(f"Agent {config.agent_id} deployed successfully")
            
        except Exception as e:
            deployment_info.status = DeploymentStatus.FAILED
            deployment_info.logs.append(f"Deployment failed: {str(e)}")
            logger.error(f"Failed to deploy agent {config.agent_id}: {e}")
        
        return deployment_info
    
    async def _deploy_with_docker(self, deployment_info: DeploymentInfo):
        """Deploy agent using Docker"""
        config = deployment_info.config
        
        # Create Dockerfile content
        dockerfile_content = f"""
FROM {config.image}

WORKDIR /app

# Copy agent code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
{chr(10).join([f'ENV {k}={v}' for k, v in config.environment.items()])}

# Expose ports
{chr(10).join([f'EXPOSE {port}' for port in config.ports])}

# Run agent
CMD ["python", "agent_runner.py"]
"""
        
        # Build and run containers
        for i in range(config.replicas):
            container_name = f"{config.agent_id}_replica_{i}"
            
            try:
                # In a real implementation, you would build the image and run container
                # For now, we'll simulate this
                container_id = f"container_{config.agent_id}_{i}"
                deployment_info.container_ids.append(container_id)
                deployment_info.endpoints.append(f"http://localhost:{8000 + i}")
                
                logger.info(f"Started container {container_name}")
                
            except Exception as e:
                raise Exception(f"Failed to start container {container_name}: {e}")
    
    async def _deploy_local(self, deployment_info: DeploymentInfo):
        """Deploy agent locally (fallback)"""
        config = deployment_info.config
        
        # Simulate local deployment
        for i in range(config.replicas):
            process_id = f"process_{config.agent_id}_{i}"
            deployment_info.container_ids.append(process_id)
            deployment_info.endpoints.append(f"http://localhost:{9000 + i}")
        
        logger.info(f"Agent {config.agent_id} deployed locally")
    
    async def scale_agent(self, agent_id: str, replicas: int) -> DeploymentInfo:
        """Scale agent to specified number of replicas"""
        if agent_id not in self.deployments:
            raise ValueError(f"Agent {agent_id} not found")
        
        deployment_info = self.deployments[agent_id]
        deployment_info.status = DeploymentStatus.SCALING
        deployment_info.updated_at = datetime.now()
        
        try:
            current_replicas = len(deployment_info.container_ids)
            
            if replicas > current_replicas:
                # Scale up
                for i in range(current_replicas, replicas):
                    container_id = f"container_{agent_id}_{i}"
                    deployment_info.container_ids.append(container_id)
                    deployment_info.endpoints.append(f"http://localhost:{8000 + i}")
            
            elif replicas < current_replicas:
                # Scale down
                containers_to_remove = deployment_info.container_ids[replicas:]
                endpoints_to_remove = deployment_info.endpoints[replicas:]
                
                deployment_info.container_ids = deployment_info.container_ids[:replicas]
                deployment_info.endpoints = deployment_info.endpoints[:replicas]
                
                # In real implementation, stop and remove containers
                for container_id in containers_to_remove:
                    logger.info(f"Stopped container {container_id}")
            
            deployment_info.config.replicas = replicas
            deployment_info.status = DeploymentStatus.RUNNING
            deployment_info.updated_at = datetime.now()
            
            logger.info(f"Scaled agent {agent_id} to {replicas} replicas")
            
        except Exception as e:
            deployment_info.status = DeploymentStatus.FAILED
            deployment_info.logs.append(f"Scaling failed: {str(e)}")
            logger.error(f"Failed to scale agent {agent_id}: {e}")
        
        return deployment_info
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a deployed agent"""
        if agent_id not in self.deployments:
            return False
        
        deployment_info = self.deployments[agent_id]
        
        try:
            # Stop all containers/processes
            for container_id in deployment_info.container_ids:
                # In real implementation, stop container
                logger.info(f"Stopped container {container_id}")
            
            deployment_info.status = DeploymentStatus.STOPPED
            deployment_info.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            deployment_info.logs.append(f"Stop failed: {str(e)}")
            logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart a deployed agent"""
        if agent_id not in self.deployments:
            return False
        
        await self.stop_agent(agent_id)
        deployment_info = await self.deploy_agent(self.deployments[agent_id].config)
        
        return deployment_info.status == DeploymentStatus.RUNNING
    
    def get_deployment_info(self, agent_id: str) -> Optional[DeploymentInfo]:
        """Get deployment information for an agent"""
        return self.deployments.get(agent_id)
    
    def list_deployments(self) -> List[DeploymentInfo]:
        """List all deployments"""
        return list(self.deployments.values())
    
    async def get_agent_logs(self, agent_id: str, lines: int = 100) -> List[str]:
        """Get logs for a deployed agent"""
        if agent_id not in self.deployments:
            return []
        
        deployment_info = self.deployments[agent_id]
        
        # In real implementation, fetch logs from containers
        # For now, return stored logs
        return deployment_info.logs[-lines:]
    
    def get_deployment_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get deployment metrics"""
        if agent_id not in self.deployments:
            return {}
        
        deployment_info = self.deployments[agent_id]
        
        return {
            "agent_id": agent_id,
            "status": deployment_info.status.value,
            "replicas": len(deployment_info.container_ids),
            "endpoints": deployment_info.endpoints,
            "uptime": (datetime.now() - deployment_info.created_at).total_seconds(),
            "last_updated": deployment_info.updated_at.isoformat()
        }
    
    def export_deployment_config(self, agent_id: str) -> Optional[str]:
        """Export deployment configuration as YAML"""
        if agent_id not in self.deployments:
            return None
        
        config = self.deployments[agent_id].config
        
        deployment_yaml = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"agent-{agent_id}",
                "labels": {
                    "app": f"agent-{agent_id}"
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": f"agent-{agent_id}"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": f"agent-{agent_id}"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": f"agent-{agent_id}",
                            "image": config.image,
                            "ports": [{"containerPort": port} for port in config.ports],
                            "env": [{"name": k, "value": v} for k, v in config.environment.items()],
                            "resources": {
                                "requests": config.resources,
                                "limits": config.resources
                            }
                        }]
                    }
                }
            }
        }
        
        return yaml.dump(deployment_yaml, default_flow_style=False)

class AgentRegistry:
    """Registry for managing agent definitions and versions"""
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[str]] = {}
    
    def register_agent_definition(self, agent_id: str, definition: Dict[str, Any], version: str = "1.0.0"):
        """Register an agent definition"""
        if agent_id not in self.agents:
            self.agents[agent_id] = {}
            self.versions[agent_id] = []
        
        self.agents[agent_id][version] = definition
        if version not in self.versions[agent_id]:
            self.versions[agent_id].append(version)
        
        logger.info(f"Registered agent {agent_id} version {version}")
    
    def get_agent_definition(self, agent_id: str, version: str = None) -> Optional[Dict[str, Any]]:
        """Get agent definition by ID and version"""
        if agent_id not in self.agents:
            return None
        
        if version is None:
            # Get latest version
            if self.versions[agent_id]:
                version = self.versions[agent_id][-1]
            else:
                return None
        
        return self.agents[agent_id].get(version)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        result = []
        for agent_id, versions in self.versions.items():
            result.append({
                "agent_id": agent_id,
                "versions": versions,
                "latest_version": versions[-1] if versions else None
            })
        return result

# Health Check System
class HealthChecker:
    def __init__(self, deployment_manager: AgentDeploymentManager):
        self.deployment_manager = deployment_manager
        self.health_checks: Dict[str, Dict[str, Any]] = {}
    
    async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Check health of a deployed agent"""
        deployment_info = self.deployment_manager.get_deployment_info(agent_id)
        
        if not deployment_info:
            return {"status": "not_found", "healthy": False}
        
        health_status = {
            "agent_id": agent_id,
            "status": deployment_info.status.value,
            "healthy": deployment_info.status == DeploymentStatus.RUNNING,
            "replicas": len(deployment_info.container_ids),
            "endpoints": deployment_info.endpoints,
            "last_check": datetime.now().isoformat()
        }
        
        # Perform endpoint health checks
        healthy_endpoints = 0
        for endpoint in deployment_info.endpoints:
            try:
                # In real implementation, make HTTP request to health endpoint
                # For now, simulate health check
                healthy_endpoints += 1
            except Exception as e:
                logger.warning(f"Health check failed for {endpoint}: {e}")
        
        health_status["healthy_endpoints"] = healthy_endpoints
        health_status["endpoint_health_ratio"] = healthy_endpoints / max(len(deployment_info.endpoints), 1)
        
        self.health_checks[agent_id] = health_status
        return health_status
    
    async def check_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all deployed agents"""
        results = {}
        for agent_id in self.deployment_manager.deployments.keys():
            results[agent_id] = await self.check_agent_health(agent_id)
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        total_agents = len(self.deployment_manager.deployments)
        healthy_agents = sum(1 for info in self.health_checks.values() if info.get("healthy", False))
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "health_ratio": healthy_agents / max(total_agents, 1),
            "system_status": "healthy" if healthy_agents == total_agents else "degraded",
            "last_check": datetime.now().isoformat()
        }