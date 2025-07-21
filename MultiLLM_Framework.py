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
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv

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

class SafeFileSystem:
    """Controlled file system access for LLMs"""
    
    def __init__(self, workspace_dir="./", backup_dir="./backups"):
        self.workspace = Path(workspace_dir).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(exist_ok=True)
        self.allowed_extensions = {'.py', '.json', '.txt', '.md', '.yaml', '.yml'}
        
    def read_file(self, filepath: str) -> str:
        """Safely read files within workspace"""
        full_path = self._validate_path(filepath)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Could not read file {filepath}: {e}")
    
    def write_file(self, filepath: str, content: str, backup: bool = True) -> bool:
        """Safely write files with automatic backup"""
        full_path = self._validate_path(filepath)
        
        if backup and full_path.exists():
            self._backup_file(full_path)
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            raise Exception(f"Could not write file {filepath}: {e}")
    
    def list_files(self, pattern: str = "*") -> List[str]:
        """List files in workspace"""
        try:
            return [str(p.relative_to(self.workspace)) 
                    for p in self.workspace.glob(pattern) if p.is_file()]
        except Exception as e:
            raise Exception(f"Could not list files: {e}")
    
    def backup_file(self, filepath: str) -> str:
        """Create backup of a file"""
        full_path = self._validate_path(filepath)
        return self._backup_file(full_path)
    
    def _validate_path(self, filepath: str) -> Path:
        """Ensure path is within workspace and safe"""
        # Convert to Path and resolve
        if filepath.startswith('/'):
            # Absolute path - convert to relative
            filepath = filepath.lstrip('/')
        
        full_path = (self.workspace / filepath).resolve()
        
        # Security check: must be within workspace
        try:
            full_path.relative_to(self.workspace)
        except ValueError:
            raise Exception(f"Path outside workspace: {filepath}")
        
        # Extension check
        if full_path.suffix and full_path.suffix not in self.allowed_extensions:
            raise Exception(f"File type not allowed: {full_path.suffix}")
        
        return full_path
    
    def _backup_file(self, full_path: Path) -> str:
        """Create timestamped backup of file"""
        if not full_path.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{full_path.stem}_{timestamp}{full_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(full_path, backup_path)
        return str(backup_path)

class Toolbox:
    """A registry for tools that LLMs can use."""
    
    def __init__(self, framework):
        self.framework = framework
        self.tools = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register the default file system and scratchpad tools."""
        self.register_tool("read_file", self.framework.fs.read_file)
        self.register_tool("write_file", self.framework.fs.write_file)
        self.register_tool("list_files", self.framework.fs.list_files)
        self.register_tool("set_scratchpad", self.framework.scratchpad.set)
        self.register_tool("get_scratchpad", self.framework.scratchpad.get)
        self.register_tool("delegate_task", self.framework.delegate_task)
        self.register_tool("recall_memory", self.framework.recall_memory)
        self.register_tool("request_user_approval", self.framework.request_user_approval)

    def register_tool(self, name: str, function: callable):
        """Register a new tool."""
        self.tools[name] = function

    def use_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with the given parameters."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found.")
        
        try:
            return self.tools[tool_name](**parameters)
        except Exception as e:
            return f"Error executing tool {tool_name}: {e}"

    def get_tool_prompt(self) -> str:
        """Get the prompt section that describes the available tools."""
        return """
**AVAILABLE TOOLS**

You have access to a file system to help you with your tasks. You can request to use a tool by responding with a JSON object with the key "tool_use".

**Tools:**
- `read_file(filepath: str)`: Reads the content of a file.
- `write_file(filepath: str, content: str)`: Writes content to a file, overwriting it.
- `list_files(pattern: str)`: Lists files in the workspace.
- `set_scratchpad(key: str, value: str)`: Saves information to a shared scratchpad.
- `get_scratchpad(key: str)`: Retrieves information from the shared scratchpad.
- `delegate_task(target_llm: str, task_prompt: str)`: Delegates a task to another LLM.
- `recall_memory(query: str)`: Recalls information from the conversation history.
- `request_user_approval(reason: str)`: Asks the user for approval to proceed with a risky action.

**Example Request:**
```json
{
  "thought": "I need to see what files are in the project.",
  "tool_use": {
    "tool_name": "list_files",
    "parameters": { "pattern": "*" }
  }
}
```
"""

class SharedScratchpad:
    """A simple in-memory key-value store for LLM collaboration."""
    def __init__(self):
        self.data = {}

    def set(self, key: str, value: str):
        """Set a value in the scratchpad."""
        self.data[key] = value
        return f"Value set for key '{key}'."

    def get(self, key: str) -> Optional[str]:
        """Get a value from the scratchpad."""
        return self.data.get(key, f"No value found for key '{key}'.")

class ConversationMode:
    """Base class for conversation modes"""
    
    def __init__(self, framework):
        self.framework = framework
        self.conversation_history = []
    
    def run(self, prompt, max_rounds=5):
        """Run the conversation mode"""
        raise NotImplementedError

class RoundRobinConversation(ConversationMode):
    """Natural back-and-forth conversation between all LLMs"""
    
    def run(self, prompt, max_rounds=5):
        print(f"🔄 Starting Round-Robin Discussion: {prompt}")
        print("=" * 60)
        
        participants = ["local", "claude", "chatgpt"]
        responses = {}
        
        for round_num in range(max_rounds):
            print(f"\n📍 Round {round_num + 1}")
            print("-" * 30)
            
            for llm in participants:
                # Build context from previous responses
                context = self._build_context(responses, round_num)
                
                # Create prompt with conversation context
                full_prompt = f"""
Topic: {prompt}

{context}

Please contribute to this discussion. Build on previous responses if relevant, 
add new insights, and help move the conversation forward constructively.
"""
                
                response = self.framework.ask_single(full_prompt, llm)
                responses[f"{llm}_round_{round_num}"] = response
                
                print(f"🤖 {response.model}:")
                if response.error:
                    print(f"❌ Error: {response.error}")
                else:
                    print(f"{response.response}\n")
                
                # Check for natural conclusion
                if self._check_consensus(response.response):
                    print("✅ Consensus reached!")
                    return responses
        
        return responses
    
    def _build_context(self, responses, current_round):
        if not responses:
            return "This is the start of our discussion."
        
        context = "Previous discussion:\n"
        for key, response in responses.items():
            if not response.error:
                context += f"- {response.model}: {response.response[:150]}...\n"
        return context
    
    def _check_consensus(self, response):
        consensus_indicators = ["i agree", "consensus", "we all agree", "perfect", "exactly"]
        return any(indicator in response.lower() for indicator in consensus_indicators)

class ModeratedConversation(ConversationMode):
    """Structured conversation with Local LLM as moderator"""
    
    def run(self, prompt, max_rounds=5):
        print(f"🎯 Starting Moderated Discussion: {prompt}")
        print("🤖 Local LLM will moderate this discussion")
        print("=" * 60)
        
        # Moderator opens the discussion
        moderator_prompt = f"""
You are moderating a discussion about: {prompt}

Your role is to:
1. Guide the conversation systematically
2. Ask specific questions to Claude and ChatGPT
3. Ensure comprehensive coverage of the topic
4. Synthesize conclusions

Start by outlining the key aspects we should discuss, then ask Claude the first specific question.
"""
        
        moderator_response = self.framework.ask_single(moderator_prompt, "local")
        print(f"🤖 {moderator_response.model} (Moderator):")
        print(f"{moderator_response.response}\n")
        
        # Continue structured discussion
        participants = ["claude", "chatgpt"]
        current_participant = 0
        
        for round_num in range(max_rounds - 1):  # -1 because moderator already spoke
            participant = participants[current_participant % len(participants)]
            
            # Moderator asks specific question
            context = self._build_moderated_context(moderator_response, round_num)
            
            participant_prompt = f"""
Discussion topic: {prompt}
Moderator's guidance: {moderator_response.response}

{context}

Please respond to the moderator's question or guidance above.
"""
            
            response = self.framework.ask_single(participant_prompt, participant)
            print(f"🧠 {response.model}:")
            if response.error:
                print(f"❌ Error: {response.error}")
            else:
                print(f"{response.response}\n")
            
            # Moderator responds
            moderator_followup = f"""
{participant}'s response: {response.response}

Continue moderating the discussion. Ask the next question or provide synthesis.
"""
            
            moderator_response = self.framework.ask_single(moderator_followup, "local")
            print(f"🤖 {moderator_response.model} (Moderator):")
            print(f"{moderator_response.response}\n")
            
            current_participant += 1
        
        return {"moderated_discussion": "completed"}
    
    def _build_moderated_context(self, moderator_response, round_num):
        return f"This is round {round_num + 1} of our structured discussion."

class RoleBasedConversation(ConversationMode):
    """Conversation with specialized roles for each LLM"""
    
    def run(self, prompt, max_rounds=5):
        print(f"👥 Starting Role-Based Discussion: {prompt}")
        print("🏗️  Local LLM: System Architect")
        print("🔍 Claude: Code Reviewer") 
        print("⚙️  ChatGPT: Implementation Specialist")
        print("=" * 60)
        
        roles = {
            "local": "System Architect - Focus on high-level design, architecture patterns, and system integration",
            "claude": "Code Reviewer - Focus on code quality, best practices, security, and maintainability", 
            "chatgpt": "Implementation Specialist - Focus on practical implementation, specific solutions, and technical details"
        }
        
        responses = {}
        
        # Each role provides their perspective
        for llm, role_description in roles.items():
            role_prompt = f"""
ROLE: {role_description}

TOPIC: {prompt}

Provide your expert perspective on this topic from your specialized role. 
Focus on the aspects most relevant to your expertise.
"""
            
            response = self.framework.ask_single(role_prompt, llm)
            responses[llm] = response
            
            role_emoji = {"local": "🏗️", "claude": "🔍", "chatgpt": "⚙️"}
            print(f"{role_emoji[llm]} {response.model} ({role_description.split(' - ')[0]}):")
            if response.error:
                print(f"❌ Error: {response.error}")
            else:
                print(f"{response.response}\n")
        
        # Follow-up rounds for collaboration
        for round_num in range(1, max_rounds):
            print(f"📍 Collaboration Round {round_num}")
            print("-" * 30)
            
            for llm, role_description in roles.items():
                # Build context from other roles
                other_responses = {k: v for k, v in responses.items() if k != llm}
                context = self._build_role_context(other_responses)
                
                collab_prompt = f"""
ROLE: {role_description}
TOPIC: {prompt}

Other team members have provided their perspectives:
{context}

Respond to their input from your role's perspective. Address any concerns, 
build on good ideas, or propose solutions to challenges they've raised.
"""
                
                response = self.framework.ask_single(collab_prompt, llm)
                responses[f"{llm}_round_{round_num}"] = response
                
                role_emoji = {"local": "🏗️", "claude": "🔍", "chatgpt": "⚙️"}
                print(f"{role_emoji[llm]} {response.model}:")
                if response.error:
                    print(f"❌ Error: {response.error}")
                else:
                    print(f"{response.response}\n")
        
        return responses
    
    def _build_role_context(self, other_responses):
        context = ""
        for llm, response in other_responses.items():
            if not response.error:
                context += f"{response.model}: {response.response[:200]}...\n\n"
        return context

class Conductor(ConversationMode):
    """The main conversational loop that assesses complexity and manages the workflow."""

    def run(self, prompt: str):
        print(f"🎶 Conductor received prompt: {prompt}")

        # 1. Complexity Assessment
        complexity_prompt = f"""
You are the Conductor of a multi-LLM framework. Your first job is to assess the complexity of the user's request. Classify the following prompt into one of three categories: 'simple_task', 'complex_task_internal', or 'complex_task_external'.

- 'simple_task': A request that can be handled by a single tool use.
- 'complex_task_internal': A task that requires multiple steps but can be handled autonomously by the AI team.
- 'complex_task_external': A task that is ambiguous, risky, or requires human approval for a multi-step plan.

User Prompt: "{prompt}"

Respond with ONLY the JSON classification. Example:
{{
  "classification": "simple_task",
  "reason": "The user is asking to list files, which is a single action."
}}
"""
        assessment_response = self.framework.ask_single(complexity_prompt, "local")
        
        try:
            assessment = json.loads(assessment_response.response)
            classification = assessment.get("classification")
            print(f"🧠 Conductor classified task as: {classification}")

            if classification == "simple_task":
                # 2a. Handle Simple Task
                return self.framework.ask_single(prompt, "local")

            elif classification == "complex_task_internal":
                # 2b. Handle Internal Complex Task
                print("🤖 Delegating to AI team for autonomous execution...")
                return self.framework.conversation_manager.start_conversation(prompt, 'orchestrated')

            elif classification == "complex_task_external":
                # 2c. Handle External Complex Task (Plan, Confirm, Execute)
                print("📝 This task requires a plan. Requesting plan from ChatGPT...")
                
                # 3. Plan Generation
                plan_prompt = f"Generate a step-by-step plan to achieve this goal: {prompt}. Respond with a JSON array of actions, where each action is a tool call."
                plan_response = self.framework.ask_single(plan_prompt, "chatgpt")
                
                try:
                    plan = json.loads(plan_response.response)
                    print("📋 Proposed Plan:")
                    for i, step in enumerate(plan, 1):
                        print(f"  {i}. {step['tool_name']}({step['parameters']})")

                    # 4. Plan Confirmation
                    if self.framework.request_user_approval("Do you approve this plan? (yes/no)"):
                        # 5. Plan Execution
                        print("✅ Plan approved. Executing...")
                        results = []
                        for step in plan:
                            result = self.framework.toolbox.use_tool(step['tool_name'], step['parameters'])
                            results.append(result)
                        return {"plan_results": results}
                    else:
                        print("❌ Plan rejected by user.")
                        return {"error": "Plan rejected"}
                except (json.JSONDecodeError, KeyError):
                    return {"error": "Failed to generate a valid plan."}

        except (json.JSONDecodeError, KeyError):
            print("⚠️ Could not classify task, defaulting to simple execution.")
            return self.framework.ask_single(prompt, "local")

class OrchestratedConversation(ConversationMode):
    """A structured conversation where one LLM can delegate tasks to another."""

    def run(self, prompt: str, worker_llm: str = "chatgpt", orchestrator_llm: str = "local"):
        print(f"🎼 Starting Orchestrated Conversation: {prompt}")
        print(f"👷 Worker: {worker_llm}, 🎻 Orchestrator: {orchestrator_llm}")
        print("=" * 60)

        # Initial prompt to the worker
        response = self.framework.ask_single(prompt, worker_llm)

        if response.error:
            print(f"❌ Initial worker response failed: {response.error}")
            return {"final_response": None, "error": response.error}

        # Check if the worker delegated a task
        try:
            json_start = response.response.find('{')
            json_end = response.response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response.response[json_start:json_end]
                parsed_json = json.loads(json_str)

                if "tool_use" in parsed_json and parsed_json["tool_use"]["tool_name"] == "delegate_task":
                    delegation = parsed_json["tool_use"]["parameters"]
                    target_llm = delegation.get("target_llm")
                    task_prompt = delegation.get("task_prompt")

                    if target_llm == orchestrator_llm:
                        print(f"🎻 Orchestrator ({orchestrator_llm}) is handling delegated task: {task_prompt}")
                        
                        # Orchestrator performs the task
                        orchestrator_response = self.framework.ask_single(task_prompt, orchestrator_llm)

                        if orchestrator_response.error:
                            print(f"❌ Orchestrator failed: {orchestrator_response.error}")
                            return {"final_response": None, "error": orchestrator_response.error}

                        # Worker receives the result and completes the original task
                        final_prompt = f"The delegated task '{task_prompt}' was completed by {orchestrator_llm} with the following result:\n\n{orchestrator_response.response}\n\nPlease use this information to complete your original task."
                        final_response = self.framework.ask_single(final_prompt, worker_llm)
                        
                        print(f"✅ Final response from {worker_llm}:")
                        print(final_response.response)
                        return {"final_response": final_response.response}

        except (json.JSONDecodeError, KeyError):
            # Not a delegation request, just a direct answer
            pass

        print(f"✅ Final response from {worker_llm}:")
        print(response.response)
        return {"final_response": response.response}

class FreeFormConversation(ConversationMode):
    """Creative, unstructured conversation for brainstorming"""
    
    def run(self, prompt, max_rounds=5):
        print(f"🌊 Starting Free-Form Brainstorming: {prompt}")
        print("💡 Creative mode - wild ideas welcome!")
        print("=" * 60)
        
        participants = ["chatgpt", "claude", "local"]  # Start with ChatGPT for creativity
        responses = {}
        
        for round_num in range(max_rounds):
            for i, llm in enumerate(participants):
                # Rotate starting participant each round
                current_llm = participants[(i + round_num) % len(participants)]
                
                # Build creative context
                context = self._build_creative_context(responses, round_num)
                
                creative_prompt = f"""
CREATIVE BRAINSTORMING SESSION

Topic: {prompt}

{context}

This is a creative brainstorming session! Think outside the box, propose wild ideas, 
build on others' creativity, and don't worry about practical constraints yet. 
What innovative, exciting, or unconventional ideas do you have?
"""
                
                response = self.framework.ask_single(creative_prompt, current_llm)
                responses[f"{current_llm}_round_{round_num}"] = response
                
                emoji_map = {"local": "🤖", "claude": "🧠", "chatgpt": "💬"}
                print(f"{emoji_map[current_llm]} {response.model}:")
                if response.error:
                    print(f"❌ Error: {response.error}")
                else:
                    print(f"{response.response}\n")
                
                # Brief pause between responses for readability
                if i < len(participants) - 1:
                    print("💭 ...")
        
        return responses
    
    def _build_creative_context(self, responses, current_round):
        if not responses:
            return "Let your creativity flow! No idea is too wild."
        
        context = "Creative ideas so far:\n"
        for key, response in responses.items():
            if not response.error:
                context += f"💡 {response.response[:100]}...\n"
        return context

class ProjectKnowledgeManager:
    """Manages project documentation and knowledge sync"""
    
    def __init__(self, project_dir="./", docs_dir="./docs"):
        self.project_dir = Path(project_dir).resolve()
        self.docs_dir = Path(docs_dir).resolve()
        self.fs = SafeFileSystem(project_dir)
        
    def update_knowledge_index(self, change_description: str, files_modified: List[str]):
        """Update the machine-readable knowledge index"""
        try:
            knowledge_path = self.docs_dir / "KNOWLEDGE_INDEX.json"
            
            if knowledge_path.exists():
                with open(knowledge_path, 'r') as f:
                    knowledge = json.load(f)
            else:
                knowledge = {"recent_changes": []}
            
            # Add new change
            change_entry = {
                "timestamp": datetime.now().isoformat(),
                "description": change_description,
                "files_modified": files_modified,
                "session": knowledge.get("project_info", {}).get("current_session", "unknown")
            }
            
            if "recent_changes" not in knowledge:
                knowledge["recent_changes"] = []
            
            knowledge["recent_changes"].append(change_entry)
            knowledge["project_info"]["last_updated"] = datetime.now().isoformat()
            
            # Keep only last 20 changes
            knowledge["recent_changes"] = knowledge["recent_changes"][-20:]
            
            with open(knowledge_path, 'w') as f:
                json.dump(knowledge, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not update knowledge index: {e}")
    
    def get_project_context(self) -> str:
        """Build comprehensive project context for LLMs"""
        context = "=== PROJECT CONTEXT ===\n\n"
        
        try:
            # Add current status
            status_path = self.docs_dir / "PROJECT_STATUS.md"
            if status_path.exists():
                context += "CURRENT STATUS:\n"
                context += self.fs.read_file(str(status_path.relative_to(self.project_dir)))
                context += "\n\n"
            
            # Add recent changes
            knowledge_path = self.docs_dir / "KNOWLEDGE_INDEX.json"
            if knowledge_path.exists():
                with open(knowledge_path, 'r') as f:
                    knowledge = json.load(f)
                
                context += "RECENT CHANGES:\n"
                for change in knowledge.get("recent_changes", [])[-5:]:
                    context += f"- {change['timestamp']}: {change['description']}\n"
                context += "\n"
                
                context += "CURRENT PRIORITIES:\n"
                for priority in knowledge.get("next_priorities", [])[:3]:
                    context += f"- Priority {priority['priority']}: {priority['description']}\n"
                context += "\n"
            
        except Exception as e:
            context += f"Warning: Could not load full context: {e}\n"
        
        return context

class ConversationModeManager:
    """Manages different conversation modes"""
    
    def __init__(self, framework):
        self.framework = framework
        self.modes = {
            'round_robin': RoundRobinConversation(framework),
            'moderated': ModeratedConversation(framework),
            'role_based': RoleBasedConversation(framework),
            'free_form': FreeFormConversation(framework),
            'orchestrated': OrchestratedConversation(framework),
            'conductor': Conductor(framework)
        }
    
    def auto_select_mode(self, prompt):
        """Intelligently choose conversation mode based on prompt"""
        prompt_lower = prompt.lower()
        
        # Role-based triggers
        if any(word in prompt_lower for word in ['design', 'architecture', 'implement', 'review']):
            return 'role_based'
        
        # Moderated triggers
        elif any(word in prompt_lower for word in ['analyze', 'systematic', 'plan', 'strategy']):
            return 'moderated'
        
        # Free-form triggers
        elif any(word in prompt_lower for word in ['brainstorm', 'creative', 'future', 'wild', 'innovative']):
            return 'free_form'
        
        # Default to round-robin
        else:
            return 'round_robin'
    
    def start_conversation(self, prompt, mode='auto', max_rounds=5):
        """Start a conversation in the specified mode"""
        if mode == 'auto':
            mode = self.auto_select_mode(prompt)
            print(f"🧠 Auto-selected mode: {mode.replace('_', '-')}")
        
        if mode not in self.modes:
            print(f"❌ Unknown mode: {mode}")
            return None
        
        return self.modes[mode].run(prompt, max_rounds)
    
    def list_modes(self):
        """List available conversation modes"""
        return {
            'round_robin': '🔄 Natural back-and-forth discussion',
            'moderated': '🎯 Structured, goal-oriented discussion',
            'role_based': '👥 Expert perspectives (Architect/Reviewer/Implementer)',
            'free_form': '🌊 Creative brainstorming',
            'orchestrated': '🎼 Automated delegation between LLMs'
        }

class MultiLLMFramework:
    """Simple orchestrator for multiple LLMs"""
    
    def __init__(self, config_file="llm_config.json"):
        self.config = self.load_config(config_file)
        self.conversation_log = []
        self.fs = SafeFileSystem()
        self.knowledge_manager = ProjectKnowledgeManager()
        self.scratchpad = SharedScratchpad()
        self.session_cost = 0.0
        self.conversation_manager = ConversationModeManager(self)
        self.toolbox = Toolbox(self)
        load_dotenv(dotenv_path=Path(__file__).parent.parent / "04_System" / ".env")
    
    def delegate_task(self, target_llm: str, task_prompt: str) -> str:
        """A tool to delegate a task to another LLM."""
        print(f"Delegating task to {target_llm}: {task_prompt}")
        response = self.ask_single(task_prompt, target_llm)
        if response.error:
            return f"Error during delegated task: {response.error}"
        return response.response

    def request_user_approval(self, reason: str) -> bool:
        """Request user approval for a specific action."""
        response = input(f"❓ {reason} [y/n]: ").lower()
        return response == 'y'

    def recall_memory(self, query: str) -> str:
        """Recall information from the conversation history."""
        log_file = self.config['memory']['log_file']
        if not os.path.exists(log_file):
            return "No conversation history found."

        with open(log_file, 'r') as f:
            log = json.load(f)

        # Simple text search for now, can be improved with semantic search
        relevant_entries = [
            entry for entry in log
            if query.lower() in entry.get("prompt", "").lower()
            or any(query.lower() in r.get("response", "").lower() for r in entry.get("responses", {}).values())
        ]

        if not relevant_entries:
            return f"No memories found matching '{query}'."

        # Return a summary of the most recent relevant entries
        summary = "Found relevant memories:\n"
        for entry in relevant_entries[-3:]: # Limit to last 3 for brevity
            summary += f"- At {entry['timestamp']}, the prompt was: '{entry['prompt'][:100]}...'\n"
            for model, resp in entry['responses'].items():
                if resp['error']:
                    summary += f"  - {model} responded with an error: {resp['error']}\n"
                else:
                    summary += f"  - {model} responded: '{resp['response'][:100]}...'\n"
        return summary
        
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
                usage = result.get('usage', {})
                cost = self._calculate_cost("gpt-4o", usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0))
                self.session_cost += cost
                return LLMResponse(
                    model="ChatGPT-4o",
                    response=result['choices'][0]['message']['content'],
                    timestamp=datetime.now().isoformat(),
                    tokens_used=usage.get('total_tokens'),
                    cost=cost,
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
                usage = result.get('usage', {})
                cost = self._calculate_cost("claude-3-5-sonnet-20241022", usage.get('input_tokens', 0), usage.get('output_tokens', 0))
                self.session_cost += cost
                return LLMResponse(
                    model="Claude-3.5-Sonnet",
                    response=result['content'][0]['text'],
                    timestamp=datetime.now().isoformat(),
                    tokens_used=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                    cost=cost,
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
        
        # Automatically inject project context
        project_context = self.knowledge_manager.get_project_context()
        full_context = f"{project_context}\n\n{context}"

        for model in models:
            print(f"  📡 Calling {model}...")
            
            if model == "chatgpt":
                responses["chatgpt"] = self.call_openai(prompt, full_context)
            elif model == "claude":
                responses["claude"] = self.call_claude(prompt, full_context)
            elif model == "local":
                responses["local"] = self.call_local_llm(prompt, full_context)
            
            # Show status
            if responses[model].error:
                print(f"  ❌ {model} failed: {responses[model].error}")
            else:
                print(f"  ✅ {model} responded ({responses[model].response_time:.1f}s)")
        
        # Log the conversation
        self.log_conversation(prompt, full_context, responses)
        
        return responses
    
    def ask_single(self, prompt: str, model: str = "local", context: str = "", max_tool_uses: int = 5) -> LLMResponse:
        """Ask a single LLM, with support for tool use."""
        print(f"🤖 Asking {model}: {prompt[:100]}...")

        # Add tool instructions to the context
        full_context = f"{context}\n\n{self.toolbox.get_tool_prompt()}"
        previous_tool_calls = []

        for i in range(max_tool_uses):
            if model == "chatgpt":
                response = self.call_openai(prompt, full_context)
            elif model == "claude":
                response = self.call_claude(prompt, full_context)
            elif model == "local":
                response = self.call_local_llm(prompt, full_context)
            else:
                raise ValueError(f"Unknown model: {model}")

            if response.error:
                return response

            # Check for tool use request
            try:
                # A simple way to find a JSON block
                json_start = response.response.find('{')
                json_end = response.response.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = response.response[json_start:json_end]
                    parsed_json = json.loads(json_str)
                    
                    if "tool_use" in parsed_json:
                        tool_request = parsed_json["tool_use"]
                        tool_name = tool_request.get("tool_name")
                        parameters = tool_request.get("parameters", {})
                        
                        # Detect repetitive tool calls
                        if (tool_name, parameters) in previous_tool_calls:
                            response.response = "Detected a repetitive tool call loop. Aborting."
                            response.error = "Repetitive tool call"
                            return response
                        previous_tool_calls.append((tool_name, parameters))

                        print(f"🛠️  Using tool: {tool_name} with params: {parameters}")
                        
                        # Execute the tool
                        tool_result = self.toolbox.use_tool(tool_name, parameters)
                        
                        # Formulate the next prompt with a summary of the tool's result
                        tool_result_summary = f"Tool '{tool_name}' executed successfully."
                        if isinstance(tool_result, str) and len(tool_result) > 200:
                            tool_result_summary += f" Result preview: {tool_result[:200]}..."
                        else:
                            tool_result_summary += f" Result: {tool_result}"

                        prompt = f"The tool '{tool_name}' was used and returned: '{tool_result_summary}'. If you have enough information, please provide your final answer. Otherwise, you may use another tool."
                        full_context += f"\n\nPrevious tool use:\n{json.dumps(parsed_json, indent=2)}\nResult: {tool_result_summary}"
                        continue # Go to the next iteration of the loop
            except (json.JSONDecodeError, KeyError):
                # Not a valid tool request, so it's a final answer
                pass

            # If no tool was used, or after the last tool use, return the response
            self.log_conversation(prompt, context, {model: response})
            return response

        # Reached max tool uses
        return LLMResponse(
            model=model,
            response="Reached maximum number of tool uses in a single turn.",
            timestamp=datetime.now().isoformat(),
            error="Max tool uses exceeded"
        )
    
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
    
    # === SELF-IMPROVEMENT CAPABILITIES ===
    
    def analyze_self(self, target_file: str = "MultiLLM_Framework.py") -> Dict[str, LLMResponse]:
        """Let the framework analyze its own code"""
        print(f"🔍 Analyzing {target_file}...")
        
        try:
            # Read the current code
            source_code = self.fs.read_file(target_file)
            
            # Get project context
            context = self.knowledge_manager.get_project_context()
            
            # Prepare analysis prompts for each LLM
            analyses = {}
            
            # Local LLM: Architecture and performance analysis
            local_prompt = f"""
            {context}
            
            ROLE: Architecture and Performance Analyst
            
            Analyze this Python code for architecture and performance improvements:
            
            ```python
            {source_code}
            ```
            
            Focus on:
            1. Code architecture and design patterns
            2. Performance optimization opportunities
            3. Memory usage and efficiency
            4. Scalability considerations
            
            Provide specific, actionable recommendations.
            """
            
            analyses["local"] = self.ask_single(local_prompt, "local")
            
            # Claude: Code quality and best practices
            claude_prompt = f"""
            {context}
            
            ROLE: Code Quality and Best Practices Reviewer
            
            Review this Python code for quality and best practices:
            
            ```python
            {source_code}
            ```
            
            Focus on:
            1. Code quality and readability
            2. Python best practices and conventions
            3. Error handling and robustness
            4. Security considerations
            5. Documentation and maintainability
            
            Provide specific improvement suggestions with examples.
            """
            
            analyses["claude"] = self.ask_single(claude_prompt, "claude")
            
            # ChatGPT: Feature suggestions and creative improvements
            chatgpt_prompt = f"""
            {context}
            
            ROLE: Feature Development and Creative Problem Solver
            
            Analyze this Python code for feature enhancements and creative improvements:
            
            ```python
            {source_code}
            ```
            
            Focus on:
            1. New feature opportunities
            2. User experience improvements
            3. Integration possibilities
            4. Creative solutions to current limitations
            5. Future-proofing considerations
            
            Suggest specific features and improvements with implementation ideas.
            """
            
            analyses["chatgpt"] = self.ask_single(chatgpt_prompt, "chatgpt")
            
            # Log this analysis
            self.knowledge_manager.update_knowledge_index(
                f"Self-analysis of {target_file} completed",
                [target_file]
            )
            
            return analyses
            
        except Exception as e:
            print(f"❌ Error during self-analysis: {e}")
            return {}
    
    def collaborative_improvement(self, target_file: str, improvement_goal: str) -> bool:
        """LLMs collaborate to improve code"""
        print(f"🤖 Starting collaborative improvement: {improvement_goal}")
        
        try:
            # Step 1: Get current project context
            context = self.knowledge_manager.get_project_context()
            
            # Step 2: All LLMs analyze current code
            print("📊 Phase 1: Multi-LLM Analysis...")
            analyses = self.analyze_self(target_file)
            
            if not analyses:
                print("❌ Analysis failed, cannot proceed with improvement")
                return False
            
            # Step 3: Synthesize improvement plan
            print("🧠 Phase 2: Synthesizing Improvement Plan...")
            synthesis_prompt = f"""
            {context}
            
            GOAL: {improvement_goal}
            
            ANALYSIS RESULTS:
            
            Local LLM (Architecture/Performance): {analyses.get('local', {}).response if analyses.get('local') else 'No response'}
            
            Claude (Code Quality/Best Practices): {analyses.get('claude', {}).response if analyses.get('claude') else 'No response'}
            
            ChatGPT (Features/Creative Solutions): {analyses.get('chatgpt', {}).response if analyses.get('chatgpt') else 'No response'}
            
            Based on these analyses, create a specific, detailed implementation plan for: {improvement_goal}
            
            The plan should:
            1. Incorporate the best ideas from all three analyses
            2. Be technically feasible and safe
            3. Maintain backward compatibility
            4. Include specific code changes needed
            5. Consider potential risks and mitigation strategies
            
            Provide a clear, step-by-step implementation plan.
            """
            
            plan_response = self.ask_single(synthesis_prompt, "claude")
            
            if plan_response.error:
                print(f"❌ Plan synthesis failed: {plan_response.error}")
                return False
            
            print("📋 Improvement Plan:")
            print(plan_response.response)
            
            # Step 4: Generate implementation
            print("⚙️  Phase 3: Generating Implementation...")
            current_code = self.fs.read_file(target_file)
            
            impl_prompt = f"""
            {context}
            
            IMPLEMENTATION PLAN:
            {plan_response.response}
            
            CURRENT CODE:
            ```python
            {current_code}
            ```
            
            Generate the improved code that implements this plan.
            
            REQUIREMENTS:
            1. Provide ONLY the complete, working Python code
            2. Maintain all existing functionality
            3. Add the improvements as specified in the plan
            4. Ensure proper error handling
            5. Include appropriate comments for new code
            
            Return the complete file content, ready to save.
            """
            
            impl_response = self.ask_single(impl_prompt, "chatgpt")
            
            if impl_response.error:
                print(f"❌ Implementation generation failed: {impl_response.error}")
                return False
            
            # Step 5: Review and validate
            print("🔍 Phase 4: Code Review and Validation...")
            review_prompt = f"""
            {context}
            
            ORIGINAL GOAL: {improvement_goal}
            
            Review this improved code for correctness and safety:
            
            ```python
            {impl_response.response}
            ```
            
            Check for:
            1. Syntax errors
            2. Logic issues
            3. Security concerns
            4. Compatibility with existing functionality
            5. Whether it actually achieves the improvement goal
            
            Respond with either:
            - "APPROVED: [brief reason why it's good]"
            - "REJECTED: [specific issues that need to be fixed]"
            """
            
            review_response = self.ask_single(review_prompt, "local")
            
            if review_response.error:
                print(f"❌ Code review failed: {review_response.error}")
                return False
            
            print("📝 Review Result:")
            print(review_response.response)
            
            if "APPROVED" in review_response.response.upper():
                # Apply the improvement
                print("✅ Applying collaborative improvement...")
                
                # Create backup first
                backup_path = self.fs.backup_file(target_file)
                print(f"📦 Backup created: {backup_path}")
                
                # Write the improved code
                self.fs.write_file(target_file, impl_response.response, backup=False)
                
                # Update knowledge index
                self.knowledge_manager.update_knowledge_index(
                    f"Collaborative improvement applied: {improvement_goal}",
                    [target_file]
                )
                
                print("🎉 Collaborative improvement successfully applied!")
                return True
            else:
                print(f"❌ Improvement rejected by review: {review_response.response}")
                return False
                
        except Exception as e:
            print(f"❌ Error during collaborative improvement: {e}")
            return False
    
    def self_improve(self, improvement_description: str, target_file: str = "MultiLLM_Framework.py") -> bool:
        """Simple self-improvement interface"""
        return self.collaborative_improvement(target_file, improvement_description)
    
    def validate_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """List available backups"""
        try:
            backup_files = self.fs.list_files("backups/*")
            return sorted(backup_files, reverse=True)  # Most recent first
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
            return []
    
    def restore_backup(self, backup_file: str, target_file: str = "MultiLLM_Framework.py") -> bool:
        """Restore from a backup"""
        try:
            backup_content = self.fs.read_file(f"backups/{backup_file}")
            self.fs.write_file(target_file, backup_content, backup=True)
            
            self.knowledge_manager.update_knowledge_index(
                f"Restored {target_file} from backup {backup_file}",
                [target_file]
            )
            
            print(f"✅ Restored {target_file} from {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False
    
    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of an API call."""
        pricing = self.config.get("pricing", {}).get(model_name)
        if not pricing:
            return 0.0
        
        input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0)
        return input_cost + output_cost

    def interactive_mode(self):
        """Interactive CLI mode"""
        print("🧠 Kurt's Self-Improving Multi-LLM Framework")
        print("🤖 LLM Commands:")
        print("  'all <prompt>' - Ask all LLMs")
        print("  'local <prompt>' - Ask local LLM")
        print("  'claude <prompt>' - Ask Claude")
        print("  'chatgpt <prompt>' - Ask ChatGPT")
        print("💬 Conversation Commands:")
        print("  'discuss <prompt>' - Auto-select conversation mode")
        print("  'discuss:round-robin <prompt>' - Natural back-and-forth")
        print("  'discuss:moderated <prompt>' - Structured discussion")
        print("  'discuss:roles <prompt>' - Expert role-based discussion")
        print("  'discuss:freeform <prompt>' - Creative brainstorming")
        print("  'modes' - List conversation modes")
        print("🔧 Self-Improvement Commands:")
        print("  'analyze' - Analyze current code")
        print("  'improve <description>' - Collaborative improvement")
        print("  'backups' - List available backups")
        print("  'restore <backup>' - Restore from backup")
        print("  'status' - Show project status")
        print("  'quit' - Exit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💭 > ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'cost':
                    print(f"💰 Session cost so far: ${self.session_cost:.4f}")
                    continue

                # The Conductor now handles all other input
                self.conversation_manager.start_conversation(user_input, 'conductor')

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
