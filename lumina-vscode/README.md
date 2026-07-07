# Lumina AI OS — VS Code Extension

AI-powered coding assistant that connects to your local Lumina backend.

## Features

- **Chat** (`Ctrl+Alt+L`) — Open AI chat panel
- **Explain** (`Ctrl+Alt+E`) — Select code and get explanation
- **Generate** (`Ctrl+Alt+G`) — Describe code to insert at cursor
- **Review** — Get suggestions on current file

## Requirements

- Lumina backend running on `http://localhost:8000`
- Node.js 18+

## Install

```bash
cd lumina-vscode
npm install -g vsce
vsce package
code --install-extension lumina-vscode-0.1.0.vsix
```

Or install manually: Extensions → ... → Install from VSIX
