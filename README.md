# Spatial Constellation System

Kurt's Spatial AI Operating System - A unified multi-LLM orchestration platform with persistent memory and collaborative intelligence.

## Overview

The Spatial Constellation System is an advanced AI orchestration platform that manages multiple Language Learning Models (LLMs) with persistent memory, file operations, and collaborative workflows. It provides a conversational CLI interface for interacting with ChatGPT, Claude Code, and Local LLMs while maintaining context across sessions.

## Key Features

- **Multi-LLM Orchestration**: Seamlessly work with ChatGPT, Claude Code, and Local LLMs
- **Persistent Memory**: PostgreSQL-based memory system with vector similarity search
- **File System Integration**: Secure file operations with permission-based access control
- **Conversational CLI**: Natural language interface for AI interactions
- **Collaborative Workflows**: Multi-model coordination for complex tasks
- **Session Management**: Context preservation across interactions
- **Review/Undo System**: Flask API wrapper with operation tracking

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Conversational│    │     Brain        │    │   Persistent    │
│       CLI       │◄──►│    System        │◄──►│    Memory       │
│                 │    │                  │    │  (PostgreSQL)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Flask API      │    │   File System    │    │   Vector Store  │
│   Wrapper       │    │   Operations     │    │   (pgvector)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- OpenAI API key
- Anthropic API key
- Local LLM setup (Ollama/llama.cpp)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd spatial-constellation-repo
```

2. Set up virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

4. Initialize database:
```bash
python scripts/setup_database.py
```

5. Start the system:
```bash
./scripts/start_system.sh
```

### Basic Usage

Launch the conversational CLI:
```bash
chat
```

Commands:
- `hello world` - Send to ChatGPT (default)
- `claude analyze this code` - Send to Claude Code
- `local write notes.txt My notes` - Send to Local LLM (can write files)
- `all what is quantum physics?` - Ask all three models
- `memory search keyword` - Search conversation history
- `system status` - Show system status

## File Structure

```
spatial-constellation-repo/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
├── .gitignore               # Git ignore patterns
├── core/                    # Core system components
│   ├── brain.py            # Multi-LLM orchestrator
│   ├── persistent_memory.py # Memory management
│   └── conversational_cli.py # CLI interface
├── api/                     # Flask API wrapper
│   ├── app.py              # Main Flask application
│   ├── review_undo.py      # Review/undo system
│   └── enforcement.py      # AI enforcement framework
├── config/                  # Configuration files
│   ├── config.py           # Main configuration
│   └── llm_config.json     # LLM model configurations
├── scripts/                 # Utility scripts
│   ├── setup_database.py   # Database initialization
│   ├── start_system.sh     # System startup
│   └── migration_tools.py  # Migration utilities
├── tests/                   # Test suite
│   ├── test_brain.py       # Brain system tests
│   ├── test_memory.py      # Memory system tests
│   └── test_cli.py         # CLI tests
├── docs/                    # Documentation
│   ├── user-manual.md      # Complete user manual
│   ├── migration-log.md    # Migration progress log
│   └── architecture.md     # System architecture
└── data/                    # Data directory
    ├── workspace/          # LLM workspace
    └── logs/               # System logs
```

## System Commands

The system provides several PATH-accessible commands:

- `chat` - Launch conversational CLI
- `user-guide` - Access system documentation
- `ug status` - Quick system status check

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Migration Status

The system is currently in migration from SQLite to PostgreSQL architecture:

- ✅ Phase 1: PostgreSQL persistent memory implementation
- ✅ Phase 2: Conversational CLI with multi-LLM support
- ✅ Phase 3: Review/undo system with Flask API
- 🔄 Phase 4: Enhanced collaboration architecture (in progress)
- ⏳ Phase 5: Frontend integration (planned)

### Contributing

1. Create feature branch from master
2. Implement changes with tests
3. Update documentation
4. Submit pull request

## Configuration

### Environment Variables

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=spatial_constellation
POSTGRES_USER=spatial_ai
POSTGRES_PASSWORD=your_password

# System Configuration
LOG_LEVEL=INFO
WORKSPACE_PATH=/path/to/workspace
```

### LLM Configuration

Edit `config/llm_config.json` to configure model settings:

```json
{
  "chatgpt": {
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "claude": {
    "model": "claude-3.5-sonnet",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "local": {
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL service: `sudo systemctl status postgresql`
   - Verify credentials in `.env`
   - Ensure pgvector extension is installed

2. **LLM API Errors**
   - Verify API keys in `.env`
   - Check rate limits and billing status
   - Test individual model connections

3. **File Permission Errors**
   - Check workspace permissions
   - Verify LLM permission modes
   - Review file operation logs

### Emergency Recovery

Return to working system:
```bash
cd /home/kurt/spatial-ai
./master_startup.sh start
```

### Support

- Check the user manual: `user-guide`
- View system logs: `user-guide logs`
- Migration status: `user-guide migration`

## License

Private development project - All rights reserved.

## Version History

- **v0.1.0** - Initial migration workspace setup
- **v0.2.0** - PostgreSQL memory system implementation
- **v0.3.0** - Conversational CLI with multi-LLM support
- **v0.4.0** - Flask API wrapper with review/undo system
- **v0.5.0** - Enhanced collaboration architecture (current)

---

**Last Updated:** July 2025  
**Status:** Active Development  
**Maintainer:** Kurt