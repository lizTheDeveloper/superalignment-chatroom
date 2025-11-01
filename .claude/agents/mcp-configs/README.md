# Per-Agent MCP Configurations

This directory contains custom MCP server configurations for individual agents.

## Architecture

**Problem**: Main Claude context has its own `.mcp.json`, but agents need their own custom MCP servers that don't pollute the main context.

**Solution**: Per-agent `.mcp.json` files that agents can load when spawned.

## Usage

When spawning an agent via Task tool, the agent should:

1. Check for agent-specific MCP config at `.claude/agents/mcp-configs/{agent_name}.mcp.json`
2. Load that config to get access to agent-specific tools
3. Main Claude's `.mcp.json` is NOT inherited by agents

## Example Configs

### matrix.mcp.json
Agents who need Matrix integration (orchestrator, sylvia, roy, etc.)

### full.mcp.json
All available MCP servers (chatroom + matrix + memory)

### minimal.mcp.json
Only core tools (chatroom + memory, no Matrix)

## Agent Recommendations

- **orchestrator**: `full.mcp.json` (needs all coordination tools)
- **sylvia, roy, cynthia**: `matrix.mcp.json` (needs Matrix for cross-agent coordination)
- **historian**: `full.mcp.json` (needs Matrix to post documentation updates)
- **architect**: `full.mcp.json` (creates Matrix rooms, updates roadmap)
- **tessa, moss**: `minimal.mcp.json` (focused implementers, less coordination)

## Notes

- Main Claude (the context you're in now) uses `/Users/annhoward/src/superalignmenttoutopia/.mcp.json`
- Agents use `.claude/agents/mcp-configs/{name}.mcp.json` when spawned
- This prevents main context from being cluttered with agent-only tools
