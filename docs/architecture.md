# Spatial Constellation System Architecture

**Version:** 1.0  
**Last Updated:** July 2025  
**Status:** Active Development  

## Overview

The Spatial Constellation System is a multi-LLM orchestration platform designed to provide unified AI capabilities through a conversational interface with persistent memory and collaborative workflows.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Spatial Constellation System                 │
├─────────────────────────────────────────────────────────────────┤
│                        User Interfaces                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Conversational  │  │   Flask API     │  │   Web Interface │  │
│  │      CLI        │  │    Wrapper      │  │   (Planned)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Orchestration Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Brain System   │  │  Task Router    │  │  Collaboration  │  │
│  │  (Multi-LLM)    │  │                 │  │   Coordinator   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Core Services                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Persistent    │  │  File System    │  │   Session       │  │
│  │     Memory      │  │   Operations    │  │  Management     │  │
│  │  (PostgreSQL)   │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         LLM Providers                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    ChatGPT      │  │   Claude Code   │  │   Local LLM     │  │
│  │   (OpenAI)      │  │  (Anthropic)    │  │   (Ollama)      │  │
│  │   Read-Only     │  │   Read-Only     │  │  Read/Write     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Data Storage                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL    │  │   File System   │  │     Logs        │  │
│  │   + pgvector    │  │    Workspace    │  │   & Metrics     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer

#### Conversational CLI (`core/conversational_cli.py`)
- **Purpose**: Primary user interface for multi-LLM interactions
- **Features**:
  - Natural language command processing
  - Session management and history
  - File operation integration
  - Memory search and export
- **Status**: ✅ Implemented, requires collaboration fixes

#### Flask API Wrapper (`api/app.py`)
- **Purpose**: RESTful API for programmatic access
- **Features**:
  - HTTP endpoints for all CLI functions
  - Review/undo system for operations
  - Authentication and rate limiting
  - JSON response formatting
- **Status**: ✅ Implemented

### 2. Orchestration Layer

#### Brain System (`core/brain.py`)
- **Purpose**: Multi-LLM coordination and management
- **Features**:
  - Provider abstraction layer
  - Request routing and load balancing
  - Response aggregation and comparison
  - Permission and security enforcement
- **Key Classes**:
  - `Brain`: Main orchestrator
  - `LLMProvider`: Abstract provider interface
  - `SecurityManager`: Permission enforcement
- **Status**: ✅ Implemented, individual LLM calls work

#### Task Router (Planned)
- **Purpose**: Intelligent task distribution based on model capabilities
- **Features**:
  - Task analysis and decomposition
  - Model capability matching
  - Workload balancing
- **Status**: 🔄 Not implemented (collaboration issues)

#### Collaboration Coordinator (Planned)
- **Purpose**: Multi-model workflow orchestration
- **Features**:
  - Sequential task handoffs
  - Result synthesis and validation
  - Conflict resolution
- **Status**: 🔄 Not implemented (critical missing component)

### 3. Core Services

#### Persistent Memory (`core/persistent_memory.py`)
- **Purpose**: Cross-session memory and context storage
- **Features**:
  - Vector similarity search with pgvector
  - Session and conversation tracking
  - Metadata and context linking
  - Memory consolidation and cleanup
- **Database Schema**:
  ```sql
  memory_entries (
    id, session_id, component, entry_type, 
    content, context, metadata, embedding, 
    created_at, updated_at
  )
  ```
- **Status**: ✅ Implemented and working

#### File System Operations
- **Purpose**: Secure file access and manipulation
- **Features**:
  - Permission-based access control (read/write/deny)
  - Workspace sandboxing for local LLM
  - Audit logging for all operations
  - Trash system for safe deletion
- **Permissions**:
  - ChatGPT/Claude: Read-only system-wide
  - Local LLM: Read/write in workspace
- **Status**: ✅ Implemented

#### Session Management
- **Purpose**: User session tracking and context preservation
- **Features**:
  - Session state persistence
  - Context window management
  - Multi-session support
- **Status**: ✅ Basic implementation

### 4. LLM Provider Integration

#### OpenAI ChatGPT
- **Model**: gpt-4o
- **Capabilities**: General reasoning, code analysis, fast responses
- **Permissions**: Read-only file access
- **Rate Limits**: 500 RPM, 30K TPM

#### Anthropic Claude Code
- **Model**: claude-3.5-sonnet
- **Capabilities**: Advanced reasoning, code analysis, complex tasks
- **Permissions**: Read-only file access, system analysis
- **Rate Limits**: 200 RPM, 20K TPM

