# AI Workspace Directory

This is the secure workspace where AI models can perform file operations.

## Purpose

- Safe sandbox for AI file operations
- Local LLM has full read/write access here
- Remote LLMs (ChatGPT/Claude) have read-only access

## File Operations

### Local LLM Capabilities
- Create new files
- Modify existing files
- Delete files (moved to `.trash`, never permanently deleted)
- Create subdirectories
- Full workspace access

### Remote LLMs (ChatGPT/Claude)
- Read existing files
- Analyze file contents
- Cannot modify or create files

## Safety Features

### Trash System
- Deleted files are moved to `.trash/` subdirectory
- Nothing is ever permanently deleted
- Can be restored if needed

### Permission Isolation
- Only Local LLM can write files
- Prevents accidental modifications by remote models
- Audit logging for all operations

## Sample Files

You can create sample files here for AI to work with:

```bash
echo "Hello, AI!" > sample.txt
echo "print('Hello World')" > example.py
mkdir projects
```

## Best Practices

1. **Keep important files elsewhere** - This is a working directory
2. **Regular backups** - Export important AI-generated content
3. **Review AI changes** - Always review files modified by AI
4. **Use version control** - Consider git for important projects

---

**Note**: Files in this directory are excluded from the main repository to avoid committing AI-generated content.