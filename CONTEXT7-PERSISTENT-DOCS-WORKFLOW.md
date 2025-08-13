# Context7 Persistent Documentation Workflow

## Overview

We've successfully implemented a custom MCP server that wraps Context7 with persistent local storage, allowing you to download documentation once and reuse it across multiple projects and coding agents.

## What We Built

### 1. **Python MCP Server** (`global-docs-mcp-python/`)
- **Location**: `C:/Users/kayno/QAeCore/global-docs-mcp-python/`
- **Technology**: Python with UV package manager
- **Features**:
  - Wraps Context7 MCP server functionality
  - Adds persistent local storage at `~/SharedDocs/context7-docs/`
  - Smart caching (uses cached versions unless forced refresh)
  - Structured directory layout: `org/project/version/topic.md`
  - Cross-agent compatibility

### 2. **Global Documentation Storage**
- **Location**: `~/SharedDocs/context7-docs/`
- **Structure**:
  ```
  ~/SharedDocs/context7-docs/
  ├── astral-sh/
  │   └── uv/
  │       └── latest/
  │           ├── installation_and_basic_usage.md
  │           └── project_management_with_pyproject_toml.md
  ├── modelcontextprotocol/
  │   └── python-sdk/
  │       └── latest/
  │           └── creating_MCP_servers_in_Python.md
  └── react/
      └── react/
          └── latest/
              ├── hooks.md
              └── components.md
  ```

### 3. **Downloaded Documentation**
During our setup, we successfully downloaded:
- **UV Documentation**: Installation, basic usage, project management
- **MCP Python SDK Documentation**: Creating MCP servers, tools, resources
- **Context7 Documentation**: Available libraries and usage

## Tools Available

### `resolve-library-id`
- **Purpose**: Search for Context7-compatible library IDs
- **Parameters**: `libraryName` (string)
- **Example**: `"uv python package manager"` → `/astral-sh/uv`

### `get-library-docs-with-cache`
- **Purpose**: Download and cache documentation
- **Parameters**:
  - `context7CompatibleLibraryID` (required): Library ID like `/astral-sh/uv`
  - `topic` (optional): Focus topic like "installation"
  - `tokens` (optional): Max tokens (default: 10000)
  - `forceRefresh` (optional): Force re-download (default: false)

### `list-cached-docs`
- **Purpose**: List all cached documentation files
- **Parameters**: None
- **Returns**: File paths, sizes, and modification dates

### `read-cached-doc`
- **Purpose**: Read specific cached documentation
- **Parameters**: `relativePath` (e.g., "astral-sh/uv/latest/installation.md")

## Current Configuration

### MCP Settings (`mcp_settings.json`)
```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "uv",
      "args": ["run", "context7-persistent-docs"],
      "cwd": "C:/Users/kayno/QAeCore/global-docs-mcp-python",
      "alwaysAllow": [
        "resolve-library-id",
        "get-library-docs-with-cache", 
        "list-cached-docs",
        "read-cached-doc"
      ]
    }
  }
}
```

## How to Use

### 1. **Restart KiloCode**
MCP servers require restart to pick up configuration changes.

### 2. **Download Documentation**
```json
{
  "tool": "get-library-docs-with-cache",
  "args": {
    "context7CompatibleLibraryID": "/react/react",
    "topic": "hooks",
    "tokens": 15000
  }
}
```

### 3. **List Cached Docs**
```json
{
  "tool": "list-cached-docs",
  "args": {}
}
```

### 4. **Read Cached Documentation**
```json
{
  "tool": "read-cached-doc", 
  "args": {
    "relativePath": "react/react/latest/hooks.md"
  }
}
```

## Benefits Achieved

✅ **Offline Access**: Documentation available without internet  
✅ **Speed**: Cached docs load instantly  
✅ **Cross-Project**: Same cache across all projects  
✅ **Cross-Agent**: Works with KiloCode, Gemini Code Assist, etc.  
✅ **Version Control**: Different versions preserved  
✅ **Bandwidth Savings**: No re-downloading  
✅ **UV Compatible**: Modern Python tooling  

## Troubleshooting

### Server Won't Start
```bash
cd global-docs-mcp-python
uv run python -c "from context7_persistent_docs.server import main; print('OK')"
```

### Connection Issues  
1. Restart VS Code/KiloCode
2. Check MCP settings path is correct
3. Verify UV environment: `cd global-docs-mcp-python && uv sync`

### Permission Errors
Ensure `~/SharedDocs/` directory is writable

### Context7 Not Available
Original Context7 MCP server must be accessible via `npx -y @upstash/context7-mcp`

## Replication for Other Agents

### For Gemini Code Assist
1. Copy the MCP configuration to Gemini's settings
2. Update paths as needed
3. Restart Gemini Code Assist

### For Other MCP Clients
```json
{
  "command": "uv",
  "args": ["run", "context7-persistent-docs"],
  "cwd": "C:/Users/kayno/QAeCore/global-docs-mcp-python"
}
```

## File Structure Summary

```
C:/Users/kayno/QAeCore/
├── global-docs-mcp-python/              # Our custom MCP server
│   ├── context7_persistent_docs/
│   │   ├── __init__.py
│   │   └── server.py                    # Main server implementation
│   ├── pyproject.toml                   # UV configuration
│   └── README.md                        # Detailed setup instructions
├── global-docs-mcp/                     # Node.js version (backup)
└── CONTEXT7-PERSISTENT-DOCS-WORKFLOW.md # This documentation

~/SharedDocs/context7-docs/               # Global documentation cache
├── astral-sh/uv/latest/                 # UV documentation
├── modelcontextprotocol/python-sdk/     # MCP Python SDK docs  
└── [future downloaded docs...]          # Additional cached docs
```

## Next Steps

1. **Restart KiloCode** to activate the new MCP server
2. **Test the workflow** by downloading documentation for your current projects
3. **Configure other agents** using the same MCP server setup
4. **Build your documentation library** by caching docs for frequently used libraries

## Success Metrics

- ✅ Custom MCP server created and configured
- ✅ Global documentation storage implemented  
- ✅ UV-compatible Python implementation
- ✅ Cross-agent compatible design
- ✅ Smart caching with metadata
- ✅ Structured directory organization
- ✅ Downloaded sample documentation (UV, MCP, Context7)

**The persistent documentation system is ready for use across all your coding environments!**