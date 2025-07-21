# Kurt's Spatial AI System - User Manual

**Last Updated:** 2025-07-18  
**System Status:** Migration in progress (Phase 1 - Step 3 Complete)  

---

## Table of Contents

### [System Overview](#system-overview)
- [Current Architecture](#current-architecture)
- [Migration Status](#migration-status)
- [Safety & Rollback](#safety--rollback)

### [Core Systems](#core-systems)
- [Unified Orchestrator](#unified-orchestrator)
- [Persistent Memory (SQLite)](#persistent-memory-sqlite)
- [Persistent Memory (PostgreSQL)](#persistent-memory-postgresql)
- [Brain System](#brain-system)
- [MultiLLM Framework](#multillm-framework)

### [Database Systems](#database-systems)
- [PostgreSQL Setup](#postgresql-setup)
- [pgvector Extension](#pgvector-extension)
- [Database Management](#database-management)

### [Migration Tools](#migration-tools)
- [Migration Log](#migration-log)
- [Memory Migration Test](#memory-migration-test)
- [Backup Systems](#backup-systems)

### [Development Environment](#development-environment)
- [Python Virtual Environment](#python-virtual-environment)
- [Dependencies](#dependencies)
- [Configuration Files](#configuration-files)

### [Startup Scripts](#startup-scripts)
- [Master Startup](#master-startup)
- [Original Startup](#original-startup)
- [Component Scripts](#component-scripts)

### [System Commands](#system-commands)
- [User Guide Command](#user-guide-command)
- [Conversational CLI](#conversational-cli)
- [System Control](#system-control)
- [Database Operations](#database-operations)
- [Testing Commands](#testing-commands)
- [Troubleshooting](#troubleshooting)

### [File Structure](#file-structure)
- [Working System](#working-system)
- [Migration Workspace](#migration-workspace)
- [Backup Locations](#backup-locations)

---

## System Overview

### Current Architecture
Kurt's Spatial AI system consists of multiple AI components orchestrated through a unified memory system. The system is currently in migration from SQLite-based to PostgreSQL-based architecture for improved scalability.

### Migration Status
- **Phase 1 - Step 3:** ✅ Complete (PostgreSQL persistent memory implemented)
- **Current State:** Dual memory systems (SQLite + PostgreSQL) running in parallel
- **Next Phase:** Flask API wrapper implementation

### Safety & Rollback
All migration work is performed in isolated workspace with complete backup of working system.

**Emergency Rollback:**
```bash
cd /home/kurt/spatial-ai
./master_startup.sh start  # Returns to working system
```

---

## Core Systems

### Unified Orchestrator
**Purpose:** Master coordination system for all AI components  
**Path:** `/home/kurt/spatial-ai/unified_orchestrator.py`  
**Status:** ✅ Working  

**Key Features:**
- Component lifecycle management
- Persistent memory integration
- Interactive CLI interface
- Process monitoring

**Usage:**
```bash
# Interactive mode
python3 /home/kurt/spatial-ai/unified_orchestrator.py

# Commands: start, stop, status, exec, memory, consolidate, quit
```

### Persistent Memory (SQLite)
**Purpose:** Original persistent memory system  
**Path:** `/home/kurt/spatial-ai/persistent_memory_core.py`  
**Database:** `/home/kurt/spatial-ai/data/global_memory.db`  
**Status:** ✅ Working (44KB, 10+ entries)  

**Key Features:**
- Session management
- Cross-component memory
- Context linking
- Memory consolidation

**Test:**
```bash
cd /home/kurt/spatial-ai
python3 persistent_memory_core.py
```

### Persistent Memory (PostgreSQL)
**Purpose:** Scalable PostgreSQL-based memory system  
**Path:** `/home/kurt/migration-workspace/persistent_memory_postgres.py`  
**Database:** PostgreSQL `spatial_constellation` database  
**Status:** ✅ Working (identical API to SQLite)  

**Key Features:**
- pgvector support for semantic search
- JSONB metadata storage
- Concurrent access support
- Vector similarity indexing

**Test:**
```bash
cd /home/kurt/migration-workspace
POSTGRES_USER=spatial_ai POSTGRES_PASSWORD=spatial_ai_password /home/kurt/venvs/voice_ai_311/bin/python3 persistent_memory_postgres.py
```

### Brain System
**Purpose:** Multi-LLM orchestrator with secure file operations  
**Path:** `/home/kurt/Assistant/coordinator/brain.py`  
**Status:** ✅ Working (with persistent memory integration)  

**Key Features:**
- OpenAI, Anthropic, Local LLM support
- Secure file operations
- Permission modes (manual/auto/readonly)
- Audit trails

### MultiLLM Framework
**Purpose:** Multi-provider LLM comparison and management  
**Path:** `/home/kurt/whisper.cpp/MultiLLM_Framework.py`  
**Status:** ✅ Working  

**Key Features:**
- Response comparison
- Cost tracking
- Conversation logging
- Performance metrics

---

## Database Systems

### PostgreSQL Setup
**Version:** PostgreSQL 16.9  
**Status:** ✅ Running  
**Service:** `postgresql.service`  

**Database Details:**
- **Host:** localhost:5432
- **Database:** spatial_constellation
- **User:** spatial_ai
- **Password:** spatial_ai_password

**Service Control:**
```bash
# Check status
sudo systemctl status postgresql

# Start/stop/restart
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
```

### pgvector Extension
**Version:** 0.7.0 (built from source)  
**Purpose:** Vector similarity search for AI workloads  
**Status:** ✅ Enabled in spatial_constellation database  

**Verification:**
```bash
sudo -u postgres psql -d spatial_constellation -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

### Database Management
**Connection:**
```bash
# Connect as spatial_ai user
psql -h localhost -U spatial_ai -d spatial_constellation

# Connect as postgres superuser
sudo -u postgres psql
```

**Common Operations:**
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('spatial_constellation'));

-- View memory entries
SELECT component, COUNT(*) FROM memory_entries GROUP BY component;

-- Check extensions
SELECT * FROM pg_extension;
```

---

## Migration Tools

### Migration Log
**Path:** `/home/kurt/migration-workspace/migration_log.md`  
**Purpose:** Complete migration plan and progress tracking  

**Key Sections:**
- Step-by-step migration plan
- Completed task documentation
- Safety measures and rollback procedures
- Current status summary

### Memory Migration Test
**Path:** `/home/kurt/migration-workspace/test_memory_migration.py`  
**Purpose:** Validate SQLite vs PostgreSQL compatibility  

**Test Coverage:**
- API compatibility verification
- Data consistency checking
- Performance comparison
- Migration readiness assessment

**Run Test:**
```bash
cd /home/kurt/migration-workspace
POSTGRES_USER=spatial_ai POSTGRES_PASSWORD=spatial_ai_password /home/kurt/venvs/voice_ai_311/bin/python3 test_memory_migration.py
```

### Backup Systems
**Working System Backup:** `/home/kurt/spatial-ai-backup/`  
**Database Backup:** Manual SQL dumps  
**Configuration Backup:** Included in system backup  

---

## Development Environment

### Python Virtual Environment
**Path:** `/home/kurt/venvs/voice_ai_311/`  
**Python Version:** 3.11  
**Status:** ✅ Active for all operations  

**Activation:**
```bash
source /home/kurt/venvs/voice_ai_311/bin/activate
# or use full path:
/home/kurt/venvs/voice_ai_311/bin/python3
```

### Dependencies
**Core Python Packages:**
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment configuration
- `requests` - HTTP operations
- `sqlite3` - Built-in SQLite support

**System Dependencies:**
- PostgreSQL 16 + pgvector
- Python 3.11
- Git (for pgvector build)
- Build tools (gcc, make, etc.)

### Configuration Files
**Unified Config:** `/home/kurt/spatial-ai/.env`  
**Brain Config:** `/home/kurt/Assistant/coordinator/config/config.py`  
**Migration Config:** Environment variables  

---

## Startup Scripts

### Master Startup
**Path:** `/home/kurt/spatial-ai/master_startup.sh`  
**Purpose:** Complete system startup with persistent memory  
**Status:** ✅ Working  

**Usage:**
```bash
cd /home/kurt/spatial-ai

# Start all components
./master_startup.sh start

# Check status
./master_startup.sh status

# Stop all components
./master_startup.sh stop

# Restart system
./master_startup.sh restart

# Interactive mode
./master_startup.sh interactive
```

### Original Startup
**Path:** `/home/kurt/spatial-ai/startup.sh`  
**Purpose:** Foundation layer startup with master plan checking  
**Status:** ✅ Working  

**Features:**
- Master plan verification
- Session logging
- Component discovery
- Dependency checking

### Component Scripts
**Enhanced CLI:** `/home/kurt/spatial-ai/enhanced_cli.py`  
**Various component scripts in:** `/home/kurt/Assistant/coordinator/`  

---

## System Commands

### User Guide Command
**Command:** `user-guide` or `ug` (short alias)  
**Purpose:** System-wide access to documentation and help  
**Location:** `/home/kurt/.local/bin/user-guide`  
**Path:** Available system-wide via PATH (`/home/kurt/.local/bin/` directory)  

**Usage:**
```bash
# Show full user manual
user-guide
user-guide manual

# Quick reference
user-guide quick
ug quick

# System status
user-guide status
ug status

# Daily workflow guide
user-guide experience

# Migration progress
user-guide migration

# AI enforcement details
user-guide enforcement

# Available commands
user-guide commands

# Help
user-guide help
```

**Features:**
- ✅ Available from anywhere in the system
- ✅ Color-coded output for readability
- ✅ Multiple documentation views
- ✅ Real-time system status checking
- ✅ Short alias `ug` for quick access

### Conversational CLI
**Command:** `chat` (available system-wide)  
**Purpose:** Multi-LLM conversational interface with file access and memory management  
**Location:** `/home/kurt/.local/bin/chat`  
**Path:** Available system-wide via PATH  

**Usage:**
```bash
# Launch conversational CLI from anywhere
chat
```

**Available Models:**
- **ChatGPT (gpt-4o)** - Fast, reliable, read access to all files
- **Claude Code (claude-3.5-sonnet)** - Advanced reasoning, read access to all files  
- **Local LLM (llama3)** - Private, full read/write access

**File Permissions:**
- **All Models**: Can read any file on the system (~/Documents, /home/kurt/*, etc.)
- **Local LLM Only**: Can create, modify, and delete files in workspace
- **ChatGPT/Claude**: Read-only access everywhere

**Basic Commands:**
```bash
# Conversation
hello world                    # Send to ChatGPT (default)
chatgpt explain quantum physics # Send to ChatGPT specifically  
claude analyze this code       # Send to Claude Code
local write notes.txt My notes # Send to Local LLM (can write files)
all what is 2+2?              # Ask all three models

# File Operations (All Models)
read ~/Documents/file.txt      # Read any file
list ~/Documents              # List directory contents
show config.py                # Show file contents

# File Operations (Local LLM Only)
local write test.txt Hello     # Create/write file
local delete old.txt           # Delete file
local read sensitive.txt       # Read file (same as others)

# Session Management
history                        # Show recent conversations
search quantum                 # Search past conversations  
clear                         # Clear current session
files                         # List workspace files
```

**Memory Management:**
```bash
memory stats                   # Show memory statistics
memory search keyword          # Deep search all stored conversations
memory clear                   # Clear old memory entries (with confirmation)
memory export                  # Export conversations to JSON file
```

**Context Management:**
```bash
context show                   # Show current session context
context set chatgpt           # Set default model to ChatGPT
context set claude            # Set default model to Claude
context set local             # Set default model to Local LLM
context reset                 # Reset current session
```

**System Management:**
```bash
system status                  # Show detailed system status
system config                 # Show configuration file locations
system logs                   # Show log file locations  
system restart                # Show restart instructions
```

**Session Features:**
- ✅ **Persistent Memory**: All conversations stored across sessions
- ✅ **Cross-Model Awareness**: Models see workspace files and can reference them
- ✅ **Session Continuity**: Picks up where you left off
- ✅ **Smart Search**: Find conversations by content or context
- ✅ **Export Capability**: Save conversations to JSON files
- ✅ **File Integration**: Models understand and can work with your actual files

**Workspace:**
- **Location**: `/home/kurt/Assistant/coordinator/llm_workspace/`
- **Purpose**: Safe sandbox for AI file operations
- **Contents**: Created files, sample files (welcome.txt, example.py)
- **Trash**: Deleted files go to `.trash` subdirectory (never permanent deletion)

**Examples:**
```bash
# Daily workflow
chat
chatgpt summarize my project status
read ~/Documents/project_notes.txt  
local write daily_summary.txt Today's progress: ...
memory search "project status"
quit

# Code analysis
chat  
claude analyze ~/code/main.py
local write review.txt Claude's analysis: ...
all explain this function
```

**Integration:**
- Works alongside existing `user-guide` system
- Connects to unified orchestrator and persistent memory
- Uses same brain system as other components
- Fully integrated with review/undo system

---

## Useful Commands

### System Control
```bash
# Check system status
cd /home/kurt/spatial-ai && ./master_startup.sh status

# View running processes
ps aux | grep -E "(unified_orchestrator|brain)" | grep -v grep

# Check memory database size
du -h /home/kurt/spatial-ai/data/global_memory.db

# View system logs
tail -f /home/kurt/spatial-ai/logs/startup.log
```

### Database Operations
```bash
# Test PostgreSQL connection
psql -h localhost -U spatial_ai -d spatial_constellation -c "SELECT 'Connected' as status;"

# View PostgreSQL memory stats
psql -h localhost -U spatial_ai -d spatial_constellation -c "SELECT component, COUNT(*) FROM memory_entries GROUP BY component;"

# Check pgvector extension
sudo -u postgres psql -d spatial_constellation -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"

# Database backup
pg_dump -h localhost -U spatial_ai spatial_constellation > backup_$(date +%Y%m%d).sql
```

### Testing Commands
```bash
# Test SQLite memory system
cd /home/kurt/spatial-ai && python3 persistent_memory_core.py

# Test PostgreSQL memory system
cd /home/kurt/migration-workspace && POSTGRES_USER=spatial_ai POSTGRES_PASSWORD=spatial_ai_password /home/kurt/venvs/voice_ai_311/bin/python3 persistent_memory_postgres.py

# Run migration compatibility test
cd /home/kurt/migration-workspace && POSTGRES_USER=spatial_ai POSTGRES_PASSWORD=spatial_ai_password /home/kurt/venvs/voice_ai_311/bin/python3 test_memory_migration.py

# Test brain system
cd /home/kurt/Assistant/coordinator && python3 brain.py
```

### Troubleshooting
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Check Python virtual environment
/home/kurt/venvs/voice_ai_311/bin/python3 --version

# Test Python packages
/home/kurt/venvs/voice_ai_311/bin/python3 -c "import psycopg2; print('psycopg2 OK')"

# Check disk space
df -h /home/kurt/

# Memory usage
free -h
```

---

## File Structure

### Working System
```
/home/kurt/spatial-ai/                    # Main working system
├── master_startup.sh                     # Primary startup script
├── startup.sh                           # Foundation startup script
├── unified_orchestrator.py              # Master orchestrator
├── persistent_memory_core.py             # SQLite memory system
├── enhanced_cli.py                       # Enhanced CLI interface
├── .env                                  # Unified configuration
├── data/                                 # System data
│   ├── global_memory.db                  # SQLite database (44KB)
│   ├── session_state.json               # Session persistence
│   ├── conversations/                    # Memory conversations
│   ├── index/                           # Vector index
│   └── cache/                           # System cache
└── logs/                                # System logs
    └── startup.log                      # Startup log
```

### Migration Workspace
```
/home/kurt/migration-workspace/           # Migration workspace
├── migration_log.md                     # Complete migration plan
├── persistent_memory_postgres.py        # PostgreSQL memory system
├── test_memory_migration.py             # Migration compatibility test
├── user-manual.md                       # This manual
└── spatial_constellation_system/        # Target Flask/React architecture
    ├── backend/                         # Flask API backend
    ├── frontend/                        # React frontend
    ├── data/                           # Data directory
    ├── logs/                           # Logs directory
    └── scripts/                        # Utility scripts
```

### Backup Locations
```
/home/kurt/spatial-ai-backup/            # Complete working system backup
/home/kurt/Assistant/coordinator/        # Brain system
/home/kurt/whisper.cpp/                  # MultiLLM framework
/home/kurt/Documents/KurtVault/          # Project documentation
```

---

## Quick Reference

### Emergency Commands
```bash
# Quick help and status
user-guide status       # System status
user-guide quick        # Quick reference
ug help                 # Command help
chat                    # Start conversational AI

# Rollback to working system
cd /home/kurt/spatial-ai && ./master_startup.sh start

# Stop everything
cd /home/kurt/spatial-ai && ./master_startup.sh stop

# Check system health
cd /home/kurt/spatial-ai && ./master_startup.sh status
```

### Migration Status Check
```bash
# View migration log
user-guide migration    # Full migration log
ug status              # Quick status

# Test both memory systems
cd /home/kurt/migration-workspace && POSTGRES_USER=spatial_ai POSTGRES_PASSWORD=spatial_ai_password /home/kurt/venvs/voice_ai_311/bin/python3 test_memory_migration.py
```

### Key File Paths
- **Main System:** `/home/kurt/spatial-ai/`
- **Migration Work:** `/home/kurt/migration-workspace/`
- **Backup:** `/home/kurt/spatial-ai-backup/`
- **Brain System:** `/home/kurt/Assistant/coordinator/`
- **LLM Workspace:** `/home/kurt/Assistant/coordinator/llm_workspace/`
- **Virtual Environment:** `/home/kurt/venvs/voice_ai_311/`
- **User Guide Command:** `/home/kurt/.local/bin/user-guide`
- **Chat Command:** `/home/kurt/.local/bin/chat`
- **System Commands:** `/home/kurt/.local/bin/` (in PATH)

---

**For questions or issues, refer to the migration log or test the emergency rollback procedure.**

Brainstorming for the spatial gravity effects:

Semantic Gravity Workspace

A living knowledge canvas that thinks—and forgets—at human speed

1 Executive Snapshot (2‑minute read)

Picture your project files, notes, and web clippings as stars on a dark canvas.  Open your laptop and a constellation blooms: related items drift toward one another, bright links pulse where you last worked, and quieter clusters fade into the background until needed.  A timeline slider lets you scrub back to yesterday’s focus or branch off into a new what‑if scenario.  No folders, no search boxes—just a map that reveals what matters now, then gracefully forgets what doesn’t.

Why it matters:  Knowledge workers drown in static file trees and noisy search results.  The Semantic Gravity Workspace keeps your attention on the center of gravity of the current task while still remembering the long tail.  It’s like Google Drive, Obsidian’s graph, and Git time‑travel fused into one intuitive lens.

2 Key Features (lay‑person overview)

Feature

What the user sees

Behind the scenes

Dynamic clusters

Dots self‑organize by topic; touching two items brightens their link.

Cosine similarity of text embeddings + session‑weight boost.

Auto‑decay

Old rabbit holes dim and drift outward.

Exponential half‑life applied to session weights.

Time‑travel slider

Drag to 10 AM yesterday; the map morphs to that moment.

Immutable event log + snapshot replay.

Branch & merge

Fork a speculative path; merge if it pans out.

Event‑stream branching akin to Git DAG.

Focus tags

Type “#patent” → related nodes magnetize instantly.

One‑shot weight spike added to affected edges.

Top‑K pruning

Canvas never clutters; only most relevant links stay visible.

Each node stores only its K strongest outgoing edges.

3 Business Value & Use Cases

R&D labs: surface prior experiments when parameters resemble today’s run.

Legal teams: hop between clauses, prior art, and commentary without combing folders.

Creative writing: resurrect stashed story lines by sliding back to the “aha” moment.

Startup founders: pivot by forking the graph, preserving institutional memory without extra docs.

Revenue model: SaaS seat licenses + on‑prem enterprise tier for regulated sectors.

4 System Architecture (technical audience)

flowchart TD
  subgraph Client
    UI[Electron / WebGL Constellation UI]
  end
  subgraph Edge
    WASM[Lightweight overlay runtime (Rust)]
  end
  subgraph Core
    Redis[Session Overlay (Redis)]
    ANN[Vector Store (Milvus/HNSW)]
    Graph[Persistent Graph (Postgres + pgvector)]
    Log[Immutable Event Log (Apache Kafka / NATS)]
    Snap[Snapshot Store (Parquet in S3)]
  end
  UI -- WebSocket --> WASM
  WASM --> Redis & ANN
  Redis <--> Log
  Log --> Snap
  Redis --> Graph

Data flow:

Ingest new file → embed → store vector + create node.

Action event (open, tag) → publish to event_log.

Runtime applies boost, updates Redis overlay, streams diff to UI.

Every 20 min or Δ>30 % edges → snapshot job materializes overlay to Parquet.

5 Algorithms & Formulas (data‑science deep dive)

5.1 Weight model

Let  be static semantic similarity of embeddings .  Let  be volatile affinity accumulated from user events:



Total link weight:  with  user‑tunable.  Half‑life of boosts: .

5.2 Edge pruning

For each node  keep only the top‑K outgoing edges by .  Complexity per update:  using a bounded heap.

5.3 Snapshot reconstruction

Given snapshot at  and event sequence :

Load snapshot into overlay.

Replay events, updating  in .

UI refresh bulk‑transmits changed edges (WebRTC data channel, binary flatbuffers).

5.4 Branching

Each branch is a pointer to parent snapshot + its own delta log.  Merge uses weighted union:  Conflict if both branches altered  (rare).

6 Hardware & Deployment Targets

Scale

Corpus size

RAM

Disk

CPU / GPU

Solo dev laptop

≤ 10 k docs

4 GB overlay

20 GB total

4‑core CPU; optional RTX 3050

SMB team

1 M docs

32 GB RAM

500 GB SSD

16‑core + A100 for batch re‑embedding

Enterprise

200 M docs

256 GB RAM per shard

50 TB NVMe + S3

Kubernetes + GPU pool

Latency target: < 100 ms edge update round‑trip for 95‑th percentile user action.

7 Implementation Roadmap

Phase

Milestone

Duration

0

Prototype UI + static embeddings; no decay

4 weeks

1

Session overlay, exponential decay, top‑K pruning

+6 weeks

2

Timeline slider, snapshot/replay, branch UI

+8 weeks

3

Multi‑user sync, access control, cloud deploy

+12 weeks

4

Advanced analytics API (RAG integration)

+6 weeks

8 Team & Collaboration Needs

Backend engineer (Rust/Go) for event sourcing pipeline.

Data scientist for embedding tuning & decay‑parameter optimization.

Front‑end/WebGL dev for constellation UI & timeline slider.

DevOps for GPU inference serving + CI/CD.

Domain experts (legal, IoT, coating science) to curate seed corpora.

9 Appendix A – Computational Complexity Summary

Operation

Time

Space

New event update





Snapshot dump





Seek to timestamp



 overlay

Full re‑embed

 GPU



Here  = nodes,  = stored edges,  = embedding dimension.

10 Appendix B – Glossary

Embedding High‑dimensional vector representing semantic meaning of text or media.ANN index Approximate nearest‑neighbor structure enabling sub‑millisecond similarity search.Decay constant (β) Fractional retention of a boost per time unit.Snapshot Serialized overlay state at a wall‑clock timestamp.Branch Divergent sequence of events inheriting from a prior snapshot.

Prepared July 2025  ·  Revision 1.0


