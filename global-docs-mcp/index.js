#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';

class Context7PersistentDocsServer {
  constructor() {
    this.server = new Server(
      {
        name: "context7-persistent-docs",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );
    
    // Global docs directory - accessible from all projects
    this.docsBaseDir = path.join(os.homedir(), 'SharedDocs', 'context7-docs');
    
    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async ensureDirectoryExists(dirPath) {
    try {
      await fs.access(dirPath);
    } catch {
      await fs.mkdir(dirPath, { recursive: true });
    }
  }

  async callContext7(toolName, args) {
    return new Promise((resolve, reject) => {
      const child = spawn('npx', ['-y', '@upstash/context7-mcp'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          try {
            // Parse MCP protocol response
            const lines = stdout.trim().split('\n');
            const response = JSON.parse(lines[lines.length - 1]);
            resolve(response);
          } catch (e) {
            reject(new Error(`Failed to parse Context7 response: ${e.message}`));
          }
        } else {
          reject(new Error(`Context7 failed with code ${code}: ${stderr}`));
        }
      });

      // Send MCP request
      const request = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
          name: toolName,
          arguments: args
        }
      };

      child.stdin.write(JSON.stringify(request) + '\n');
      child.stdin.end();
    });
  }

  sanitizeFilename(str) {
    return str.replace(/[<>:"/\\|?*]/g, '-').replace(/\s+/g, '_');
  }

  async saveDocumentationToFile(libraryId, topic, content, metadata = {}) {
    // Create directory structure: ~/SharedDocs/context7-docs/org/project/topic/
    const pathParts = libraryId.split('/').filter(Boolean);
    const org = pathParts[0] || 'unknown';
    const project = pathParts[1] || 'unknown';
    const version = pathParts[2] || 'latest';
    
    const libraryDir = path.join(this.docsBaseDir, org, project, version);
    await this.ensureDirectoryExists(libraryDir);
    
    const topicSafe = this.sanitizeFilename(topic || 'general');
    const filename = `${topicSafe}.md`;
    const filepath = path.join(libraryDir, filename);
    
    // Create markdown content with metadata
    const timestamp = new Date().toISOString();
    const markdownContent = `---
library: ${libraryId}
topic: ${topic || 'general'}
retrieved: ${timestamp}
source: Context7
tokens: ${metadata.tokens || 'unknown'}
---

# ${libraryId} - ${topic || 'Documentation'}

> Retrieved from Context7 on ${timestamp}

${content}

---
*Cached locally by context7-persistent-docs MCP server*
`;
    
    await fs.writeFile(filepath, markdownContent, 'utf8');
    
    return {
      filepath,
      libraryDir,
      filename
    };
  }

  async listSavedDocumentation() {
    try {
      await this.ensureDirectoryExists(this.docsBaseDir);
      
      const results = [];
      
      async function scanDirectory(dir, relativePath = '') {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          const relPath = path.join(relativePath, entry.name);
          
          if (entry.isDirectory()) {
            await scanDirectory(fullPath, relPath);
          } else if (entry.name.endsWith('.md')) {
            const stats = await fs.stat(fullPath);
            results.push({
              path: relPath,
              fullPath,
              size: stats.size,
              modified: stats.mtime.toISOString()
            });
          }
        }
      }
      
      await scanDirectory(this.docsBaseDir);
      return results;
    } catch (error) {
      return [];
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "resolve-library-id",
            description: "Resolves a package/product name to a Context7-compatible library ID and returns a list of matching libraries.",
            inputSchema: {
              type: "object",
              properties: {
                libraryName: {
                  type: "string",
                  description: "Library name to search for and retrieve a Context7-compatible library ID."
                }
              },
              required: ["libraryName"],
              additionalProperties: false
            },
          },
          {
            name: "get-library-docs-with-cache",
            description: "Fetches up-to-date documentation for a library and saves it locally for future reference. Combines Context7 retrieval with persistent local storage.",
            inputSchema: {
              type: "object",
              properties: {
                context7CompatibleLibraryID: {
                  type: "string",
                  description: "Exact Context7-compatible library ID (e.g., '/mongodb/docs', '/vercel/next.js', '/supabase/supabase')."
                },
                topic: {
                  type: "string",
                  description: "Topic to focus documentation on (e.g., 'hooks', 'routing')."
                },
                tokens: {
                  type: "number",
                  description: "Maximum number of tokens of documentation to retrieve (default: 10000).",
                  default: 10000
                },
                forceRefresh: {
                  type: "boolean",
                  description: "Force re-download even if cached version exists (default: false).",
                  default: false
                }
              },
              required: ["context7CompatibleLibraryID"],
              additionalProperties: false
            },
          },
          {
            name: "list-cached-docs",
            description: "List all locally cached documentation files with metadata.",
            inputSchema: {
              type: "object",
              properties: {},
              additionalProperties: false
            },
          },
          {
            name: "read-cached-doc",
            description: "Read a specific cached documentation file.",
            inputSchema: {
              type: "object",
              properties: {
                relativePath: {
                  type: "string",
                  description: "Relative path to the cached documentation file (e.g., 'react/react/latest/hooks.md')."
                }
              },
              required: ["relativePath"],
              additionalProperties: false
            },
          }
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        if (name === "resolve-library-id") {
          // Pass through to Context7
          const result = await this.callContext7("resolve-library-id", args);
          return result;
          
        } else if (name === "get-library-docs-with-cache") {
          const { context7CompatibleLibraryID, topic = "general", tokens = 10000, forceRefresh = false } = args;
          
          // Check if cached version exists (unless force refresh)
          if (!forceRefresh) {
            const pathParts = context7CompatibleLibraryID.split('/').filter(Boolean);
            const org = pathParts[0] || 'unknown';
            const project = pathParts[1] || 'unknown';
            const version = pathParts[2] || 'latest';
            const topicSafe = this.sanitizeFilename(topic);
            
            const cachedPath = path.join(this.docsBaseDir, org, project, version, `${topicSafe}.md`);
            
            try {
              const cached = await fs.readFile(cachedPath, 'utf8');
              const stats = await fs.stat(cachedPath);
              
              return {
                content: [
                  {
                    type: "text",
                    text: `**Using cached documentation (modified: ${stats.mtime.toISOString()})**\n\n${cached}`
                  }
                ],
                isError: false,
                cached: true,
                filepath: cachedPath
              };
            } catch {
              // Cache miss, proceed with fresh download
            }
          }
          
          // Fetch fresh documentation from Context7
          const result = await this.callContext7("get-library-docs", {
            context7CompatibleLibraryID,
            topic,
            tokens
          });
          
          if (result.content && result.content[0] && result.content[0].text) {
            // Save to cache
            const saveResult = await this.saveDocumentationToFile(
              context7CompatibleLibraryID,
              topic,
              result.content[0].text,
              { tokens }
            );
            
            return {
              ...result,
              cached: false,
              savedTo: saveResult.filepath,
              message: `Documentation saved to: ${saveResult.filepath}`
            };
          }
          
          return result;
          
        } else if (name === "list-cached-docs") {
          const docs = await this.listSavedDocumentation();
          
          return {
            content: [
              {
                type: "text",
                text: `**Cached Documentation Files (${docs.length} total)**\n\nBase directory: ${this.docsBaseDir}\n\n` +
                  docs.map(doc => `- ${doc.path} (${Math.round(doc.size/1024)}KB, modified: ${doc.modified})`).join('\n') +
                  (docs.length === 0 ? '\nNo cached documentation found.' : '')
              }
            ],
            isError: false,
            files: docs
          };
          
        } else if (name === "read-cached-doc") {
          const { relativePath } = args;
          const fullPath = path.join(this.docsBaseDir, relativePath);
          
          try {
            const content = await fs.readFile(fullPath, 'utf8');
            const stats = await fs.stat(fullPath);
            
            return {
              content: [
                {
                  type: "text",
                  text: content
                }
              ],
              isError: false,
              filepath: fullPath,
              size: stats.size,
              modified: stats.mtime.toISOString()
            };
          } catch (error) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              `Failed to read cached documentation: ${error.message}`
            );
          }
          
        } else {
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${name}`
          );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Context7 Persistent Docs MCP server running on stdio");
  }
}

const server = new Context7PersistentDocsServer();
server.run().catch(console.error);