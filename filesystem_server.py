#!/usr/bin/env python3
"""
MCP Filesystem Server - Provides secure filesystem access via MCP protocol
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiofiles
import shutil
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Configuration
ALLOWED_EXTENSIONS = {'.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.xml', '.csv', '.html', '.css', '.sh', '.conf', '.cfg', '.ini', '.log'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
WORK_DIR = Path.home()  # Can be customized via environment variable

class FilesystemMCPServer:
    def __init__(self, work_dir: Path = WORK_DIR):
        self.work_dir = Path(work_dir).resolve()
        self.server = Server("filesystem-mcp")
        self.setup_tools()
        self.setup_resources()
    
    def is_safe_path(self, path: Path) -> bool:
        """Check if path is within allowed directory and not hidden/system file"""
        try:
            resolved = path.resolve()
            return (
                str(resolved).startswith(str(self.work_dir)) and
                not any(part.startswith('.') for part in resolved.parts[len(self.work_dir.parts):])
            )
        except (OSError, ValueError):
            return False
    
    def setup_tools(self):
        """Register all filesystem tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="read_file",
                    description="Read the contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to read"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_file", 
                    description="Write content to a file (creates if doesn't exist)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to write"},
                            "content": {"type": "string", "description": "Content to write to the file"}
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="create_directory",
                    description="Create a new directory",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "path": {"type": "string", "description": "Path to the directory to create"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the directory to list"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Delete a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to delete"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="move_file",
                    description="Move or rename a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {"type": "string", "description": "Current path of the file"},
                            "destination": {"type": "string", "description": "New path for the file"}
                        },
                        "required": ["source", "destination"]
                    }
                ),
                Tool(
                    name="search_files",
                    description="Search for files by name pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Glob pattern to search for"},
                            "directory": {"type": "string", "description": "Directory to search in (optional)", "default": "."}
                        },
                        "required": ["pattern"]
                    }
                ),
                Tool(
                    name="get_file_info",
                    description="Get metadata about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to get info about"}
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "read_file":
                    return await self._read_file(arguments["path"])
                elif name == "write_file":
                    return await self._write_file(arguments["path"], arguments["content"])
                elif name == "create_directory":
                    return await self._create_directory(arguments["path"])
                elif name == "list_directory":
                    return await self._list_directory(arguments["path"])
                elif name == "delete_file":
                    return await self._delete_file(arguments["path"])
                elif name == "move_file":
                    return await self._move_file(arguments["source"], arguments["destination"])
                elif name == "search_files":
                    return await self._search_files(
                        arguments["pattern"], 
                        arguments.get("directory", ".")
                    )
                elif name == "get_file_info":
                    return await self._get_file_info(arguments["path"])
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _read_file(self, path: str) -> List[TextContent]:
        file_path = self.work_dir / path
        
        if not self.is_safe_path(file_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"Error: File {path} does not exist")]
        
        if file_path.is_dir():
            return [TextContent(type="text", text=f"Error: {path} is a directory, not a file")]
        
        # Check file size
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return [TextContent(type="text", text=f"Error: File {path} is too large (max {MAX_FILE_SIZE} bytes)")]
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return [TextContent(type="text", text=content)]
        except UnicodeDecodeError:
            return [TextContent(type="text", text=f"Error: {path} is not a text file")]
    
    async def _write_file(self, path: str, content: str) -> List[TextContent]:
        file_path = self.work_dir / path
        
        if not self.is_safe_path(file_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return [TextContent(type="text", text=f"Successfully wrote to {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error writing to {path}: {str(e)}")]
    
    async def _create_directory(self, path: str) -> List[TextContent]:
        dir_path = self.work_dir / path
        
        if not self.is_safe_path(dir_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return [TextContent(type="text", text=f"Successfully created directory {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating directory {path}: {str(e)}")]
    
    async def _list_directory(self, path: str) -> List[TextContent]:
        dir_path = self.work_dir / path
        
        if not self.is_safe_path(dir_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        if not dir_path.exists():
            return [TextContent(type="text", text=f"Error: Directory {path} does not exist")]
        
        if not dir_path.is_dir():
            return [TextContent(type="text", text=f"Error: {path} is not a directory")]
        
        try:
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith('.'):
                    continue  # Skip hidden files
                item_type = "DIR" if item.is_dir() else "FILE"
                items.append(f"[{item_type}] {item.name}")
            
            result = "\n".join(items) if items else "Directory is empty"
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing directory {path}: {str(e)}")]
    
    async def _delete_file(self, path: str) -> List[TextContent]:
        file_path = self.work_dir / path
        
        if not self.is_safe_path(file_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"Error: {path} does not exist")]
        
        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            return [TextContent(type="text", text=f"Successfully deleted {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error deleting {path}: {str(e)}")]
    
    async def _move_file(self, source: str, destination: str) -> List[TextContent]:
        src_path = self.work_dir / source
        dst_path = self.work_dir / destination
        
        if not self.is_safe_path(src_path) or not self.is_safe_path(dst_path):
            return [TextContent(type="text", text="Error: Access denied")]
        
        if not src_path.exists():
            return [TextContent(type="text", text=f"Error: Source {source} does not exist")]
        
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            return [TextContent(type="text", text=f"Successfully moved {source} to {destination}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error moving {source} to {destination}: {str(e)}")]
    
    async def _search_files(self, pattern: str, directory: str) -> List[TextContent]:
        search_dir = self.work_dir / directory
        
        if not self.is_safe_path(search_dir):
            return [TextContent(type="text", text=f"Error: Access denied to {directory}")]
        
        if not search_dir.exists():
            return [TextContent(type="text", text=f"Error: Directory {directory} does not exist")]
        
        try:
            matches = list(search_dir.glob(pattern))
            if not matches:
                return [TextContent(type="text", text=f"No files found matching pattern '{pattern}'")]
            
            results = []
            for match in sorted(matches):
                rel_path = match.relative_to(self.work_dir)
                item_type = "DIR" if match.is_dir() else "FILE"
                results.append(f"[{item_type}] {rel_path}")
            
            return [TextContent(type="text", text="\n".join(results))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching for {pattern}: {str(e)}")]
    
    async def _get_file_info(self, path: str) -> List[TextContent]:
        file_path = self.work_dir / path
        
        if not self.is_safe_path(file_path):
            return [TextContent(type="text", text=f"Error: Access denied to {path}")]
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"Error: {path} does not exist")]
        
        try:
            stat = file_path.stat()
            info = {
                "path": path,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting info for {path}: {str(e)}")]
    
    def setup_resources(self):
        """Setup MCP resources (if needed)"""
        pass
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="filesystem-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

async def main():
    # Allow custom work directory via environment variable
    work_dir = Path(os.environ.get("MCP_FILESYSTEM_ROOT", Path.home()))
    
    if len(sys.argv) > 1:
        work_dir = Path(sys.argv[1])
    
    server = FilesystemMCPServer(work_dir)
    print(f"🚀 Starting MCP Filesystem Server - Working directory: {server.work_dir}", file=sys.stderr)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
