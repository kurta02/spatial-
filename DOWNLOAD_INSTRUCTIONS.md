# Spatial Constellation System - Setup Instructions

This guide will help you set up the complete Multi-AI Collaboration System with Manus's advanced agent coordination.

## Quick Start

1. **Download and Setup:**
   ```bash
   # Navigate to your desired directory
   cd /home/kurt/
   
   # If you haven't already cloned the repository:
   git clone https://github.com/kurta02/spatial-.git spatial-constellation-system
   cd spatial-constellation-system
   ```

2. **Install Dependencies:**
   ```bash
   # Install Python requirements
   pip install -r requirements.txt
   
   # Or install manually:
   pip install requests flask sqlite3 anthropic openai
   ```

3. **Setup Ollama (Local Models):**
   ```bash
   # Install Ollama if not already installed
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull recommended models
   ollama pull llama3:latest
   ollama pull mistral:latest
   ollama pull dolphin-mixtral:latest
   ```

4. **Initialize the System:**
   ```bash
   # Run the startup script
   python scripts/start_system.py
   ```

## File Structure Overview

```
spatial-constellation-system/
├── README.md                           # Project overview
├── DOWNLOAD_INSTRUCTIONS.md            # This file
├── AI_Execution_Protocol.md           # AI agent execution rules
├── codex_log.md                       # Codex execution tracking
├── HALT_marker_readme.md              # AI agent control system
├── src/                               # Core system files
│   ├── core/
│   │   ├── local_agent_coordinator.py  # Manus's agent coordination
│   │   ├── agents.py                  # Agent orchestration
│   │   └── brain.py                   # Multi-LLM coordinator
│   └── memory/
│       └── persistent_memory.py        # Manus's memory system
├── config/
│   ├── agents.json                    # Agent configuration
│   └── config.py                      # System configuration
├── scripts/
│   ├── start_system.py                # System startup
│   ├── start_system.sh                # System startup (bash)
│   └── stop_system.sh                 # System shutdown
├── docs/                              # Documentation
├── tests/                             # Test suites
└── data/                              # Runtime data and logs
```

## System Components

### 1. Local Agent Coordinator (Manus's Design)
**File:** `src/core/local_agent_coordinator.py`
- Cost-optimized multi-AI coordination
- Local-first approach (uses Ollama)
- Strategic API model delegation
- Task complexity analysis and routing

### 2. Persistent Memory System (Manus's Design)  
**File:** `src/memory/persistent_memory.py`
- Robust long-term memory with SQLite backend
- Automatic deduplication and consolidation
- Git integration for version control
- Thread-safe operations

### 3. Agent Configuration
**File:** `config/agents.json`
- Comprehensive agent definitions
- Cost optimization settings
- Task routing configuration
- Safety and validation settings

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```bash
# AI API Keys (optional - system works locally without these)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
DATABASE_URL=sqlite:///data/spatial_constellation.db

# System Settings
LOG_LEVEL=INFO
SESSION_STATE_PATH=data/session_state.json
```

### Agent Configuration
Edit `config/agents.json` to customize:
- Model endpoints and parameters
- Task routing logic
- Cost optimization settings
- Safety and validation requirements

## Usage Examples

### Basic Task Execution
```python
from src.core.local_agent_coordinator import LocalAgentCoordinator

# Initialize coordinator
coordinator = LocalAgentCoordinator()

# Create and execute a task
task_id = coordinator.create_task("Analyze this code for potential issues")
result = coordinator.execute_task(task_id)

print(f"Task result: {result}")
```

### Memory System Usage
```python
from src.memory.persistent_memory import PersistentMemory

# Initialize memory
memory = PersistentMemory()

# Store information
memory.store_memory(
    component="analysis",
    entry_type="code_review",
    content="Found 3 potential security issues in authentication module",
    importance=8
)

# Retrieve memories
recent_memories = memory.retrieve_memory(component="analysis", limit=10)
```

### System Status Check
```python
# Check overall system status
status = coordinator.get_status()
print(f"Active tasks: {status['active_tasks']}")
print(f"Total cost: ${status['total_cost']:.4f}")
print(f"Local tasks completed: {status['local_tasks_completed']}")

# Check memory statistics
memory_stats = memory.get_memory_stats()
print(f"Total memories: {memory_stats['total_entries']}")
```

## Advanced Features

### Cost Optimization
The system prioritizes local models (free) and only uses API models when necessary:
- **Simple tasks** → Local primary model
- **Moderate tasks** → Local model with validation
- **Complex tasks** → API model with local validation
- **Critical tasks** → API model with human approval

### Persistent Memory
All interactions are automatically stored with:
- Deduplication to prevent redundant storage
- Importance scoring for memory prioritization
- Automatic consolidation of old memories
- Git backup integration

### Multi-Agent Validation
Tasks can be validated by multiple agents:
- Primary execution by most appropriate agent
- Secondary validation by different agent
- Escalation when validation fails
- Human approval for critical operations

## Troubleshooting

### Ollama Not Available
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Pull required models
ollama pull llama3:latest
ollama pull mistral:latest
```

### Memory System Issues
```bash
# Check database
sqlite3 data/persistent_memory.db ".tables"

# View recent memories
sqlite3 data/persistent_memory.db "SELECT * FROM memory_entries ORDER BY created_at DESC LIMIT 5;"
```

### Agent Coordination Issues
```python
# Check agent availability
coordinator = LocalAgentCoordinator()
status = coordinator._check_agent_availability()
print(f"Available agents: {status}")
```

## Integration with Existing Tools

This system integrates with your existing spatial constellation tools:
- **Brain System** (`core/brain.py`) - Multi-LLM coordination
- **Flask API** (`api/app.py`) - HTTP interface
- **Conversational CLI** (`core/conversational_cli.py`) - Command line interface
- **Review System** (`api/review_undo_system.py`) - Change management

## Next Steps

1. **Run the startup script** to initialize everything
2. **Test with simple tasks** to verify functionality
3. **Configure API keys** for advanced features
4. **Customize agent routing** in `config/agents.json`
5. **Set up automatic backups** for persistent memory

## Support

- Check `data/logs/` for detailed system logs
- Review `codex_log.md` for AI agent execution history
- Consult `MASTER SYSTEM DOCUMENTATION.md` for comprehensive reference
- Use `HALT_marker_readme.md` for AI agent control

The system is designed to work entirely locally if needed, with optional cloud AI integration for complex tasks.