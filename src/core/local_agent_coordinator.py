#!/usr/bin/env python3
"""
Local Agent Coordinator - Cost-Effective Multi-AI Collaboration System
Handles most tasks locally, delegates strategically to API models
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Local model can handle
    MODERATE = "moderate"  # Local with validation
    COMPLEX = "complex"    # Requires API model
    CRITICAL = "critical"  # Requires human approval

class AgentType(Enum):
    LOCAL_PRIMARY = "local_primary"      # Main local model (ollama/llama)
    LOCAL_VALIDATOR = "local_validator"  # Secondary local model for validation
    API_SPECIALIST = "api_specialist"    # GPT-4/Claude for complex tasks
    HUMAN_OVERSEER = "human_overseer"    # Human approval for critical tasks

@dataclass
class Task:
    id: str
    description: str
    complexity: TaskComplexity
    assigned_agent: AgentType
    context: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    validation_required: bool = False

class LocalAgentCoordinator:
    """
    Coordinates multiple AI agents with cost optimization
    Primary workflow: Local -> Validation -> API (only if needed)
    """
    
    def __init__(self, config_path: str = "config/agents.json"):
        self.config_path = config_path
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.session_id = f"session_{int(time.time())}"
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'data/coordinator_{self.session_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load agent configurations
        self.agents_config = self._load_agent_config()
        
        self.logger.info(f"Local Agent Coordinator initialized - Session: {self.session_id}")
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent configuration with defaults"""
        default_config = {
            "local_models": {
                "primary": {
                    "name": "llama3",
                    "endpoint": "http://localhost:11434/api/generate",
                    "model": "llama3:latest",
                    "capabilities": ["general", "coding", "analysis"]
                },
                "validator": {
                    "name": "mistral",
                    "endpoint": "http://localhost:11434/api/generate", 
                    "model": "mistral:latest",
                    "capabilities": ["validation", "review", "quality_check"]
                }
            },
            "api_models": {
                "gpt4": {
                    "name": "gpt-4",
                    "capabilities": ["complex_reasoning", "specialized_tasks"],
                    "cost_per_token": 0.00003
                },
                "claude": {
                    "name": "claude-3",
                    "capabilities": ["analysis", "coding", "reasoning"],
                    "cost_per_token": 0.000015
                }
            },
            "task_routing": {
                "simple": "local_primary",
                "moderate": "local_primary_with_validation",
                "complex": "api_specialist",
                "critical": "api_specialist_with_human"
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            self.logger.info("No config file found, using defaults")
            return default_config
    
    def analyze_task_complexity(self, description: str, context: Dict[str, Any] = None) -> TaskComplexity:
        """
        Analyze task complexity to determine optimal agent assignment
        Uses local model for analysis to avoid API costs
        """
        # Simple heuristics for now - can be enhanced with local model analysis
        complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "list", "show", "display", "get", "retrieve", "status",
                "check", "verify", "validate", "simple"
            ],
            TaskComplexity.MODERATE: [
                "analyze", "compare", "summarize", "organize", "categorize",
                "implement", "create", "build", "modify"
            ],
            TaskComplexity.COMPLEX: [
                "design", "architect", "optimize", "complex", "advanced",
                "integrate", "coordinate", "orchestrate", "strategic"
            ],
            TaskComplexity.CRITICAL: [
                "delete", "remove", "destroy", "critical", "production",
                "deploy", "publish", "irreversible"
            ]
        }
        
        description_lower = description.lower()
        
        # Check for critical indicators first
        for indicator in complexity_indicators[TaskComplexity.CRITICAL]:
            if indicator in description_lower:
                return TaskComplexity.CRITICAL
        
        # Check complexity levels
        for complexity, indicators in complexity_indicators.items():
            if complexity == TaskComplexity.CRITICAL:
                continue
            for indicator in indicators:
                if indicator in description_lower:
                    return complexity
        
        # Default to moderate for unknown tasks
        return TaskComplexity.MODERATE
    
    def create_task(self, description: str, context: Dict[str, Any] = None) -> str:
        """Create and queue a new task"""
        task_id = f"task_{int(time.time() * 1000)}"
        complexity = self.analyze_task_complexity(description, context)
        
        # Determine agent assignment based on complexity
        agent_assignment = {
            TaskComplexity.SIMPLE: AgentType.LOCAL_PRIMARY,
            TaskComplexity.MODERATE: AgentType.LOCAL_PRIMARY,
            TaskComplexity.COMPLEX: AgentType.API_SPECIALIST,
            TaskComplexity.CRITICAL: AgentType.HUMAN_OVERSEER
        }
        
        task = Task(
            id=task_id,
            description=description,
            complexity=complexity,
            assigned_agent=agent_assignment[complexity],
            context=context or {},
            created_at=datetime.now(),
            validation_required=(complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX])
        )
        
        self.active_tasks[task_id] = task
        self.logger.info(f"Task created: {task_id} - {complexity.value} - {description[:50]}...")
        
        return task_id
    
    def execute_local_task(self, task: Task) -> Dict[str, Any]:
        """Execute task using local model (Ollama)"""
        try:
            # Prepare prompt for local model
            prompt = self._prepare_local_prompt(task)
            
            # Call local model via Ollama API
            response = self._call_ollama(prompt, task.context.get('model', 'llama3:latest'))
            
            if response and 'response' in response:
                return {
                    'success': True,
                    'result': response['response'],
                    'agent': 'local_primary',
                    'cost': 0.0,
                    'tokens_used': response.get('eval_count', 0)
                }
            else:
                return {
                    'success': False,
                    'error': 'No response from local model',
                    'agent': 'local_primary'
                }
                
        except Exception as e:
            self.logger.error(f"Local task execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'local_primary'
            }
    
    def _prepare_local_prompt(self, task: Task) -> str:
        """Prepare optimized prompt for local model"""
        system_context = """You are a local AI assistant working as part of a multi-agent system. 
Your role is to handle tasks efficiently and indicate when you need help from more capable models.

Guidelines:
- Be concise and direct
- If task is beyond your capabilities, say "ESCALATE: [reason]"
- Focus on practical, actionable responses
- Maintain context awareness"""
        
        user_prompt = f"""Task: {task.description}

Context: {json.dumps(task.context, indent=2) if task.context else 'None'}

Please complete this task or indicate if escalation is needed."""
        
        return f"{system_context}\n\nUser: {user_prompt}\n\nAssistant:"
    
    def _call_ollama(self, prompt: str, model: str = "llama3:latest") -> Dict[str, Any]:
        """Call Ollama API for local model inference"""
        try:
            import requests
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            return None
    
    def validate_result(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate result using secondary local model"""
        if not task.validation_required:
            return {'validated': True, 'validator': 'none'}
        
        try:
            validation_prompt = f"""Validate this task completion:

Original Task: {task.description}
Result: {result.get('result', 'No result')}

Check for:
1. Task completion accuracy
2. Quality of response
3. Any obvious errors or omissions

Respond with: VALID or INVALID: [reason]"""
            
            validation_response = self._call_ollama(validation_prompt, "mistral:latest")
            
            if validation_response and 'response' in validation_response:
                validation_text = validation_response['response'].strip()
                is_valid = validation_text.upper().startswith('VALID')
                
                return {
                    'validated': is_valid,
                    'validator': 'local_validator',
                    'validation_response': validation_text,
                    'validation_cost': 0.0
                }
            else:
                return {
                    'validated': False,
                    'validator': 'local_validator',
                    'error': 'Validation failed - no response'
                }
                
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                'validated': False,
                'validator': 'local_validator', 
                'error': str(e)
            }
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task using the appropriate agent"""
        if task_id not in self.active_tasks:
            return {'success': False, 'error': 'Task not found'}
        
        task = self.active_tasks[task_id]
        self.logger.info(f"Executing task {task_id}: {task.description[:50]}...")
        
        # Execute based on assigned agent
        if task.assigned_agent == AgentType.LOCAL_PRIMARY:
            result = self.execute_local_task(task)
            
            # Validate if required
            if task.validation_required and result.get('success'):
                validation = self.validate_result(task, result)
                result['validation'] = validation
                
                # If validation fails, consider escalation
                if not validation.get('validated', False):
                    self.logger.warning(f"Task {task_id} failed validation, considering escalation")
                    # Could implement automatic escalation here
            
        elif task.assigned_agent == AgentType.API_SPECIALIST:
            result = {'success': False, 'error': 'API specialist not implemented yet'}
            
        elif task.assigned_agent == AgentType.HUMAN_OVERSEER:
            result = {'success': False, 'error': 'Human approval required', 'requires_human': True}
            
        else:
            result = {'success': False, 'error': 'Unknown agent type'}
        
        # Update task
        task.result = result
        task.completed_at = datetime.now()
        
        # Move to completed tasks
        self.completed_tasks.append(task)
        del self.active_tasks[task_id]
        
        self.logger.info(f"Task {task_id} completed: {result.get('success', False)}")
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        return {
            'session_id': self.session_id,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'agents_available': self._check_agent_availability(),
            'total_cost': sum(task.result.get('cost', 0) for task in self.completed_tasks if task.result),
            'local_tasks_completed': len([t for t in self.completed_tasks if t.result and t.result.get('agent') == 'local_primary'])
        }
    
    def _check_agent_availability(self) -> Dict[str, bool]:
        """Check which agents are available"""
        availability = {}
        
        # Check Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            availability['ollama'] = response.status_code == 200
        except:
            availability['ollama'] = False
        
        # Check API models (placeholder)
        availability['gpt4'] = True  # Assume available if API key exists
        availability['claude'] = True
        
        return availability

if __name__ == "__main__":
    # Simple test
    coordinator = LocalAgentCoordinator()
    
    # Test task creation and execution
    task_id = coordinator.create_task("List the current directory contents")
    result = coordinator.execute_task(task_id)
    
    print(f"Task result: {result}")
    print(f"Status: {coordinator.get_status()}")

