#!/usr/bin/env python3
"""
Morph MCP Server

Exposes Morph LLM capabilities via MCP tools:
- morph-chat: generic chat completion
- morph-merge-code: code merge helper using XML-ish template

Env:
- MORPH_API_KEY (required)
- MORPH_BASE_URL (default https://api.morphllm.com/v1)
- MORPH_MODEL (default morph-v3-large)
"""

import os
import asyncio
from typing import Any, Dict, List

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None  # Will error on use


DEFAULT_BASE_URL = os.getenv("MORPH_BASE_URL", "https://api.morphllm.com/v1")
DEFAULT_MODEL = os.getenv("MORPH_MODEL", "morph-v3-large")


class MorphServer:
    def __init__(self) -> None:
        self.server = Server("morph-mcp")
        self._setup_handlers()

    def _get_client(self) -> "OpenAI":
        if OpenAI is None:
            raise RuntimeError("openai package not available. Please install 'openai>=1.40.0'.")
        api_key = os.getenv("MORPH_API_KEY")
        if not api_key:
            raise RuntimeError("MORPH_API_KEY not set in environment")
        return OpenAI(api_key=api_key, base_url=os.getenv("MORPH_BASE_URL", DEFAULT_BASE_URL))

    def _setup_handlers(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="morph-chat",
                    description="Morph chat completion. Provide messages=[{role, content}], optional model.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string"},
                                        "content": {"type": "string"}
                                    },
                                    "required": ["role", "content"],
                                    "additionalProperties": False
                                }
                            },
                            "model": {"type": "string"}
                        },
                        "required": ["messages"],
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="morph-merge-code",
                    description="Merge code with instructions and update proposals using Morph.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "instructions": {"type": "string"},
                            "initial_code": {"type": "string"},
                            "code_edit": {"type": "string"},
                            "model": {"type": "string"}
                        },
                        "required": ["instructions", "initial_code", "code_edit"],
                        "additionalProperties": False
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> types.TextContent:
            client = self._get_client()
            model = arguments.get("model") or DEFAULT_MODEL

            if name == "morph-chat":
                messages = arguments["messages"]
                resp = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: client.chat.completions.create(model=model, messages=messages)
                )
                content = resp.choices[0].message.content
                return types.TextContent(type="text", text=content)

            if name == "morph-merge-code":
                prompt = (
                    f"<instruction>{arguments['instructions']}</instruction>\n"
                    f"<code>{arguments['initial_code']}</code>\n"
                    f"<update>{arguments['code_edit']}</update>"
                )
                resp = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
                )
                content = resp.choices[0].message.content
                return types.TextContent(type="text", text=content)

            raise types.MCPError(f"Unknown tool: {name}")

    async def run(self) -> None:
        await self.server.run(  # type: ignore[arg-type]
            mcp.server.stdio.STDIOTransport(),
            InitializationOptions(),
        )


def main() -> None:
    srv = MorphServer()
    asyncio.run(srv.run())


if __name__ == "__main__":
    main()