#### Local LLM
- **Model**: Configurable (default: llama3)
- **Capabilities**: Private processing, full file operations
- **Permissions**: Full read/write workspace access
- **Rate Limits**: Hardware dependent

### 5. Data Storage

#### PostgreSQL Database
- **Purpose**: Primary data store for memory and metadata
- **Extensions**: pgvector for embedding storage and similarity search
- **Tables**:
  - `memory_entries`: Conversation and context storage
  - `review_undo`: Operation tracking for API wrapper
- **Features**:
  - JSONB for flexible metadata storage
  - Vector indexing for semantic search
  - Concurrent access support

#### File System Workspace
- **Location**: `/home/kurt/Assistant/coordinator/llm_workspace/`
- **Purpose**: Safe sandbox for AI file operations
- **Features**:
  - Trash directory for safe deletion
  - Permission isolation
  - Audit logging

## Data Flow

### 1. User Request Processing
```
User Input → CLI Parser → Command Router → Brain System → LLM Provider
     ↓
Response ← UI Formatter ← Response Handler ← Brain System ← LLM Response
     ↓
Persistent Memory Storage
```

### 2. Multi-Model Collaboration (Planned)
```
User Request → Task Analyzer → Task Decomposition
     ↓
Model 1 (Analysis) → Model 2 (Implementation) → Model 3 (Verification)
     ↓
Result Synthesis → Response Formatting → User
```

### 3. File Operations
```
File Command → Permission Check → Workspace Validation → File Operation
     ↓
Audit Log → Operation Result → User Feedback
```

## Security Model

### Authentication
- Local user authentication (file system permissions)
- API key management for LLM providers
- Future: JWT tokens for API access

### Authorization
- Role-based permissions (read-only vs read/write)
- Workspace isolation for different models
- Command-level access control

### Data Privacy
- Local PostgreSQL database (no cloud storage)
- API keys stored in environment variables
- Conversation data stays on local system

## Configuration Management

### Environment Variables
```bash
# LLM Configuration
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=spatial_constellation
POSTGRES_USER=spatial_ai
POSTGRES_PASSWORD=

# System Configuration
DEFAULT_PERMISSION_MODE=readonly
ENABLE_FILE_OPERATIONS=true
WORKSPACE_PATH=/path/to/workspace
```

### LLM Configuration (`config/llm_config.json`)
- Model parameters and capabilities
- Rate limits and timeouts
- Collaboration rules and handoff protocols

## Performance Considerations

### Scalability
- Connection pooling for database access
- Async request processing for multiple LLMs
- Caching for frequent memory queries

### Monitoring
- Request/response timing metrics
- Token usage tracking
- Error rate monitoring
- Memory usage statistics

## Development Roadmap

### Phase 1: Core Functionality ✅
- [x] Brain system with individual LLM access
- [x] PostgreSQL memory integration
- [x] Basic conversational CLI
- [x] File system permissions

### Phase 2: Collaboration (Current) 🔄
- [ ] Fix multi-model collaboration architecture
- [ ] Implement task decomposition and routing
- [ ] Add model role awareness
- [ ] Resolve CLI system message pollution

### Phase 3: Advanced Features
- [ ] Web interface development
- [ ] Advanced analytics and reporting
- [ ] Plugin system for extensibility
- [ ] Multi-user support

### Phase 4: Enterprise Features
- [ ] SSO integration
- [ ] Advanced security controls
- [ ] Distributed deployment support
- [ ] API rate limiting and quotas

## Known Issues

### Critical Issues
1. **Multi-model collaboration broken** - `chat_all()` method fails
2. **System message pollution** - Internal messages visible to users
3. **Command distribution failure** - "all" command doesn't properly coordinate

### Medium Priority Issues
1. Incomplete test coverage
2. Missing error handling in some components
3. Performance optimization needed for large memory datasets

### Low Priority Issues
1. Documentation gaps in some modules
2. Logging consistency across components
3. Configuration validation improvements

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock LLM providers for testing
- Database integration tests

### Integration Tests
- End-to-end workflow testing
- Multi-model collaboration scenarios
- File operation permission validation

### Performance Tests
- Memory query performance
- Concurrent user simulation
- Token usage optimization

## Deployment Architecture

### Development Environment
- Local PostgreSQL instance
- Python virtual environment
- Direct LLM API access

### Production Considerations
- Database backup and recovery
- SSL/TLS for API endpoints
- Load balancing for high availability
- Monitoring and alerting systems

---

**This document is actively maintained and updated as the system evolves. For implementation details, see the individual component documentation and source code.**