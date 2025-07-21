#!/usr/bin/env python3
"""
brain.py - Multi-LLM Orchestrator & Secure File Ops Framework
2025-07-01 (v2 baseline, FIXED)
-------------------------------------------------------------
* Multi-LLM orchestration: OpenAI GPT, Anthropic Claude, Local (Ollama)
* Secure, auditable file operations (list/read/write/append/delete/restore) in llm_workspace/
* All deletes go to .trash, never permanent
* All file ops logged (file_ops.log)
* Permission modes: manual (confirm), auto, readonly (switchable anytime)

Author: Kurt (& AI)
"""

import os
import json
import requests
import shutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# --------------- CONFIG -----------------
from config import config

# --------------- UNIFIED MEMORY -----------------
try:
    import sys
    sys.path.insert(0, '/home/kurt/spatial-ai')
    from persistent_memory_core import get_memory_core, store_memory, retrieve_memory, store_session_state, retrieve_session_state
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    print("Warning: Persistent memory system not available")

# Load unified configuration
from dotenv import load_dotenv
load_dotenv("/home/kurt/spatial-ai/.env")

# ----------- DATA STRUCTURES ------------

@dataclass
class LLMResponse:
    model: str
    response: str
    timestamp: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    response_time: Optional[float] = None

# --------------- MAIN CLASS ---------------

