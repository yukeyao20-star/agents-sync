#!/usr/bin/env bash
# Scope Recall MCP Server Stdio Launcher
exec /Users/lei/agents/virtualenvs/agent-shared-test/bin/python -I -B -m scope_recall.adapters.codex.mcp_entry \
  --config /Users/lei/agents/scope_recall/instance/codex-installation.json \
  --workspace /Users/lei/Documents "$@"
