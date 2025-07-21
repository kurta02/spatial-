#!/usr/bin/env python3
"""
Direct brain.py integration - Makes your LLM actually DO things
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brain import Brain
import requests
import json
import re

class BrainAgent:
    def __init__(self):
        # Initialize with workspace in the brain directory
        os.chdir(os.path.expanduser("~/Documents/brain"))
        self.brain = Brain()
        self.conversation = []
        
    def call_llm(self, prompt):
        """Call your local LLM"""
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={
                    'model': 'llama3:latest',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()['response']
        except:
            return "Error calling LLM - is Ollama running?"
    
    def execute_task(self, task):
        """Main execution loop"""
        print(f"\n🎯 TASK: {task}\n")
        
        # Get file list
        files = self.brain.list_files()
        
        prompt = f"""Task: {task}

Current files in workspace: {files}

You have these commands:
- To list files, say "LIST_FILES" 
- To read a file, say "READ_FILE: filename"
- To write a file, say "WRITE_FILE: filename" then the content
- To delete a file, say "DELETE_FILE: filename"

Complete the task and say DONE when finished."""

        # Simple execution loop
        for i in range(5):
            response = self.call_llm(prompt)
            print(f"LLM: {response}\n")
            
            # Parse commands
            if "LIST_FILES" in response:
                files = self.brain.list_files()
                print(f"Files: {files}\n")
                prompt = f"Files in workspace: {files}\nContinue with task."
                
            elif "READ_FILE:" in response:
                match = re.search(r'READ_FILE:\s*(\S+)', response)
                if match:
                    filename = match.group(1)
                    content = self.brain.read_file(filename)
                    print(f"Read {filename}: {content[:200]}...\n")
                    prompt = f"Content of {filename}: {content}\nContinue with task."
                    
            elif "WRITE_FILE:" in response:
                match = re.search(r'WRITE_FILE:\s*(\S+)\s*\n(.*)', response, re.DOTALL)
                if match:
                    filename = match.group(1)
                    content = match.group(2).split('DONE')[0].strip()
                    self.brain.write_file(filename, content)
                    print(f"Wrote {filename}\n")
                    prompt = f"Successfully wrote {filename}. Continue with task."
                    
            if "DONE" in response:
                print("✅ Task completed!")
                break

if __name__ == "__main__":
    agent = BrainAgent()
    
    # Run the cleanup task
    task = """Find information about brain.py files and create a cleanup_report.md with:
    1. A list of locations where brain.py files exist
    2. Recommendations for organizing them
    3. Next steps for cleanup"""
    
    agent.execute_task(task)