class Brain:
    def __init__(self):
        self.config = config.BRAIN_CONFIG
        self.conversation_log = []
        self.mode = "manual"  # manual, auto, readonly
        self.ensure_workspace()
        
        # Initialize persistent memory
        if MEMORY_ENABLED:
            self.memory = get_memory_core()
            self.session_id = self.memory.get_current_session_id()
            store_memory("brain_system", "initialization", "Brain system initialized with persistent memory")
            
            # Load previous session state
            previous_state = retrieve_session_state("brain_system")
            if previous_state:
                self.mode = previous_state.get("mode", "manual")
                store_memory("brain_system", "state_restore", f"Restored mode: {self.mode}")
        else:
            self.memory = None
            self.session_id = None
    
    def ensure_workspace(self):
        os.makedirs(config.SANDBOX_ROOT, exist_ok=True)
        os.makedirs(config.TRASH_DIR, exist_ok=True)

    # ------------ LLM API Calls ------------

    def call_openai(self, prompt: str, context: str = "") -> LLMResponse:
        start_time = time.time()
        
        # Store LLM call in persistent memory
        if MEMORY_ENABLED:
            store_memory("brain_system", "llm_call", f"OpenAI call: {prompt[:100]}...", 
                        context=context, metadata={"model": "gpt-4o", "provider": "openai"})
        
        try:
            # Use unified config for API key
            api_key = os.getenv("OPENAI_API_KEY") or self.config['openai']['api_key']
            headers = {
                "Authorization": f"Bearer {api_key}",
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
                headers=headers, json=data, timeout=60
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
                headers=headers, json=data, timeout=60
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

    # ----------- FILE OPS: SANDBOXED & AUDITABLE ------------

    def _sandbox_path(self, rel_path: str) -> str:
        abs_path = os.path.abspath(os.path.join(config.SANDBOX_ROOT, rel_path))
        if not abs_path.startswith(config.SANDBOX_ROOT):
            raise PermissionError("Path traversal detected or file outside workspace.")
        return abs_path

    def list_files(self, subdir: str = "") -> List[str]:
        dir_path = self._sandbox_path(subdir)
        if not os.path.exists(dir_path):
            return []
        return sorted(os.listdir(dir_path))

    def read_file(self, path: str) -> str:
        abs_path = self._sandbox_path(path)
        if not os.path.isfile(abs_path):
            return f"[File not found: {path}]"
        with open(abs_path, "r") as f:
            return f.read()

    def write_file(self, path: str, content: str, append=False) -> str:
        abs_path = self._sandbox_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        mode = "a" if append else "w"
        with open(abs_path, mode) as f:
            f.write(content)
        self.log_file_op("append" if append else "write", path)
        return f"[Wrote {len(content)} chars to {path}]"

    def delete_file(self, path: str) -> str:
        abs_path = self._sandbox_path(path)
        os.makedirs(config.TRASH_DIR, exist_ok=True)
        if not os.path.isfile(abs_path):
            return f"[File not found: {path}]"
        trash_path = os.path.join(config.TRASH_DIR, os.path.basename(path))
        shutil.move(abs_path, trash_path)
        self.log_file_op("delete", path)
        return f"[Moved {path} to .trash]"

    def restore_file(self, filename: str) -> str:
        trash_path = os.path.join(config.TRASH_DIR, filename)
        restore_path = self._sandbox_path(filename)
        if not os.path.isfile(trash_path):
            return f"[Not found in trash: {filename}]"
        shutil.move(trash_path, restore_path)
        self.log_file_op("restore", filename)
        return f"[Restored {filename} from .trash]"

    def log_file_op(self, op: str, path: str):
        with open(config.OPS_LOG, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {op} | {path}\\n")

    # ------------ LLM INTERFACE ------------

    def ask_single(self, prompt: str, model: str = "local", context: str = "") -> LLMResponse:
        print(f"🤖 Asking {model}: {prompt[:100]}...")
        if model == "chatgpt":
            response = self.call_openai(prompt, context)
        elif model == "claude":
            response = self.call_claude(prompt, context)
        elif model == "local":
            response = self.call_local_llm(prompt, context)
        else:
            raise ValueError(f"Unknown model: {model}")
        self.log_conversation(prompt, context, {model: response})
        return response

    def ask_all(self, prompt: str, context: str = "", models: List[str] = None) -> Dict[str, LLMResponse]:
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
            if responses[model].error:
                print(f"  ❌ {model} failed: {responses[model].error}")
            else:
                print(f"  ✅ {model} responded ({responses[model].response_time:.1f}s)")
        self.log_conversation(prompt, context, responses)
        return responses

    def log_conversation(self, prompt: str, context: str, responses: Dict[str, LLMResponse]):
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "context": context,
            "responses": {k: asdict(v) for k, v in responses.items()}
        }
        self.conversation_log.append(conversation)
        log_file = self.config['memory']['log_file']
        try:
            with open(log_file, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save log: {e}")

    # ------------- PERMISSION MODE -------------

    def set_mode(self, new_mode: str):
        if new_mode not in config.MODES:
            print(f"[Invalid mode: {new_mode}] Modes: {config.MODES}")
            return
        self.mode = new_mode
        print(f"[Mode set to {new_mode}]")

    def confirm(self, action_desc: str) -> bool:
        if self.mode == "auto":
            return True
        elif self.mode == "readonly":
            print("[Readonly mode: operation blocked]")
            return False
        else:
            choice = input(f"Confirm {action_desc}? [Y/n]: ").strip().lower()
            return choice in ["", "y", "yes"]

    # ------------- CLI INTERFACE -------------

    def interactive_mode(self):
        # Import preferences_manager here to avoid circular dependencies if it imports Brain
        from components.user_prefs.preferences_manager import load_user_preferences

        print("🧠 brain.py - MultiLLM Orchestrator")
        print("Type 'help' for commands. Workspace:", config.SANDBOX_ROOT)
        print("Current mode:", self.mode)
        print("="*60)

        # Load user preferences at startup
        user_prefs = load_user_preferences()
        print("\n--- User Preferences Loaded ---")
        print(user_prefs[:200] + "...\n") # Print first 200 chars for confirmation
        print("-------------------------------")
        
        while True:
            try:
                user_input = input("\n💭 > ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == "help":
                    print("""
LLM chat:
  all <prompt>            - Ask all models
  chatgpt <prompt>        - Ask ChatGPT
  claude <prompt>         - Ask Claude
  local <prompt>          - Ask Local LLM

File ops:
  list [dir]              - List files in [dir] (default ".")
  read <path>             - Show file content
  write <path> <content>  - Write (overwrite) file (ask to confirm)
  append <path> <content> - Append to file (ask to confirm)
  delete <path>           - Move file to .trash (ask to confirm)
  restore <filename>      - Restore from .trash (ask to confirm)

Mode/Control:
  set mode <manual|auto|readonly>   - Change permission mode
  help                   - Show this help
  quit/exit/q            - Quit
""")
                elif user_input.startswith('all '):
                    prompt = user_input[4:]
                    # Pass user preferences as context to LLMs
                    responses = self.ask_all(prompt, context=user_prefs)
                    print(self.compare_responses(responses))
                elif user_input.startswith('chatgpt '):
                    prompt = user_input[8:]
                    response = self.ask_single(prompt, "chatgpt", context=user_prefs)
                    print(response.response if not response.error else f"❌ {response.error}")
                elif user_input.startswith('claude '):
                    prompt = user_input[7:]
                    response = self.ask_single(prompt, "claude", context=user_prefs)
                    print(response.response if not response.error else f"❌ {response.error}")
                elif user_input.startswith('local '):
                    prompt = user_input[6:]
                    response = self.ask_single(prompt, "local", context=user_prefs)
                    print(response.response if not response.error else f"❌ {response.error}")

                # ----- File operations -----
                elif user_input.startswith('list'):
                    parts = user_input.split(" ", 1)
                    subdir = parts[1] if len(parts) > 1 else ""
                    print(self.list_files(subdir))
                elif user_input.startswith('read '):
                    path = user_input[5:]
                    print(self.read_file(path))
                elif user_input.startswith('write '):
                    parts = user_input[6:].split(' ', 1)
                    if len(parts) < 2:
                        print("Usage: write <path> <content>")
                    else:
                        if self.confirm(f"write to {parts[0]}"):
                            print(self.write_file(parts[0], parts[1], append=False))
                        else:
                            print("[Write cancelled.]")
                elif user_input.startswith('append '):
                    parts = user_input[7:].split(' ', 1)
                    if len(parts) < 2:
                        print("Usage: append <path> <content>")
                    else:
                        if self.confirm(f"append to {parts[0]}"):
                            print(self.write_file(parts[0], parts[1], append=True))
                        else:
                            print("[Append cancelled.]")
                elif user_input.startswith('delete '):
                    path = user_input[7:]
                    if self.confirm(f"delete {path} (move to .trash)"):
                        print(self.delete_file(path))
                    else:
                        print("[Delete cancelled.]")
                elif user_input.startswith('restore '):
                    filename = user_input[8:]
                    if self.confirm(f"restore {filename} from .trash"):
                        print(self.restore_file(filename))
                    else:
                        print("[Restore cancelled.]")

                # --- Mode switching ---
                elif user_input.startswith('set mode '):
                    new_mode = user_input[9:].strip()
                    self.set_mode(new_mode)
                else:
                    print("Unknown command. Type 'help' for usage.")
            except KeyboardInterrupt:
                print("\\n[Interrupted.]")
                break
            except Exception as e:
                print(f"[Error: {e}]")

    def compare_responses(self, responses: Dict[str, LLMResponse]) -> str:
        comparison = "\\n" + "="*60 + "\\n"
        comparison += "🤖 MULTI-LLM RESPONSE COMPARISON\\n"
        comparison += "="*60 + "\\n"
        for model, response in responses.items():
            comparison += f"\\n🔹 {response.model}:\\n"
            if response.error:
                comparison += f"❌ Error: {response.error}\\n"
            else:
                comparison += f"⏱️  Response time: {response.response_time:.1f}s\\n"
                if response.tokens_used:
                    comparison += f"🎯 Tokens: {response.tokens_used}\\n"
                comparison += f"💬 Response:\\n{response.response}\\n"
            comparison += "-" * 40 + "\\n"
        return comparison

# ---------------- MAIN ENTRY ----------------

if __name__ == "__main__":
    brain = Brain()
    brain.interactive_mode()
