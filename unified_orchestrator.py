#!/usr/bin/env python3
"""
Unified Orchestrator - Master coordination system for Kurt's AI ecosystem
Integrates all components with persistent memory everywhere
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import signal
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import threading
from contextlib import contextmanager

# Add spatial-ai to path
sys.path.insert(0, '/home/kurt/spatial-ai')

from persistent_memory_core import get_memory_core, store_memory, retrieve_memory, store_session_state, retrieve_session_state
from dotenv import load_dotenv

# Load unified configuration
load_dotenv("/home/kurt/spatial-ai/.env")

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedOrchestrator:
    """Master orchestrator for all AI components with persistent memory"""
    
    def __init__(self):
        self.memory = get_memory_core()
        self.session_id = self.memory.start_new_session("orchestrator")
        self.components = {}
        self.processes = {}
        self.is_running = False
        self._shutdown_event = threading.Event()
        
        # Configuration from environment
        self.brain_system_path = os.getenv("BRAIN_SYSTEM_PATH", "/home/kurt/Assistant/coordinator")
        self.multi_llm_path = os.getenv("MULTI_LLM_PATH", "/home/kurt/whisper.cpp")
        self.rag_vault_path = os.getenv("RAG_VAULT_PATH", "/home/kurt/Documents/KurtVault")
        self.brain_api_port = int(os.getenv("BRAIN_API_PORT", "8888"))
        
        # Component registry
        self.component_registry = {
            "brain_system": {
                "path": self.brain_system_path,
                "script": "brain.py",
                "type": "api_server",
                "port": self.brain_api_port,
                "enabled": True
            },
            "multi_llm": {
                "path": self.multi_llm_path,
                "script": "MultiLLM_Framework.py",
                "type": "interactive",
                "enabled": True
            },
            "whisper_cpp": {
                "path": "/home/kurt/whisper.cpp",
                "binary": "build/bin/whisper-cli",
                "type": "binary",
                "enabled": os.getenv("ENABLE_SPEECH_INPUT", "true").lower() == "true"
            },
            "rag_system": {
                "path": "/home/kurt",
                "script": "ask_rag_interactive.py",
                "type": "interactive",
                "enabled": os.getenv("ENABLE_VECTOR_SEARCH", "true").lower() == "true"
            }
        }
        
        # Initialize memory tracking
        self._init_memory_tracking()
        
        store_memory("orchestrator", "system_start", f"Unified orchestrator initialized - Session: {self.session_id}")
        logger.info(f"Unified Orchestrator initialized - Session: {self.session_id}")
    
    def _init_memory_tracking(self):
        """Initialize persistent memory tracking for all components"""
        # Store current configuration
        config_state = {
            "session_id": self.session_id,
            "components": self.component_registry,
            "paths": {
                "brain_system": self.brain_system_path,
                "multi_llm": self.multi_llm_path,
                "rag_vault": self.rag_vault_path
            },
            "initialized_at": datetime.now().isoformat()
        }
        
        store_session_state("orchestrator", config_state)
        
        # Initialize component states
        for component_name in self.component_registry:
            component_state = retrieve_session_state(component_name)
            if component_state is None:
                store_session_state(component_name, {
                    "status": "initialized",
                    "last_seen": datetime.now().isoformat(),
                    "memory_enabled": True
                })
    
    def start_component(self, component_name: str) -> bool:
        """Start a component with memory tracking"""
        if component_name not in self.component_registry:
            logger.error(f"Unknown component: {component_name}")
            return False
        
        component = self.component_registry[component_name]
        
        if not component.get("enabled", True):
            logger.info(f"Component {component_name} is disabled")
            return False
        
        try:
            component_path = Path(component["path"])
            
            if component["type"] == "api_server":
                # Start brain system API server
                cmd = [sys.executable, component["script"]]
                process = subprocess.Popen(
                    cmd,
                    cwd=component_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=self._get_component_env(component_name)
                )
                
                self.processes[component_name] = process
                logger.info(f"Started {component_name} API server (PID: {process.pid})")
                
            elif component["type"] == "interactive":
                # Interactive components managed separately
                logger.info(f"Interactive component {component_name} registered")
                
            elif component["type"] == "binary":
                # Binary components available on-demand
                logger.info(f"Binary component {component_name} available")
            
            # Update component state
            store_session_state(component_name, {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "process_id": self.processes.get(component_name, {}).get("pid") if component_name in self.processes else None
            })
            
            store_memory("orchestrator", "component_start", f"Started component: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start component {component_name}: {e}")
            store_memory("orchestrator", "component_error", f"Failed to start {component_name}: {str(e)}")
            return False
    
    def stop_component(self, component_name: str) -> bool:
        """Stop a component with memory tracking"""
        if component_name in self.processes:
            process = self.processes[component_name]
            try:
                process.terminate()
                process.wait(timeout=5)
                del self.processes[component_name]
                
                # Update component state
                store_session_state(component_name, {
                    "status": "stopped",
                    "stopped_at": datetime.now().isoformat()
                })
                
                store_memory("orchestrator", "component_stop", f"Stopped component: {component_name}")
                logger.info(f"Stopped component: {component_name}")
                return True
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                del self.processes[component_name]
                logger.warning(f"Force killed component: {component_name}")
                return True
        
        return False
    
    def _get_component_env(self, component_name: str) -> Dict[str, str]:
        """Get environment variables for a component"""
        env = os.environ.copy()
        
        # Add unified config path
        env["UNIFIED_CONFIG_PATH"] = "/home/kurt/spatial-ai/.env"
        env["PERSISTENT_MEMORY_ENABLED"] = "true"
        env["SESSION_ID"] = self.session_id
        env["COMPONENT_NAME"] = component_name
        
        # Add API keys
        env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
        env["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")
        
        return env
    
    def execute_command(self, component_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command on a component with memory tracking"""
        start_time = datetime.now()
        
        # Store command execution
        store_memory("orchestrator", "command_execution", 
                    f"Executing command on {component_name}: {command}",
                    context=f"session_{self.session_id}",
                    metadata={"component": component_name, "command": command, "kwargs": kwargs})
        
        try:
            result = self._execute_component_command(component_name, command, **kwargs)
            
            # Store result
            execution_time = (datetime.now() - start_time).total_seconds()
            store_memory("orchestrator", "command_result",
                        f"Command completed on {component_name}: {command}",
                        context=f"session_{self.session_id}",
                        metadata={"component": component_name, "command": command, 
                                "result": result, "execution_time": execution_time})
            
            return result
            
        except Exception as e:
            # Store error
            store_memory("orchestrator", "command_error",
                        f"Command failed on {component_name}: {command} - {str(e)}",
                        context=f"session_{self.session_id}",
                        metadata={"component": component_name, "command": command, "error": str(e)})
            raise
    
    def _execute_component_command(self, component_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command on specific component"""
        if component_name == "brain_system":
            return self._execute_brain_command(command, **kwargs)
        elif component_name == "multi_llm":
            return self._execute_multi_llm_command(command, **kwargs)
        elif component_name == "whisper_cpp":
            return self._execute_whisper_command(command, **kwargs)
        elif component_name == "rag_system":
            return self._execute_rag_command(command, **kwargs)
        else:
            raise ValueError(f"Unknown component: {component_name}")
    
    def _execute_brain_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command on brain system"""
        # This would integrate with the brain.py API
        logger.info(f"Executing brain command: {command}")
        return {"status": "success", "component": "brain_system", "command": command}
    
    def _execute_multi_llm_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command on MultiLLM framework"""
        logger.info(f"Executing MultiLLM command: {command}")
        return {"status": "success", "component": "multi_llm", "command": command}
    
    def _execute_whisper_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute whisper.cpp command"""
        logger.info(f"Executing whisper command: {command}")
        return {"status": "success", "component": "whisper_cpp", "command": command}
    
    def _execute_rag_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute RAG system command"""
        logger.info(f"Executing RAG command: {command}")
        return {"status": "success", "component": "rag_system", "command": command}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status with memory context"""
        status = {
            "session_id": self.session_id,
            "orchestrator_uptime": datetime.now().isoformat(),
            "components": {},
            "processes": {},
            "memory_stats": self.memory.get_memory_stats(),
            "recent_activity": retrieve_memory("orchestrator", limit=10)
        }
        
        # Component status
        for component_name in self.component_registry:
            component_state = retrieve_session_state(component_name)
            status["components"][component_name] = {
                "enabled": self.component_registry[component_name].get("enabled", True),
                "state": component_state,
                "process_active": component_name in self.processes
            }
        
        # Process status
        for name, process in self.processes.items():
            status["processes"][name] = {
                "pid": process.pid,
                "running": process.poll() is None
            }
        
        return status
    
    def consolidate_memory(self) -> Dict[str, Any]:
        """Consolidate memory across all components"""
        result = self.memory.consolidate_memory()
        
        store_memory("orchestrator", "memory_consolidation",
                    f"Memory consolidation completed: {result}")
        
        return result
    
    def start_all_components(self) -> Dict[str, bool]:
        """Start all enabled components"""
        results = {}
        
        for component_name in self.component_registry:
            if self.component_registry[component_name].get("enabled", True):
                results[component_name] = self.start_component(component_name)
        
        self.is_running = True
        store_memory("orchestrator", "system_start", "All components started")
        
        return results
    
    def stop_all_components(self) -> Dict[str, bool]:
        """Stop all components"""
        results = {}
        
        for component_name in list(self.processes.keys()):
            results[component_name] = self.stop_component(component_name)
        
        self.is_running = False
        store_memory("orchestrator", "system_stop", "All components stopped")
        
        return results
    
    def run_interactive_session(self):
        """Run an interactive session with persistent memory"""
        print(f"🧠 Unified AI Orchestrator - Session: {self.session_id}")
        print("Commands: start, stop, status, exec, memory, consolidate, quit")
        print("Use 'help' for detailed command information")
        
        store_memory("orchestrator", "interactive_start", "Interactive session started")
        
        while not self._shutdown_event.is_set():
            try:
                user_input = input("\n🤖 > ").strip()
                
                if not user_input:
                    continue
                
                # Store user input
                store_memory("orchestrator", "user_input", user_input, context="interactive")
                
                parts = user_input.split()
                command = parts[0].lower()
                
                if command == "quit" or command == "exit":
                    break
                elif command == "help":
                    self._show_help()
                elif command == "start":
                    if len(parts) > 1:
                        result = self.start_component(parts[1])
                        print(f"Start {parts[1]}: {'Success' if result else 'Failed'}")
                    else:
                        result = self.start_all_components()
                        print(f"Started components: {result}")
                elif command == "stop":
                    if len(parts) > 1:
                        result = self.stop_component(parts[1])
                        print(f"Stop {parts[1]}: {'Success' if result else 'Failed'}")
                    else:
                        result = self.stop_all_components()
                        print(f"Stopped components: {result}")
                elif command == "status":
                    status = self.get_system_status()
                    print(json.dumps(status, indent=2))
                elif command == "exec":
                    if len(parts) >= 3:
                        component = parts[1]
                        cmd = " ".join(parts[2:])
                        try:
                            result = self.execute_command(component, cmd)
                            print(f"Result: {result}")
                        except Exception as e:
                            print(f"Error: {e}")
                    else:
                        print("Usage: exec <component> <command>")
                elif command == "memory":
                    if len(parts) > 1 and parts[1] == "stats":
                        stats = self.memory.get_memory_stats()
                        print(json.dumps(stats, indent=2))
                    else:
                        entries = retrieve_memory("orchestrator", limit=5)
                        for entry in entries:
                            print(f"  {entry['created_at']}: {entry['content']}")
                elif command == "consolidate":
                    result = self.consolidate_memory()
                    print(f"Consolidation result: {result}")
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                store_memory("orchestrator", "error", f"Interactive error: {str(e)}")
        
        store_memory("orchestrator", "interactive_end", "Interactive session ended")
        print("Session ended. Goodbye!")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
        🧠 Unified AI Orchestrator Commands:
        
        start [component]    - Start all components or specific component
        stop [component]     - Stop all components or specific component
        status              - Show system status
        exec <comp> <cmd>   - Execute command on component
        memory [stats]      - Show recent memory or stats
        consolidate         - Consolidate memory
        help                - Show this help
        quit/exit           - Exit orchestrator
        
        Components: brain_system, multi_llm, whisper_cpp, rag_system
        """
        print(help_text)
    
    def shutdown(self):
        """Shutdown orchestrator"""
        self._shutdown_event.set()
        self.stop_all_components()
        store_memory("orchestrator", "shutdown", "Orchestrator shutdown complete")
        logger.info("Orchestrator shutdown complete")

def signal_handler(signum, frame, orchestrator):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    orchestrator.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    orchestrator = UnifiedOrchestrator()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, orchestrator))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, orchestrator))
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "daemon":
            # Run as daemon
            orchestrator.start_all_components()
            while orchestrator.is_running:
                time.sleep(1)
        else:
            # Run interactive session
            orchestrator.run_interactive_session()
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        store_memory("orchestrator", "fatal_error", f"Fatal error: {str(e)}")
    finally:
        orchestrator.shutdown()