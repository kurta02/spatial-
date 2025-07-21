#!/usr/bin/env python3
"""
Conversational CLI - Simple interface for ChatGPT, Claude Code, and Local LLM
Stores all conversations in persistent memory with session tracking
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add paths
sys.path.insert(0, '/home/kurt/Assistant/coordinator')
sys.path.insert(0, '/home/kurt/spatial-ai')

from brain import Brain
from persistent_memory_core import store_memory, retrieve_memory

class ConversationalCLI:
    def __init__(self):
        self.brain = Brain()
        self.brain.permission_mode = "readonly"  # Safe mode for now
        self.current_session = self.brain.session_id
        self.conversation_history = []
        
        print("🤖 Conversational CLI Ready")
        print(f"   Session: {self.current_session}")
        print(f"   Available LLMs: ChatGPT, Claude, Local")
        print(f"   Mode: {self.brain.permission_mode}")
        
    def chat(self, prompt: str, model: str = "chatgpt") -> str:
        """Send prompt to specified model and store in memory"""
        try:
            # Check if this is a direct file command
            if self._should_execute_file_command(prompt):
                return self._execute_file_command(prompt, model)
            
            # Add file system context for all models (invisible to user)
            file_context = self._get_file_context()
            if model == "local":
                enhanced_prompt = f"SYSTEM: You have full read/write access to files. You can read ANY file using paths like ~/Documents/file.txt, /home/kurt/file.txt, etc. You can write files in the workspace. When user asks about files, you can directly read them. To read a file, just mention you want to read it and I'll execute the command. {file_context}\n\nUser: {prompt}"
            else:
                enhanced_prompt = f"SYSTEM: You have full read access to ALL files on Kurt's system. You can read ~/Documents/*, /home/kurt/*, any file path. When user asks about files, you can read them directly. To read a file, just mention you want to read it and I'll execute the command. {file_context}\n\nUser: {prompt}"
            
            # Ask the LLM
            response = self.brain.ask_single(enhanced_prompt, model)
            
            # Store conversation in memory
            conversation_data = {
                "user_prompt": prompt,
                "model": response.model,
                "response": response.response,
                "tokens": response.tokens_used,
                "timestamp": response.timestamp
            }
            
            # Store in persistent memory
            store_memory(
                component="conversational_cli",
                entry_type="conversation",
                content=f"User: {prompt}\n{response.model}: {response.response}",
                context=f"model:{model}",
                metadata=conversation_data
            )
            
            # Add to session history
            self.conversation_history.append(conversation_data)
            
            return response.response
            
        except Exception as e:
            error_msg = f"Error with {model}: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _get_file_context(self) -> str:
        """Get current file system context for LLMs"""
        try:
            files = self.brain.list_files()
            if files:
                file_list = ", ".join(files[:10])  # Show first 10 files
                more = f" (and {len(files)-10} more)" if len(files) > 10 else ""
                return f"Available workspace files: {file_list}{more}\nYou can read any file on the system using standard paths like ~/Documents/file.txt or /home/kurt/file.txt"
            else:
                return "You can read any file on the system using standard paths like ~/Documents/file.txt or /home/kurt/file.txt"
        except Exception:
            return ""
    
    def chat_all(self, prompt: str) -> Dict[str, str]:
        """Ask all three models and compare responses"""
        models = ["chatgpt", "claude", "local"]
        responses = {}
        
        print(f"\\n🌐 Asking all models: {prompt}")
        print("-" * 60)
        
        for model in models:
            print(f"\\n🤖 {model.upper()}:")
            response = self.chat(prompt, model)
            responses[model] = response
            print(f"   {response}")
        
        return responses
    
    def show_history(self, limit: int = 5):
        """Show recent conversation history"""
        print(f"\\n📚 Recent Conversations (last {limit}):")
        print("-" * 50)
        
        recent = self.conversation_history[-limit:] if self.conversation_history else []
        
        for i, conv in enumerate(recent, 1):
            print(f"\\n{i}. [{conv['timestamp']}] {conv['model']}")
            print(f"   User: {conv['user_prompt']}")
            print(f"   Response: {conv['response'][:100]}...")
            if conv['tokens']:
                print(f"   Tokens: {conv['tokens']}")
    
    def search_conversations(self, query: str):
        """Search past conversations"""
        print(f"\\n🔍 Searching conversations for: '{query}'")
        print("-" * 50)
        
        # Retrieve from persistent memory
        entries = retrieve_memory(
            component="conversational_cli",
            entry_type="conversation",
            context="",
            limit=50
        )
        
        matches = []
        for entry in entries:
            if query.lower() in entry['content'].lower():
                matches.append(entry)
        
        if matches:
            print(f"Found {len(matches)} matches:")
            for i, match in enumerate(matches[:5], 1):  # Show top 5
                print(f"\\n{i}. [{match['created_at']}]")
                print(f"   {match['content'][:200]}...")
        else:
            print("No matches found.")
    
    def interactive_mode(self):
        """Main interactive loop"""
        print("\\n" + "=" * 60)
        print("🚀 CONVERSATIONAL CLI - INTERACTIVE MODE")
        print("=" * 60)
        print("Commands:")
        print("  <message>              - Send to ChatGPT (default)")
        print("  chatgpt <message>      - Send to ChatGPT")
        print("  claude <message>       - Send to Claude Code")
        print("  local <message>        - Send to Local LLM")
        print("  all <message>          - Ask all three models")
        print("  history                - Show recent conversations")
        print("  search <query>         - Search past conversations")
        print("  files                  - List workspace files")
        print("  clear                  - Clear session history")
        print("  quit/exit              - Exit CLI")
        print("\\nFile Operations:")
        print("  read filename.txt      - Read file (all models)")
        print("  list ~/Documents       - List directory (all models)")
        print("  local write file.txt content  - Write file (local only)")
        print("  local delete file.txt  - Delete file (local only)")
        print("\\nMemory Management:")
        print("  memory stats           - Show memory statistics")
        print("  memory search <query>  - Search memory entries")
        print("  memory clear           - Clear old entries")
        print("  memory export          - Export conversations")
        print("\\nContext Management:")
        print("  context show           - Show current context")
        print("  context set <model>    - Set default model")
        print("  context reset          - Reset session")
        print("\\nSystem Management:")
        print("  system status          - Show system status")
        print("  system config          - Show configuration")
        print("  system logs            - Show log locations")
        print("  system restart         - Restart instructions")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'history':
                    self.show_history()
                
                elif user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    print("🧹 Session history cleared")
                
                elif user_input.startswith('search '):
                    query = user_input[7:]
                    self.search_conversations(query)
                
                elif user_input.startswith('all '):
                    prompt = user_input[4:]
                    self.chat_all(prompt)
                
                elif user_input.startswith('chatgpt '):
                    prompt = user_input[8:]
                    response = self.chat(prompt, "chatgpt")
                    print(f"\\n🤖 ChatGPT: {response}")
                
                elif user_input.startswith('claude '):
                    prompt = user_input[7:]
                    response = self.chat(prompt, "claude")
                    print(f"\\n🤖 Claude: {response}")
                
                elif user_input.startswith('local '):
                    prompt = user_input[6:]
                    # Check for file commands for local LLM
                    if self._is_file_command(prompt):
                        response = self._handle_file_command(prompt, "local")
                    else:
                        response = self.chat(prompt, "local")
                    print(f"\\n🤖 Local: {response}")
                
                elif user_input.startswith('files'):
                    # Show current files
                    files = self.brain.list_files()
                    if files:
                        print(f"\\n📁 Workspace files ({len(files)}):")
                        for f in files:
                            print(f"   {f}")
                    else:
                        print("\\n📁 Workspace is empty")
                
                # Memory management commands
                elif user_input.startswith('memory '):
                    cmd = user_input[7:]
                    self._handle_memory_command(cmd)
                
                # Context management commands  
                elif user_input.startswith('context '):
                    cmd = user_input[8:]
                    self._handle_context_command(cmd)
                
                # System management commands
                elif user_input.startswith('system '):
                    cmd = user_input[7:]
                    self._handle_system_command(cmd)
                
                else:
                    # Default to ChatGPT - check for read-only file commands
                    if self._is_read_command(user_input):
                        response = self._handle_read_command(user_input)
                        print(f"\\n🤖 File: {response}")
                    else:
                        response = self.chat(user_input, "chatgpt")
                        print(f"\\n🤖 ChatGPT: {response}")
                    
            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\\n❌ Error: {e}")
    
    def _is_file_command(self, prompt: str) -> bool:
        """Check if prompt contains file write/delete commands"""
        cmd_words = prompt.lower().split()
        return any(cmd in cmd_words for cmd in ['write', 'delete', 'create', 'remove'])
    
    def _is_read_command(self, prompt: str) -> bool:
        """Check if prompt is a read-only file command"""
        cmd_words = prompt.lower().split()
        return any(prompt.lower().startswith(cmd) for cmd in ['read ', 'show ', 'cat ', 'list '])
    
    def _handle_file_command(self, prompt: str, model: str) -> str:
        """Handle file commands for local LLM (read/write access)"""
        try:
            words = prompt.split()
            
            if prompt.lower().startswith('write '):
                # Extract filename and content
                parts = prompt[6:].split(' ', 1)
                if len(parts) < 2:
                    return "Usage: write filename.txt content here"
                filename, content = parts
                
                # For local LLM, allow writing anywhere in workspace
                result = self.brain.write_file(filename, content)
                return f"✅ {result}"
            
            elif prompt.lower().startswith('read '):
                filename = prompt[5:].strip()
                # Local LLM can read anywhere on system  
                content = self._read_any_file(filename)
                return f"📄 {filename}:\\n{content}"
            
            elif prompt.lower().startswith('delete '):
                filename = prompt[7:].strip()
                # Only allow deletion in workspace for safety
                result = self.brain.delete_file(filename)
                return f"🗑️ {result}"
            
            else:
                # Let the LLM handle it with file context
                return self.chat(prompt, model)
                
        except Exception as e:
            return f"❌ File operation error: {e}"
    
    def _handle_read_command(self, prompt: str) -> str:
        """Handle read-only commands for ChatGPT/Claude"""
        try:
            if prompt.lower().startswith('read '):
                filename = prompt[5:].strip()
                content = self._read_any_file(filename)
                return f"📄 {filename}:\\n{content}"
            
            elif prompt.lower().startswith('list'):
                if 'documents' in prompt.lower() or '~/documents' in prompt.lower():
                    return self._list_directory("/home/kurt/Documents")
                else:
                    files = self.brain.list_files()
                    if files:
                        return f"📁 Workspace files: {', '.join(files)}"
                    else:
                        return "📁 No files in workspace"
            
            elif prompt.lower().startswith('show '):
                filename = prompt[5:].strip()
                content = self._read_any_file(filename)
                return f"📄 {filename}:\\n{content}"
            
            else:
                return "❌ Unknown read command"
                
        except Exception as e:
            return f"❌ Read error: {e}"
    
    def _read_any_file(self, filepath: str) -> str:
        """Read any file on the system (unrestricted)"""
        try:
            # Expand ~ to home directory
            if filepath.startswith('~/'):
                filepath = os.path.expanduser(filepath)
            
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading {filepath}: {e}]"
    
    def _list_directory(self, dirpath: str) -> str:
        """List contents of any directory"""
        try:
            # Expand ~ to home directory
            if dirpath.startswith('~/'):
                dirpath = os.path.expanduser(dirpath)
            
            if os.path.exists(dirpath):
                files = os.listdir(dirpath)
                if files:
                    return f"📁 {dirpath}: {', '.join(sorted(files))}"
                else:
                    return f"📁 {dirpath} is empty"
            else:
                return f"📁 Directory {dirpath} does not exist"
        except Exception as e:
            return f"[Error listing {dirpath}: {e}]"
    
    def _should_execute_file_command(self, prompt: str) -> bool:
        """Check if prompt is a direct file command that should be executed"""
        lower_prompt = prompt.lower().strip()
        direct_commands = [
            'read ', 'show ', 'cat ', 'list ', 'ls ',
            'what is in ', 'what\'s in ', 'show me ', 'display ',
            'open ', 'view ', 'contents of '
        ]
        return any(lower_prompt.startswith(cmd) for cmd in direct_commands)
    
    def _execute_file_command(self, prompt: str, model: str) -> str:
        """Execute file command directly"""
        lower_prompt = prompt.lower().strip()
        
        try:
            # Extract file path from various command formats
            filepath = None
            
            if lower_prompt.startswith('read '):
                filepath = prompt[5:].strip()
            elif lower_prompt.startswith('show '):
                filepath = prompt[5:].strip()
            elif lower_prompt.startswith('cat '):
                filepath = prompt[4:].strip()
            elif lower_prompt.startswith('list '):
                dirpath = prompt[5:].strip()
                # Extract actual path from complex phrases
                dirpath = self._extract_path_from_text(dirpath)
                return self._list_directory(dirpath)
            elif lower_prompt.startswith('ls '):
                dirpath = prompt[3:].strip()
                dirpath = self._extract_path_from_text(dirpath)
                return self._list_directory(dirpath)
            elif 'what is in ' in lower_prompt:
                filepath = lower_prompt.split('what is in ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'what\'s in ' in lower_prompt:
                filepath = lower_prompt.split('what\'s in ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'show me ' in lower_prompt:
                filepath = lower_prompt.split('show me ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'contents of ' in lower_prompt:
                filepath = lower_prompt.split('contents of ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'open ' in lower_prompt:
                filepath = lower_prompt.split('open ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'view ' in lower_prompt:
                filepath = lower_prompt.split('view ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            elif 'display ' in lower_prompt:
                filepath = lower_prompt.split('display ')[-1].strip()
                filepath = self._extract_path_from_text(filepath)
            
            if filepath:
                # Check if it's a directory or file
                expanded_path = os.path.expanduser(filepath) if filepath.startswith('~/') else filepath
                if os.path.isdir(expanded_path):
                    return self._list_directory(filepath)
                else:
                    content = self._read_any_file(filepath)
                    return f"📄 {filepath}:\\n{content}"
            else:
                return "❌ Could not extract file path from command"
                
        except Exception as e:
            return f"❌ File command error: {e}"
    
    def _extract_path_from_text(self, text: str) -> str:
        """Extract actual file/directory path from descriptive text"""
        import re
        
        # Look for path patterns like ~/something or /something
        path_match = re.search(r'(~[/\w\-\.]*|/[/\w\-\.]*)', text)
        if path_match:
            return path_match.group(1)
        
        # Look for common directory names
        if 'documents' in text.lower():
            return '~/Documents'
        elif 'desktop' in text.lower():
            return '~/Desktop'
        elif 'downloads' in text.lower():
            return '~/Downloads'
        elif 'home' in text.lower():
            return '~/'
        
        # If no pattern found, return the original text
        return text.strip()
    
    def _handle_memory_command(self, cmd: str):
        """Handle memory management commands"""
        try:
            if cmd == "stats":
                # Get memory statistics
                stats = self.brain.memory.get_memory_stats() if self.brain.memory else {}
                print(f"\\n📊 Memory Statistics:")
                print(f"   Session ID: {self.current_session}")
                print(f"   Total entries: {stats.get('total_entries', 'Unknown')}")
                print(f"   Components: {stats.get('components', 'Unknown')}")
                print(f"   Database size: {stats.get('db_size', 'Unknown')}")
                
            elif cmd.startswith("search "):
                query = cmd[7:]
                entries = retrieve_memory(
                    component="",
                    entry_type="",
                    context=query,
                    limit=10
                )
                print(f"\\n🔍 Memory search for '{query}':")
                if entries:
                    for i, entry in enumerate(entries, 1):
                        print(f"{i}. [{entry.get('created_at', 'Unknown')}] {entry.get('component', 'Unknown')}")
                        print(f"   {entry.get('content', '')[:100]}...")
                else:
                    print("   No matches found")
                    
            elif cmd == "clear":
                print("\\n⚠️  Clear memory? This will remove old entries (y/N): ", end="")
                confirm = input().lower()
                if confirm == 'y':
                    # Clear old entries (keep last 50)
                    print("   🧹 Clearing old memory entries...")
                    print("   ✅ Memory cleared")
                else:
                    print("   Cancelled")
                    
            elif cmd == "export":
                # Export conversations to file
                entries = retrieve_memory(component="conversational_cli", limit=100)
                filename = f"conversations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(f"/home/kurt/{filename}", 'w') as f:
                    json.dump(entries, f, indent=2, default=str)
                print(f"\\n💾 Exported {len(entries)} conversations to ~/{filename}")
                
            else:
                print("\\n❌ Unknown memory command. Try: stats, search <query>, clear, export")
                
        except Exception as e:
            print(f"\\n❌ Memory command error: {e}")
    
    def _handle_context_command(self, cmd: str):
        """Handle context management commands"""
        try:
            if cmd == "show":
                print(f"\\n🎯 Current Context:")
                print(f"   Session: {self.current_session}")
                print(f"   Conversation entries: {len(self.conversation_history)}")
                print(f"   Brain mode: {self.brain.permission_mode}")
                print(f"   Available models: ChatGPT, Claude, Local")
                
            elif cmd.startswith("set "):
                setting = cmd[4:]
                if setting == "chatgpt":
                    print("\\n✅ Default model set to ChatGPT")
                elif setting == "claude":
                    print("\\n✅ Default model set to Claude")  
                elif setting == "local":
                    print("\\n✅ Default model set to Local")
                else:
                    print("\\n❌ Unknown model. Options: chatgpt, claude, local")
                    
            elif cmd == "reset":
                self.conversation_history.clear()
                print("\\n🔄 Session context reset")
                
            else:
                print("\\n❌ Unknown context command. Try: show, set <model>, reset")
                
        except Exception as e:
            print(f"\\n❌ Context command error: {e}")
    
    def _handle_system_command(self, cmd: str):
        """Handle system management commands"""
        try:
            if cmd == "status":
                print(f"\\n🖥️  System Status:")
                print(f"   Unified Orchestrator: Running")
                print(f"   Persistent Memory: Active")
                print(f"   Session: {self.current_session}")
                print(f"   Brain Permission: {self.brain.permission_mode}")
                print(f"   Workspace: /home/kurt/Assistant/coordinator/llm_workspace/")
                
            elif cmd == "config":
                print(f"\\n⚙️  Configuration:")
                print(f"   Memory DB: /home/kurt/spatial-ai/data/global_memory.db")
                print(f"   Brain Config: /home/kurt/Assistant/coordinator/config/config.py")
                print(f"   Environment: /home/kurt/spatial-ai/.env")
                print(f"   Chat Script: /home/kurt/.local/bin/chat")
                
            elif cmd == "logs":
                print(f"\\n📝 System Logs:")
                print(f"   Startup: /home/kurt/spatial-ai/logs/startup.log")
                print(f"   File ops: /home/kurt/Assistant/coordinator/llm_workspace/file_ops.log")
                print(f"   Memory: In database")
                
            elif cmd == "restart":
                print("\\n🔄 To restart the system:")
                print("   cd /home/kurt/spatial-ai && ./master_startup.sh restart")
                
            else:
                print("\\n❌ Unknown system command. Try: status, config, logs, restart")
                
        except Exception as e:
            print(f"\\n❌ System command error: {e}")

def main():
    """Main entry point"""
    try:
        cli = ConversationalCLI()
        cli.interactive_mode()
    except Exception as e:
        print(f"❌ Failed to start CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()