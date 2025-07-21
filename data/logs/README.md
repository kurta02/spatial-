# System Logs Directory

This directory contains system logs and process management files.

## Log Files

- `system.log` - Main system operations and errors
- `flask_api.log` - Flask API requests and responses
- `brain.log` - Multi-LLM coordination logs (if enabled)
- `memory.log` - Database operations and memory system logs
- `conversation.log` - CLI conversation logs

## Process Management

- `*.pid` files contain process IDs for running components
- Used by start/stop scripts to track system state
- Automatically cleaned up when components stop properly

## Log Levels

- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Errors that don't stop the system
- **CRITICAL**: Errors that require attention

## Maintenance

Logs are not automatically rotated. Monitor disk space and rotate as needed.