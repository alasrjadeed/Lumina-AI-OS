#!/bin/bash
# Start Lumina MCP Server — connects AI tools to Lumina AI OS
source "$(dirname "$0")/venv/bin/activate"
python3 "$(dirname "$0")/mcp_server/server.py"
