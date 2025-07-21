#!/usr/bin/env python3
"""
The actual fucking agent loop that makes your LLM DO things, not just talk about them.
Connects your local LLM to brain.py's file operations.
"""

import json
import re
import requests
from typing import Dict, List, Tuple, Optional

class AgentLoop:
    def __init__(self, llm_endpoint="http://localhost:11434/api/generate", 
                 file_api_endpoint="http://localhost:5005"):
        self.llm_endpoint = llm_endpoint
        self.file_api_endpoint = file_api_endpoint
        self.conversation_history = []
        self.workspace_context = {}
        
    def parse_command(self, llm_response: str) -> Optional[Tuple[str, Dict]]:
        """
        Parse LLM output for commands like:
        - LIST_FILES
        - READ_FILE: filename.txt
        - WRITE_FILE: filename.txt
          Content here...
        - DELETE_FILE: filename.txt
        - EXECUTE: <action>
        """
        # Simple command patterns - expand as needed
        patterns = {
            'list': r'LIST_FILES',
            'read': r'READ_FILE:\s*(.+)',
            'write': r'WRITE_FILE:\s*(.+)\n([\s\S]+?)(?=\n(?:LIST_FILES|READ_FILE|WRITE_FILE|DELETE_FILE|EXECUTE:|$))',
            'delete': r'DELETE_FILE:\s*(.+)',
            'execute': r'EXECUTE:\s*(.+)'
        }
        
        for cmd_type, pattern in patterns.items():
            match = re.search(pattern, llm_response, re.MULTILINE)
            if match:
                if cmd_type == 'list':
                    return ('list', {})
                elif cmd_type == 'read':
                    return ('read', {'filename': match.group(1).strip()})
                elif cmd_type == 'write':
                    return ('write', {
                        'filename': match.group(1).strip(),
                        'content': match.group(2).strip()
                    })
                elif cmd_type == 'delete':
                    return ('delete', {'filename': match.group(1).strip()})
                elif cmd_type == 'execute':
                    return ('execute', {'command': match.group(1).strip()})
        
        return None
    
    def execute_file_operation(self, operation: str, params: Dict) -> str:
        """Execute file operations via your sandbox API"""
        try:
            if operation == 'list':
                response = requests.get(f"{self.file_api_endpoint}/files")
                return f"Files in workspace:\n" + "\n".join(response.json()['files'])
                
            elif operation == 'read':
                response = requests.get(
                    f"{self.file_api_endpoint}/files/{params['filename']}"
                )
                if response.status_code == 200:
                    return f"Content of {params['filename']}:\n{response.json()['content']}"
                else:
                    return f"Error reading {params['filename']}: {response.json().get('error', 'Unknown error')}"
                    
            elif operation == 'write':
                response = requests.post(
                    f"{self.file_api_endpoint}/files/{params['filename']}",
                    json={'content': params['content']}
                )
                if response.status_code == 200:
                    return f"Successfully wrote to {params['filename']}"
                else:
                    return f"Error writing to {params['filename']}: {response.json().get('error', 'Unknown error')}"
                    
            elif operation == 'delete':
                response = requests.delete(
                    f"{self.file_api_endpoint}/files/{params['filename']}"
                )
                if response.status_code == 200:
                    return f"Successfully deleted {params['filename']} (moved to trash)"
                else:
                    return f"Error deleting {params['filename']}: {response.json().get('error', 'Unknown error')}"
                    
        except Exception as e:
            return f"Error executing {operation}: {str(e)}"
        
        return f"Unknown operation: {operation}"
    
    def call_llm(self, prompt: str) -> str:
        """Call your local LLM with context"""
        # Build context from conversation history and workspace state
        full_prompt = f"""You are an AI agent with direct file system access. You can:
- LIST_FILES to see what's in the workspace
- READ_FILE: filename.txt to read files
- WRITE_FILE: filename.txt followed by content to create/update files
- DELETE_FILE: filename.txt to delete files (they go to trash)

Current workspace context:
{json.dumps(self.workspace_context, indent=2)}

Conversation history:
{self._format_history()}

User request: {prompt}

Respond with your reasoning, then execute commands as needed. Be direct and get shit done."""
        
        try:
            response = requests.post(self.llm_endpoint, json={
                "model": "llama3:latest",  # or whatever model you're using
                "prompt": full_prompt,
                "stream": False
            })
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return f"LLM Error: {response.status_code}"
                
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def _format_history(self, max_entries=10) -> str:
        """Format recent conversation history"""
        recent = self.conversation_history[-max_entries:]
        return "\n".join([f"{entry['role']}: {entry['content']}" for entry in recent])
    
    def run_task(self, task: str, max_iterations=10):
        """Main agent loop - give it a task and let it work"""
        print(f"\n🎯 TASK: {task}\n")
        self.conversation_history.append({"role": "user", "content": task})
        
        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1} ---")
            
            # Get LLM response
            llm_response = self.call_llm(task if i == 0 else "Continue with the task")
            print(f"🤖 LLM says:\n{llm_response}\n")
            
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            
            # Parse for commands
            command = self.parse_command(llm_response)
            
            if command:
                cmd_type, params = command
                print(f"📟 Executing: {cmd_type} {params}")
                
                # Execute the command
                result = self.execute_file_operation(cmd_type, params)
                print(f"✅ Result: {result}\n")
                
                # Add result to conversation
                self.conversation_history.append({
                    "role": "system", 
                    "content": f"Command result: {result}"
                })
                
                # Update workspace context if it was a list operation
                if cmd_type == 'list':
                    self.workspace_context['files'] = result.split('\n')[1:]  # Skip header
            else:
                # No command found, check if task is complete
                if any(phrase in llm_response.lower() for phrase in 
                      ['task complete', 'done', 'finished', 'completed']):
                    print("✨ Task completed!")
                    break
        
        print("\n🏁 Agent loop finished")

def main():
    """Let's fucking go"""
    agent = AgentLoop()
    
    # Example tasks - replace with whatever you want
    tasks = [
        "Create a file called test.txt with 'Hello from the agent loop!'",
        "List all files in the workspace and create an index.md with the list",
        "Read the spatial_constellation_anchor.md file and add a new section with today's date"
    ]
    
    print("🚀 AGENT LOOP - Making LLMs Actually Do Shit\n")
    
    while True:
        print("\nWhat do you want the agent to do?")
        print("(or type 'quit' to exit, 'example' for example tasks)")
        
        user_input = input("\n> ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'example':
            for i, task in enumerate(tasks):
                print(f"{i+1}. {task}")
            continue
        else:
            agent.run_task(user_input)

if __name__ == "__main__":
    main()
