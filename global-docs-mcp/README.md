# Context7 Persistent Docs MCP Server

A custom MCP server that wraps the Context7 documentation service with persistent local storage. This allows you to download documentation once and reuse it across multiple projects and coding agents.

## Features

- **Persistent Storage**: Downloads are saved to `~/SharedDocs/context7-docs/` for global access
- **Smart Caching**: Automatically uses cached versions unless force refresh is requested
- **Organized Structure**: Files organized by `org/project/version/topic.md`
- **Metadata**: Each file includes retrieval timestamp and source information
- **Cross-Agent Compatible**: Works with any MCP-compatible coding agent

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

1. Install dependencies:
```bash
cd global-docs-mcp
npm install
```

2. Make the script executable (if on Unix-like systems):
```bash
chmod +x index.js
```

## MCP Configuration

Add to your MCP settings file:

```json
{
  "mcpServers": {
    "context7-persistent": {
      "command": "node",
      "args": ["C:/Users/kayno/QAeCore/global-docs-mcp/index.js"]
    }
  }
}
```

## Available Tools

### `resolve-library-id`
Same as original Context7 - resolves library names to Context7-compatible IDs.

### `get-library-docs-with-cache`
Enhanced version that downloads and caches documentation:
- `context7CompatibleLibraryID`: Library ID (required)
- `topic`: Documentation topic (optional)
- `tokens`: Maximum tokens to retrieve (default: 10000)
- `forceRefresh`: Force re-download even if cached (default: false)

### `list-cached-docs`
Lists all locally cached documentation files with metadata.

### `read-cached-doc`
Reads a specific cached documentation file by relative path.

## Usage Examples

1. **Download and cache React hooks documentation:**
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

2. **List all cached documentation:**
```json
{
  "tool": "list-cached-docs",
  "args": {}
}
```

3. **Read cached documentation:**
```json
{
  "tool": "read-cached-doc",
  "args": {
    "relativePath": "react/react/latest/hooks.md"
  }
}
```

## Benefits

- **Offline Access**: Once downloaded, docs are available without internet
- **Faster Access**: Cached docs load instantly
- **Cross-Project**: Use the same cached docs across all your projects
- **Version Control**: Keep different versions of documentation
- **Bandwidth Savings**: Avoid re-downloading the same documentation

## File Format

Each cached file includes:
- YAML frontmatter with metadata (library, topic, retrieval date, etc.)
- Original documentation content
- Footer with caching information