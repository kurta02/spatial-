"""
Local LLM Agent Implementation

Handles interaction with local LLM (Ollama) for the spatial constellation system.
"""

import requests
import json
from typing import Dict, Any, List
from core.agents import Agent, AgentRole
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class LocalLLMAgent(Agent):
    """Local LLM agent implementation using Ollama"""
    
    def __init__(self, name: str = "local_llm", host: str = "http://localhost:11434", model: str = "llama3.1"):
        capabilities = [
            "text_generation",
            "code_analysis",
            "conversation",
            "file_operations",  # Full read/write access
            "local_execution",
            "privacy_focused"   # Local processing
        ]
        super().__init__(name, AgentRole.LOCAL_LLM, capabilities)
        
        self.host = host
        self.model = model
        self.ollama_url = f"{host}/api"
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task using local Ollama LLM"""
        
        task_type = task.get("type")
        content = task.get("content", "")
        
        try:
            if task_type == "chat":
                return await self._handle_chat(content, task.get("context", {}))
            elif task_type == "analyze_code":
                return await self._handle_code_analysis(content, task.get("context", {}))
            elif task_type == "generate_text":
                return await self._handle_text_generation(content, task.get("context", {}))
            elif task_type == "file_operation":
                return await self._handle_file_operation(task)
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Local LLM task error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _call_ollama(self, prompt: str, system_prompt: str = None, stream: bool = False) -> str:
        """Make async call to Ollama API"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.ollama_url}/generate", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    raise RuntimeError(f"Ollama API error: {response.status}")
    
    async def _handle_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat conversation with local LLM"""
        
        # Build conversation context
        conversation_context = ""
        if "history" in context:
            for hist_msg in context["history"][-5:]:  # Last 5 for context
                role = hist_msg.get("role", "user")
                content = hist_msg.get("content", "")
                conversation_context += f"{role}: {content}\n"
        
        full_prompt = f"{conversation_context}user: {message}\nassistant:"
        
        system_prompt = context.get("system_prompt", 
            "You are a helpful AI assistant running locally. Be concise and helpful.")
        
        response = await self._call_ollama(full_prompt, system_prompt)
        
        return {
            "success": True,
            "response": response,
            "model": self.model,
            "agent": self.name,
            "local": True
        }
    
    async def _handle_code_analysis(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code using local LLM"""
        
        system_prompt = """You are a code analysis expert. Analyze the provided code for:
1. Functionality and logic
2. Potential bugs or issues
3. Code quality and structure
4. Suggestions for improvement
Provide clear, actionable feedback."""
        
        prompt = f"Analyze this code:\n\n```\n{code}\n```"
        
        response = await self._call_ollama(prompt, system_prompt)
        
        return {
            "success": True,
            "analysis": response,
            "model": self.model,
            "agent": self.name,
            "local": True
        }
    
    async def _handle_text_generation(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text using local LLM"""
        
        system_prompt = context.get("system_prompt", 
            "You are a helpful writing assistant. Generate high-quality, relevant content.")
        
        response = await self._call_ollama(prompt, system_prompt)
        
        return {
            "success": True,
            "generated_text": response,
            "model": self.model,
            "agent": self.name,
            "local": True
        }
    
    async def _handle_file_operation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operations (local LLM has write access)"""
        
        operation = task.get("operation")
        file_path = task.get("file_path")
        content = task.get("content", "")
        
        try:
            if operation == "read":
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                return {
                    "success": True,
                    "content": file_content,
                    "operation": "read",
                    "agent": self.name
                }
            
            elif operation == "write":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "message": f"File written successfully: {file_path}",
                    "operation": "write",
                    "agent": self.name
                }
            
            elif operation == "append":
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return {
                    "success": True,
                    "message": f"Content appended to: {file_path}",
                    "operation": "append", 
                    "agent": self.name
                }
            
            else:
                raise ValueError(f"Unsupported file operation: {operation}")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "agent": self.name
            }
    
    async def check_availability(self) -> bool:
        """Check if local LLM is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False