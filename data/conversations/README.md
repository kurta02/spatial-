# Conversation Exports Directory

This directory contains exported conversation files from the persistent memory system.

## Export Format

Conversations are exported as JSON files with the following structure:

```json
[
  {
    "id": 123,
    "session_id": "session_abc123",
    "component": "conversational_cli",
    "entry_type": "conversation",
    "content": "User: Hello\nChatGPT: Hello! How can I help you?",
    "context": "greeting",
    "metadata": {
      "model": "chatgpt",
      "tokens": 25,
      "response_time": 1.5
    },
    "created_at": "2025-07-21T10:00:00Z",
    "updated_at": "2025-07-21T10:00:00Z"
  }
]
```

## Export Commands

From the conversational CLI:
```
memory export           # Export all conversations
```

This creates files named: `conversations_export_YYYYMMDD_HHMMSS.json`

## Use Cases

### Backup and Archive
- Regular backups of important conversations
- Long-term storage of AI interactions
- Compliance and audit requirements

### Analysis and Research
- Analyze conversation patterns
- Study AI response quality
- Training data for improvements

### Data Migration
- Moving between different systems
- Upgrading database schemas
- System maintenance and recovery

## File Management

### Automatic Naming
Files are automatically named with timestamps to avoid conflicts:
- `conversations_export_20250721_100000.json`
- `conversations_export_20250721_150030.json`

### Size Considerations
Large conversation histories may create large export files. Consider:
- Filtering by date range (future feature)
- Exporting specific components only
- Compressing old exports

### Privacy and Security
- Exported files contain all conversation data
- Store securely if sensitive information is included
- Consider encryption for sensitive exports

---

**Note**: Export files are excluded from git to prevent committing conversation data.