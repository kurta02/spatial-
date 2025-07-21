"""
Agent Orchestration System

This module provides coordination and management for multiple AI agents
in the spatial constellation system.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Define different agent roles in the system"""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    LOCAL_LLM = "local_llm"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"

class AgentStatus(Enum):
    """Agent operational status"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class Agent:
    """Base agent class"""
    
    def __init__(self, name: str, role: AgentRole, capabilities: List[str] = None):
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.status = AgentStatus.AVAILABLE
        self.last_activity = datetime.now()
        self.task_count = 0
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task assigned to this agent"""
        self.status = AgentStatus.BUSY
        self.task_count += 1
        self.last_activity = datetime.now()
        
        try:
            # Base implementation - override in subclasses
            result = await self._process_task(task)
            self.status = AgentStatus.AVAILABLE
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.name} error: {e}")
            raise
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method in agent implementations"""
        raise NotImplementedError("Agent must implement _process_task method")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "task_count": self.task_count,
            "last_activity": self.last_activity.isoformat()
        }

class AgentOrchestrator:
    """Orchestrates multiple agents for collaborative tasks"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = asyncio.Queue()
        self.active_tasks: Dict[str, Dict] = {}
        
    def register_agent(self, agent: Agent):
        """Register an agent with the orchestrator"""
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.role.value})")
    
    def unregister_agent(self, agent_name: str):
        """Remove an agent from the orchestrator"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
    
    def get_available_agents(self, role: Optional[AgentRole] = None) -> List[Agent]:
        """Get list of available agents, optionally filtered by role"""
        available = [
            agent for agent in self.agents.values() 
            if agent.status == AgentStatus.AVAILABLE
        ]
        
        if role:
            available = [agent for agent in available if agent.role == role]
            
        return available
    
    async def assign_task(self, task: Dict[str, Any], preferred_agent: Optional[str] = None) -> Dict[str, Any]:
        """Assign a task to an appropriate agent"""
        
        # Try preferred agent first
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
            if agent.status == AgentStatus.AVAILABLE:
                return await agent.execute_task(task)
        
        # Find suitable agent based on task requirements
        required_role = task.get("required_role")
        if required_role:
            try:
                role_enum = AgentRole(required_role)
                available_agents = self.get_available_agents(role_enum)
            except ValueError:
                available_agents = self.get_available_agents()
        else:
            available_agents = self.get_available_agents()
        
        if not available_agents:
            raise RuntimeError("No available agents for task")
        
        # Select agent (simple round-robin for now)
        selected_agent = min(available_agents, key=lambda a: a.task_count)
        
        task_id = f"task_{datetime.now().timestamp()}"
        self.active_tasks[task_id] = {
            "agent": selected_agent.name,
            "task": task,
            "started": datetime.now()
        }
        
        try:
            result = await selected_agent.execute_task(task)
            result["task_id"] = task_id
            result["agent"] = selected_agent.name
            
            # Clean up completed task
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
            return result
            
        except Exception as e:
            # Clean up failed task
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            raise
    
    async def broadcast_task(self, task: Dict[str, Any], roles: Optional[List[AgentRole]] = None) -> Dict[str, Dict[str, Any]]:
        """Send the same task to multiple agents and collect results"""
        if roles:
            agents = []
            for role in roles:
                agents.extend(self.get_available_agents(role))
        else:
            agents = self.get_available_agents()
        
        if not agents:
            return {}
        
        # Execute tasks concurrently
        tasks = [agent.execute_task(task) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        broadcast_results = {}
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                broadcast_results[agent.name] = {
                    "error": str(result),
                    "status": "failed"
                }
            else:
                broadcast_results[agent.name] = result
        
        return broadcast_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = 0
        
        agent_details = {}
        for agent in self.agents.values():
            status_counts[agent.status.value] += 1
            agent_details[agent.name] = agent.get_status()
        
        return {
            "total_agents": len(self.agents),
            "status_counts": status_counts,
            "active_tasks": len(self.active_tasks),
            "agents": agent_details,
            "task_queue_size": self.task_queue.qsize()
        }

# Global orchestrator instance
global_orchestrator = AgentOrchestrator()

def get_orchestrator() -> AgentOrchestrator:
    """Get the global agent orchestrator instance"""
    return global_orchestrator