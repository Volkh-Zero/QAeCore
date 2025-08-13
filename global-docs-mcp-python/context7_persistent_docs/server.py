#!/usr/bin/env python3
"""
Context7 Persistent Docs MCP Server

A custom MCP server that wraps the Context7 documentation service with 
persistent local storage for cross-project documentation access.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import requests


class Context7PersistentDocsServer:
    def __init__(self):
        self.server = Server("context7-persistent-docs")
        
        # Global docs directory - accessible from all projects
        self.docs_base_dir = Path.home() / "SharedDocs" / "context7-docs"
        self.docs_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup handlers
        self._setup_handlers()
    
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use as filename"""
        return re.sub(r'[<>:"/\\|?*]', '-', text).replace(' ', '_')
    
    async def _call_context7(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call the original Context7 MCP server"""
        try:
            # Prepare MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            # Call Context7 via subprocess
            process = await asyncio.create_subprocess_exec(
                "npx", "-y", "@upstash/context7-mcp",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send request and get response
            stdout, stderr = await process.communicate(
                input=json.dumps(request).encode()
            )
            
            if process.returncode != 0:
                raise Exception(f"Context7 failed: {stderr.decode()}")
            
            # Parse response (last line should be JSON)
            lines = stdout.decode().strip().split('\n')
            response = json.loads(lines[-1])
            
            return response
            
        except Exception as e:
            raise Exception(f"Failed to call Context7: {str(e)}")
    
    def _save_documentation(
        self, 
        library_id: str, 
        topic: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Save documentation to structured directory"""
        
        # Parse library ID into org/project/version structure
        path_parts = [p for p in library_id.split('/') if p]
        org = path_parts[0] if len(path_parts) > 0 else 'unknown'
        project = path_parts[1] if len(path_parts) > 1 else 'unknown'
        version = path_parts[2] if len(path_parts) > 2 else 'latest'
        
        # Create directory structure
        library_dir = self.docs_base_dir / org / project / version
        library_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        topic_safe = self._sanitize_filename(topic or 'general')
        filename = f"{topic_safe}.md"
        filepath = library_dir / filename
        
        # Create markdown content with metadata
        timestamp = datetime.now().isoformat()
        markdown_content = f"""---
library: {library_id}
topic: {topic or 'general'}
retrieved: {timestamp}
source: Context7
tokens: {metadata.get('tokens', 'unknown') if metadata else 'unknown'}
---

# {library_id} - {topic or 'Documentation'}

> Retrieved from Context7 on {timestamp}

{content}

---
*Cached locally by context7-persistent-docs MCP server*
"""
        
        # Save file
        filepath.write_text(markdown_content, encoding='utf-8')
        
        return {
            "filepath": str(filepath),
            "library_dir": str(library_dir),
            "filename": filename
        }
    
    def _list_cached_docs(self) -> List[Dict[str, Any]]:
        """List all cached documentation files"""
        results = []
        
        try:
            for filepath in self.docs_base_dir.rglob("*.md"):
                relative_path = filepath.relative_to(self.docs_base_dir)
                stats = filepath.stat()
                
                results.append({
                    "path": str(relative_path).replace('\\', '/'),  # Normalize path separators
                    "full_path": str(filepath),
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
        except Exception:
            pass  # Return empty list on error
        
        return results
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="resolve-library-id",
                    description="Resolves a package/product name to a Context7-compatible library ID and returns a list of matching libraries.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "libraryName": {
                                "type": "string",
                                "description": "Library name to search for and retrieve a Context7-compatible library ID."
                            }
                        },
                        "required": ["libraryName"],
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get-library-docs-with-cache",
                    description="Fetches up-to-date documentation for a library and saves it locally for future reference. Combines Context7 retrieval with persistent local storage.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context7CompatibleLibraryID": {
                                "type": "string",
                                "description": "Exact Context7-compatible library ID (e.g., '/mongodb/docs', '/vercel/next.js', '/supabase/supabase')."
                            },
                            "topic": {
                                "type": "string",
                                "description": "Topic to focus documentation on (e.g., 'hooks', 'routing')."
                            },
                            "tokens": {
                                "type": "number",
                                "description": "Maximum number of tokens of documentation to retrieve (default: 10000)."
                            },
                            "forceRefresh": {
                                "type": "boolean",
                                "description": "Force re-download even if cached version exists (default: false)."
                            }
                        },
                        "required": ["context7CompatibleLibraryID"],
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="list-cached-docs",
                    description="List all locally cached documentation files with metadata.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="read-cached-doc",
                    description="Read a specific cached documentation file.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relativePath": {
                                "type": "string",
                                "description": "Relative path to the cached documentation file (e.g., 'react/react/latest/hooks.md')."
                            }
                        },
                        "required": ["relativePath"],
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            
            if name == "resolve-library-id":
                # Pass through to Context7
                result = await self._call_context7("resolve-library-id", arguments)
                
                if "result" in result and "content" in result["result"]:
                    content = result["result"]["content"]
                    if isinstance(content, list) and len(content) > 0:
                        return [types.TextContent(type="text", text=content[0].get("text", ""))]
                
                return [types.TextContent(type="text", text="No results from Context7")]
            
            elif name == "get-library-docs-with-cache":
                library_id = arguments["context7CompatibleLibraryID"]
                topic = arguments.get("topic", "general")
                tokens = arguments.get("tokens", 10000)
                force_refresh = arguments.get("forceRefresh", False)
                
                # Check for cached version unless force refresh
                if not force_refresh:
                    path_parts = [p for p in library_id.split('/') if p]
                    org = path_parts[0] if len(path_parts) > 0 else 'unknown'
                    project = path_parts[1] if len(path_parts) > 1 else 'unknown'
                    version = path_parts[2] if len(path_parts) > 2 else 'latest'
                    topic_safe = self._sanitize_filename(topic)
                    
                    cached_path = self.docs_base_dir / org / project / version / f"{topic_safe}.md"
                    
                    if cached_path.exists():
                        cached_content = cached_path.read_text(encoding='utf-8')
                        stats = cached_path.stat()
                        modified_time = datetime.fromtimestamp(stats.st_mtime).isoformat()
                        
                        return [types.TextContent(
                            type="text",
                            text=f"**Using cached documentation (modified: {modified_time})**\n\n{cached_content}"
                        )]
                
                # Fetch fresh documentation from Context7
                try:
                    result = await self._call_context7("get-library-docs", {
                        "context7CompatibleLibraryID": library_id,
                        "topic": topic,
                        "tokens": tokens
                    })
                    
                    if "result" in result and "content" in result["result"]:
                        content_list = result["result"]["content"]
                        if isinstance(content_list, list) and len(content_list) > 0:
                            doc_content = content_list[0].get("text", "")
                            
                            # Save to cache
                            save_result = self._save_documentation(
                                library_id, topic, doc_content, {"tokens": tokens}
                            )
                            
                            return [types.TextContent(
                                type="text",
                                text=f"{doc_content}\n\n---\n*Documentation saved to: {save_result['filepath']}*"
                            )]
                    
                    return [types.TextContent(type="text", text="No content received from Context7")]
                    
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error fetching documentation: {str(e)}")]
            
            elif name == "list-cached-docs":
                docs = self._list_cached_docs()
                
                if not docs:
                    content = f"**Cached Documentation Files (0 total)**\n\nBase directory: {self.docs_base_dir}\n\nNo cached documentation found."
                else:
                    file_list = "\n".join([
                        f"- {doc['path']} ({doc['size'] // 1024}KB, modified: {doc['modified']})" 
                        for doc in docs
                    ])
                    content = f"**Cached Documentation Files ({len(docs)} total)**\n\nBase directory: {self.docs_base_dir}\n\n{file_list}"
                
                return [types.TextContent(type="text", text=content)]
            
            elif name == "read-cached-doc":
                relative_path = arguments["relativePath"]
                full_path = self.docs_base_dir / relative_path
                
                try:
                    if not full_path.exists():
                        return [types.TextContent(type="text", text=f"File not found: {relative_path}")]
                    
                    content = full_path.read_text(encoding='utf-8')
                    stats = full_path.stat()
                    modified_time = datetime.fromtimestamp(stats.st_mtime).isoformat()
                    
                    return [types.TextContent(
                        type="text",
                        text=f"{content}\n\n---\n*File: {full_path} | Size: {stats.st_size}B | Modified: {modified_time}*"
                    )]
                    
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]
            
            else:
                raise ValueError(f"Unknown tool: {name}")


async def run_server():
    """Run the MCP server"""
    server = Context7PersistentDocsServer()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="context7-persistent-docs",
                server_version="0.1.0",
                capabilities=server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


def main():
    """Main entry point for the MCP server"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()