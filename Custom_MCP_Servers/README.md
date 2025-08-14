# Context7 Persistent Docs MCP Server (Python)

A Python MCP server that wraps the Context7 documentation service with persistent local storage. This allows you to download documentation once and reuse it across multiple projects and coding agents.

## Features

- **Persistent Storage**: Downloads are saved to `~/SharedDocs/context7-docs/` for global access
- **Smart Caching**: Automatically uses cached versions unless force refresh is requested
- **Organized Structure**: Files organized by `org/project/version/topic.md`
- **Metadata**: Each file includes retrieval timestamp and source information
- **Cross-Agent Compatible**: Works with any MCP-compatible coding agent
- **UV Compatible**: Built for modern Python package management

## Directory Structure

```
~/SharedDocs/context7-docs/
├── react/
│   └── react/
│       └── latest/
│           ├── hooks.md
│           └── components.md
├── vercel/
│   └── next.js/
│       ├── latest/
│       │   ├── routing.md
│       │   └── api-routes.md
│       └── v14.3.0-canary.87/
│           └── experimental-features.md
└── mongodb/
    └── docs/
        └── latest/
            ├── aggregation.md
            └── indexing.md
```

## Installation

### Using UV (Recommended)

1. **Initialize and install dependencies:**
```bash
cd global-docs-mcp-python
uv sync
```

2. **Install in development mode:**
```bash
uv pip install -e .
```

### Alternative: Manual Installation

```bash
cd global-docs-mcp-python
pip install -e .
```

## MCP Configuration

Add to your MCP settings file (e.g., `mcp_settings.json`):

```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "uv",
      "args": ["run", "context7-persistent-docs"],
      "cwd": "C:/Users/kayno/QAeCore/global-docs-mcp-python"
    }
  }
}
```

**Alternative configurations:**

### Using Python directly:
```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "python",
      "args": ["-m", "context7_persistent_docs.server"],
      "cwd": "C:/Users/kayno/QAeCore/global-docs-mcp-python"
    }
  }
}
```

### Using full path to UV environment:
```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "C:/Users/kayno/QAeCore/global-docs-mcp-python/.venv/Scripts/context7-persistent-docs.exe"
    }
  }
}
```

## Available Tools

### `resolve-library-id`
Same as original Context7 - resolves library names to Context7-compatible IDs.

**Parameters:**
- `libraryName` (string, required): Library name to search for

### `get-library-docs-with-cache`
Enhanced version that downloads and caches documentation.

**Parameters:**
- `context7CompatibleLibraryID` (string, required): Library ID
- `topic` (string, optional): Documentation topic
- `tokens` (number, optional): Maximum tokens to retrieve (default: 10000)
- `forceRefresh` (boolean, optional): Force re-download even if cached (default: false)

### `list-cached-docs`
Lists all locally cached documentation files with metadata.

### `read-cached-doc`
Reads a specific cached documentation file by relative path.

**Parameters:**
- `relativePath` (string, required): Path relative to cache directory

## Usage Examples

### 1. Download and cache React hooks documentation:
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

### 2. List all cached documentation:
```json
{
  "tool": "list-cached-docs",
  "args": {}
}
```

### 3. Read cached documentation:
```json
{
  "tool": "read-cached-doc",
  "args": {
    "relativePath": "react/react/latest/hooks.md"
  }
}
```

## Global Setup for Multiple Agents

To use this across all your coding agents (KiloCode, Gemini Code Assist, etc.):

1. **Install once globally:**
```bash
cd global-docs-mcp-python
uv sync
```

2. **Configure each agent's MCP settings** to point to the same server:
```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "uv",
      "args": ["run", "context7-persistent-docs"],
      "cwd": "C:/Users/kayno/QAeCore/global-docs-mcp-python"
    }
  }
}
```

3. **All agents will share the same documentation cache** at `~/SharedDocs/context7-docs/`

## Development

### Project Structure
```
global-docs-mcp-python/
├── pyproject.toml          # UV/pip configuration
├── context7_persistent_docs/
│   ├── __init__.py
│   └── server.py           # Main MCP server implementation
└── README.md
```

### Running in Development
```bash
# Start the server directly
uv run python -m context7_persistent_docs.server

# Or use the console script
uv run context7-persistent-docs
```

### Testing
You can test the server using MCP protocol tools or integrate it directly with your coding agents.

## Benefits

- **Offline Access**: Once downloaded, docs are available without internet
- **Faster Access**: Cached docs load instantly
- **Cross-Project**: Use the same cached docs across all your projects
- **Version Control**: Keep different versions of documentation
- **Bandwidth Savings**: Avoid re-downloading the same documentation
- **UV Compatible**: Modern Python tooling support

## Troubleshooting

### Common Issues

1. **"Module not found" errors**: Ensure you've run `uv sync` and the virtual environment is activated
2. **Permission errors**: Check that `~/SharedDocs/` is writable
3. **Context7 not responding**: Verify that `npx @upstash/context7-mcp` works independently

### Debug Mode
Add debug logging by modifying the server or running with verbose output:
```bash
uv run context7-persistent-docs --verbose  # (if implemented)