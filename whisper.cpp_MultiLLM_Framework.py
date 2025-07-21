#!/usr/bin/env python3
"""
Kurt's Simple Multi-LLM Framework
Brings together Claude, ChatGPT, and Local LLM in one clean interface
Built to grow into the spatial constellation system
"""

import json
import os
import requests
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class LLMResponse:
    """Standard response format for all LLMs"""
    model: str
    response: str
    timestamp: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    response_time: Optional[float] = None

class MultiLLMFramework:
    """Simple orchestrator for multiple LLMs"""
    
    def __init__(self, config_file="llm_config.json"):
        self.config = self.load_config(config_file)
        self.conversation_log = []
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load LLM configuration"""
        default_config = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o",
                "max_tokens": 4000
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4000
            },
            "local": {
                "endpoint": "http://localhost:11434/api/generate",
                "model": "llama3:latest",
                "max_tokens": 4000
            },
            "memory": {
                "log_file": "multi_llm_conversations.json",
                "max_history": 100
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
        return default_config
    
    def call_openai(self, prompt: str, context: str = "") -> LLMResponse:
        """Call ChatGPT via OpenAI API"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['openai']['api_key']}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.config['openai']['model'],
                "messages": messages,
                "max_tokens": self.config['openai']['max_tokens']
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return LLMResponse(
                    model="ChatGPT-4o",
                    response=result['choices'][0]['message']['content'],
                    timestamp=datetime.now().isoformat(),
                    tokens_used=result.get('usage', {}).get('total_tokens'),
                    response_time=time.time() - start_time
                )
            else:
                return LLMResponse(
                    model="ChatGPT-4o",
                    response="",
                    timestamp=datetime.now().isoformat(),
                    error=f"API Error: {response.status_code} - {response.text}",
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return LLMResponse(
                model="ChatGPT-4o",
                response="",
                timestamp=datetime.now().isoformat(),
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def call_claude(self, prompt: str, context: str = "") -> LLMResponse:
        """Call Claude via Anthropic API"""
        start_time = time.time()
        
        try:
            headers = {
                "x-api-key": self.config['anthropic']['api_key'],
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            data = {
                "model": self.config['anthropic']['model'],
                "max_tokens": self.config['anthropic']['max_tokens'],
                "messages": [{"role": "user", "content": full_prompt}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return LLMResponse(
                    model="Claude-3.5-Sonnet",
                    response=result['content'][0]['text'],
                    timestamp=datetime.now().isoformat(),
                    tokens_used=result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0),
                    response_time=time.time() - start_time
                )
            else:
                return LLMResponse(
                    model="Claude-3.5-Sonnet",
                    response="",
                    timestamp=datetime.now().isoformat(),
                    error=f"API Error: {response.status_code} - {response.text}",
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return LLMResponse(
                model="Claude-3.5-Sonnet",
                response="",
                timestamp=datetime.now().isoformat(),
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def call_local_llm(self, prompt: str, context: str = "") -> LLMResponse:
        """Call local LLM (Ollama)"""
        start_time = time.time()
        
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            data = {
                "model": self.config['local']['model'],
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": self.config['local']['max_tokens']
                }
            }
            
            response = requests.post(
                self.config['local']['endpoint'],
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return LLMResponse(
                    model=f"Local-{self.config['local']['model']}",
                    response=result['response'],
                    timestamp=datetime.now().isoformat(),
                    response_time=time.time() - start_time
                )
            else:
                return LLMResponse(
                    model=f"Local-{self.config['local']['model']}",
                    response="",
                    timestamp=datetime.now().isoformat(),
                    error=f"Local LLM Error: {response.status_code}",
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return LLMResponse(
                model=f"Local-{self.config['local']['model']}",
                response="",
                timestamp=datetime.now().isoformat(),
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def ask_all(self, prompt: str, context: str = "", models: List[str] = None) -> Dict[str, LLMResponse]:
        """Ask all LLMs the same question"""
        if models is None:
            models = ["chatgpt", "claude", "local"]
        
        responses = {}
        
        print(f"🤖 Asking all LLMs: {prompt[:100]}...")
        
        for model in models:
            print(f"  📡 Calling {model}...")
            
            if model == "chatgpt":
                responses["chatgpt"] = self.call_openai(prompt, context)
            elif model == "claude":
                responses["claude"] = self.call_claude(prompt, context)
            elif model == "local":
                responses["local"] = self.call_local_llm(prompt, context)
            
            # Show status
            if responses[model].error:
                print(f"  ❌ {model} failed: {responses[model].error}")
            else:
                print(f"  ✅ {model} responded ({responses[model].response_time:.1f}s)")
        
        # Log the conversation
        self.log_conversation(prompt, context, responses)
        
        return responses
    
    def ask_single(self, prompt: str, model: str = "local", context: str = "") -> LLMResponse:
        """Ask a single LLM"""
        print(f"🤖 Asking {model}: {prompt[:100]}...")
        
        if model == "chatgpt":
            response = self.call_openai(prompt, context)
        elif model == "claude":
            response = self.call_claude(prompt, context)
        elif model == "local":
            response = self.call_local_llm(prompt, context)
        else:
            raise ValueError(f"Unknown model: {model}")
        
        # Log single conversation
        self.log_conversation(prompt, context, {model: response})
        
        return response
    
    def log_conversation(self, prompt: str, context: str, responses: Dict[str, LLMResponse]):
        """Log conversation to file"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "context": context,
            "responses": {k: asdict(v) for k, v in responses.items()}
        }
        
        self.conversation_log.append(conversation)
        
        # Save to file
        log_file = self.config['memory']['log_file']
        try:
            with open(log_file, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save log: {e}")
    
    def compare_responses(self, responses: Dict[str, LLMResponse]) -> str:
        """Generate a simple comparison of responses"""
        comparison = "\n" + "="*60 + "\n"
        comparison += "🤖 MULTI-LLM RESPONSE COMPARISON\n"
        comparison += "="*60 + "\n"
        
        for model, response in responses.items():
            comparison += f"\n🔹 {response.model}:\n"
            if response.error:
                comparison += f"❌ Error: {response.error}\n"
            else:
                comparison += f"⏱️  Response time: {response.response_time:.1f}s\n"
                if response.tokens_used:
                    comparison += f"🎯 Tokens: {response.tokens_used}\n"
                comparison += f"💬 Response:\n{response.response}\n"
            comparison += "-" * 40 + "\n"
        
        return comparison
    
    def interactive_mode(self):
        """Interactive CLI mode"""
        print("🧠 Kurt's Multi-LLM Framework")
        print("Commands: 'all <prompt>', 'local <prompt>', 'claude <prompt>', 'chatgpt <prompt>', 'quit'")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💭 > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.startswith('all '):
                    prompt = user_input[4:]
                    responses = self.ask_all(prompt)
                    print(self.compare_responses(responses))
                    
                elif user_input.startswith('local '):
                    prompt = user_input[6:]
                    response = self.ask_single(prompt, "local")
                    if response.error:
                        print(f"❌ Error: {response.error}")
                    else:
                        print(f"💬 {response.model}: {response.response}")
                        
                elif user_input.startswith('claude '):
                    prompt = user_input[7:]
                    response = self.ask_single(prompt, "claude")
                    if response.error:
                        print(f"❌ Error: {response.error}")
                    else:
                        print(f"💬 {response.model}: {response.response}")
                        
                elif user_input.startswith('chatgpt '):
                    prompt = user_input[8:]
                    response = self.ask_single(prompt, "chatgpt")
                    if response.error:
                        print(f"❌ Error: {response.error}")
                    else:
                        print(f"💬 {response.model}: {response.response}")
                        
                else:
                    print("Unknown command. Try 'all <prompt>' or '<model> <prompt>'")
                    
            except KeyboardInterrupt:
                break
        
        print("\n👋 Goodbye!")

def main():
    """CLI entry point"""
    framework = MultiLLMFramework()
    
    if len(os.sys.argv) > 1:
        # Command line mode
        command = os.sys.argv[1]
        prompt = " ".join(os.sys.argv[2:])
        
        if command == "all":
            responses = framework.ask_all(prompt)
            print(framework.compare_responses(responses))
        elif command in ["local", "claude", "chatgpt"]:
            response = framework.ask_single(prompt, command)
            if response.error:
                print(f"❌ Error: {response.error}")
            else:
                print(response.response)
        else:
            print("Usage: python MultiLLM_Framework.py [all|local|claude|chatgpt] '<prompt>'")
    else:
        # Interactive mode
        framework.interactive_mode()

if __name__ == "__main__":
    main()
