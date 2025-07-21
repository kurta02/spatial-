"""
ChatGPT Agent Implementation

Handles interaction with OpenAI's ChatGPT API for the spatial constellation system.
"""

import openai
from typing import Dict, Any, List
from core.agents import Agent, AgentRole
import logging

logger = logging.getLogger(__name__)

class ChatGPTAgent(Agent):
    """ChatGPT API agent implementation"""
    
    def __init__(self, name: str = "chatgpt", api_key: str = None, model: str = "gpt-4"):
        capabilities = [
            "text_generation",
            "code_analysis", 
            "conversation",
            "reasoning",
            "file_reading"  # Read-only access
        ]
        super().__init__(name, AgentRole.CHATGPT, capabilities)
        
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task using ChatGPT API"""
        
        if not self.client:
            raise RuntimeError("ChatGPT API client not configured")
        
        task_type = task.get("type")
        content = task.get("content", "")
        
        try:
            if task_type == "chat":
                return await self._handle_chat(content, task.get("context", {}))
            elif task_type == "analyze_code":
                return await self._handle_code_analysis(content, task.get("context", {}))
            elif task_type == "generate_text":
                return await self._handle_text_generation(content, task.get("context", {}))
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
                
        except Exception as e:
            logger.error(f"ChatGPT task error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _handle_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat conversation"""
        
        messages = [{"role": "user", "content": message}]
        
        # Add context if provided
        if "system_prompt" in context:
            messages.insert(0, {"role": "system", "content": context["system_prompt"]})
        
        if "history" in context:
            for hist_msg in context["history"][-5:]:  # Last 5 messages for context
                messages.insert(-1, hist_msg)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=context.get("max_tokens", 2000),
            temperature=context.get("temperature", 0.7)
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": self.model,
            "tokens_used": response.usage.total_tokens,
            "agent": self.name
        }
    
    async def _handle_code_analysis(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code and provide insights"""
        
        system_prompt = """You are a code analysis expert. Analyze the provided code and return:
1. Code quality assessment
2. Potential issues or bugs
3. Optimization suggestions
4. Security considerations
Provide structured, actionable feedback."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this code:\n\n```\n{code}\n```"}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.3
        )
        
        return {
            "success": True,
            "analysis": response.choices[0].message.content,
            "model": self.model,
            "agent": self.name
        }
    
    async def _handle_text_generation(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text based on prompt"""
        
        messages = [{"role": "user", "content": prompt}]
        
        if "system_prompt" in context:
            messages.insert(0, {"role": "system", "content": context["system_prompt"]})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=context.get("max_tokens", 1000),
            temperature=context.get("temperature", 0.7)
        )
        
        return {
            "success": True,
            "generated_text": response.choices[0].message.content,
            "model": self.model,
            "agent": self.name
        }