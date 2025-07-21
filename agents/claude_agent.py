"""
Claude Agent Implementation

Handles interaction with Anthropic's Claude API for the spatial constellation system.
"""

import anthropic
from typing import Dict, Any, List
from core.agents import Agent, AgentRole
import logging

logger = logging.getLogger(__name__)

class ClaudeAgent(Agent):
    """Claude API agent implementation"""
    
    def __init__(self, name: str = "claude", api_key: str = None, model: str = "claude-3-sonnet-20240229"):
        capabilities = [
            "text_generation",
            "code_analysis",
            "conversation", 
            "reasoning",
            "file_reading",  # Read-only access
            "long_context"   # Claude's strength
        ]
        super().__init__(name, AgentRole.CLAUDE, capabilities)
        
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task using Claude API"""
        
        if not self.client:
            raise RuntimeError("Claude API client not configured")
        
        task_type = task.get("type")
        content = task.get("content", "")
        
        try:
            if task_type == "chat":
                return await self._handle_chat(content, task.get("context", {}))
            elif task_type == "analyze_code":
                return await self._handle_code_analysis(content, task.get("context", {}))
            elif task_type == "generate_text":
                return await self._handle_text_generation(content, task.get("context", {}))
            elif task_type == "long_analysis":
                return await self._handle_long_analysis(content, task.get("context", {}))
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Claude task error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _handle_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat conversation"""
        
        messages = [{"role": "user", "content": message}]
        
        # Add conversation history if provided
        if "history" in context:
            for hist_msg in context["history"][-10:]:  # Last 10 messages for context
                if hist_msg.get("role") in ["user", "assistant"]:
                    messages.insert(-1, hist_msg)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=context.get("max_tokens", 2000),
            temperature=context.get("temperature", 0.7),
            system=context.get("system_prompt", "You are Claude, a helpful AI assistant."),
            messages=messages
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "model": self.model,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "agent": self.name
        }
    
    async def _handle_code_analysis(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code with Claude's analytical capabilities"""
        
        system_prompt = """You are an expert code analyst. Provide comprehensive analysis including:
1. Code structure and organization
2. Potential bugs and security issues  
3. Performance optimization opportunities
4. Best practice recommendations
5. Documentation quality
Be thorough and specific in your analysis."""
        
        message = f"Please analyze this code:\n\n```\n{code}\n```"
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        )
        
        return {
            "success": True,
            "analysis": response.content[0].text,
            "model": self.model,
            "agent": self.name
        }
    
    async def _handle_text_generation(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text using Claude"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=context.get("max_tokens", 1000),
            temperature=context.get("temperature", 0.7),
            system=context.get("system_prompt", "You are a helpful writing assistant."),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "success": True,
            "generated_text": response.content[0].text,
            "model": self.model,
            "agent": self.name
        }
    
    async def _handle_long_analysis(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle long-form analysis tasks (Claude's specialty)"""
        
        system_prompt = context.get("system_prompt", 
            "You are an expert analyst. Provide detailed, structured analysis of the provided content.")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=context.get("max_tokens", 4000),
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": content}]
        )
        
        return {
            "success": True,
            "analysis": response.content[0].text,
            "model": self.model,
            "agent": self.name
        }