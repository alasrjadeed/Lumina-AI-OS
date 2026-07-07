const vscode = require('vscode');
const http = require('http');

const BASE = 'http://localhost:8000';

function apiPost(path, data) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const url = new URL(path, BASE);
    const opts = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: 120000,
    };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { reject(new Error(data.slice(0, 200))); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    req.write(body);
    req.end();
  });
}

function luminaChatPanel(context) {
  const panel = vscode.window.createWebviewPanel(
    'luminaChat', 'Lumina AI Chat', vscode.ViewColumn.Beside,
    { enableScripts: true, retainContextWhenHidden: true }
  );
  panel.iconPath = vscode.Uri.joinPath(context.extensionUri, 'icon.png');

  panel.webview.html = `<!DOCTYPE html>
<html>
<head>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #1e1e1e; color: #d4d4d4; display: flex; flex-direction: column;
  height: 100vh; padding: 12px;
}
#messages { flex: 1; overflow-y: auto; margin-bottom: 12px; }
.msg { padding: 8px 14px; margin: 6px 0; border-radius: 8px; line-height: 1.5; font-size: 13px; white-space: pre-wrap; }
.user { background: #264f78; color: #e0e0e0; margin-left: 40px; }
.assistant { background: #2d2d2d; color: #d4d4d4; border: 1px solid #3c3c3c; }
.error { background: #5a1d1d; color: #ff8a8a; }
.system { color: #888; font-style: italic; font-size: 11px; text-align: center; }
#input-bar { display: flex; gap: 8px; }
#input {
  flex: 1; padding: 10px 14px; border: 1px solid #3c3c3c; border-radius: 6px;
  background: #252526; color: #d4d4d4; font-size: 13px; outline: none;
}
#input:focus { border-color: #6366f1; }
#send-btn {
  padding: 10px 20px; background: #6366f1; color: #fff; border: none;
  border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500;
}
#send-btn:hover { background: #4f46e5; }
#send-btn:disabled { background: #3c3c3c; color: #666; cursor: default; }
pre { background: #1a1a1a; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 8px 0; }
code { font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 12px; }
</style>
</head>
<body>
<div id="messages"><div class="system">Connected to Lumina AI OS backend</div></div>
<div id="input-bar">
  <input id="input" placeholder="Ask Lumina..." autofocus>
  <button id="send-btn" onclick="send()">Send</button>
</div>
<script>
  const vscode = acquireVsCodeApi();
  const input = document.getElementById('input');
  const msgs = document.getElementById('messages');
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });

  function send() {
    const text = input.value.trim();
    if (!text) return;
    addMsg('user', text);
    input.value = '';
    document.getElementById('send-btn').disabled = true;
    vscode.postMessage({ command: 'chat', text });
  }

  function addMsg(role, text) {
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  window.addEventListener('message', e => {
    document.getElementById('send-btn').disabled = false;
    if (e.data.command === 'reply') addMsg(e.data.status, e.data.text);
  });
</script>
</body>
</html>`;

  panel.webview.onDidReceiveMessage(async (msg) => {
    if (msg.command !== 'chat') return;
    try {
      const res = await apiPost('/chat', { message: msg.text });
      panel.webview.postMessage({ command: 'reply', status: 'assistant', text: res.reply || '(empty response)' });
    } catch (e) {
      panel.webview.postMessage({ command: 'reply', status: 'error', text: `Connection error: ${e.message}\n\nMake sure the Lumina backend is running on ${BASE}` });
    }
  });
  return panel;
}

async function explainCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return vscode.window.showWarningMessage('Open a file and select code first');
  const selection = editor.document.getText(editor.selection);
  if (!selection) return vscode.window.showWarningMessage('Select code to explain');
  vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Lumina: explaining code...' }, async () => {
    try {
      const res = await apiPost('/chat', { message: 'Explain this code concisely:\n```\n' + selection.slice(0, 3000) + '\n```' });
      vscode.window.showInformationMessage(res.reply.slice(0, 500));
    } catch (e) {
      vscode.window.showErrorMessage('Lumina: ' + e.message);
    }
  });
}

async function generateCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return vscode.window.showWarningMessage('Open a file first');
  const lang = editor.document.languageId;
  const input = await vscode.window.showInputBox({ prompt: 'Describe the code to generate', placeHolder: 'e.g. a function to sort a list' });
  if (!input) return;
  vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Lumina: generating...' }, async () => {
    try {
      const res = await apiPost('/code/generate', { description: input, language: lang });
      editor.edit(eb => eb.insert(editor.selection.start, res.code));
      vscode.window.showInformationMessage('Code generated');
    } catch (e) {
      vscode.window.showErrorMessage('Lumina: ' + e.message);
    }
  });
}

async function reviewCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return vscode.window.showWarningMessage('Open a file first');
  const code = editor.document.getText(editor.selection) || editor.document.getText();
  if (!code) return vscode.window.showWarningMessage('Editor is empty');
  vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Lumina: reviewing...' }, async () => {
    try {
      const res = await apiPost('/code/generate', { description: 'Review this code and suggest improvements:\n```\n' + code.slice(0, 4000) + '\n```', language: editor.document.languageId });
      const detail = res.explanation || res.code;
      const action = await vscode.window.showInformationMessage('Lumina review complete', 'View Details');
      if (action) vscode.window.showInformationMessage(detail.slice(0, 500));
    } catch (e) {
      vscode.window.showErrorMessage('Lumina: ' + e.message);
    }
  });
}

function activate(context) {
  const openUrl = (url) => vscode.commands.executeCommand('vscode.open', vscode.Uri.parse(url));
  context.subscriptions.push(
    vscode.commands.registerCommand('lumina.chat', () => luminaChatPanel(context)),
    vscode.commands.registerCommand('lumina.explain', explainCode),
    vscode.commands.registerCommand('lumina.generate', generateCode),
    vscode.commands.registerCommand('lumina.review', reviewCode),
    vscode.commands.registerCommand('lumina.openDashboard', () => openUrl('http://localhost:5173')),
    vscode.commands.registerCommand('lumina.openApiDocs', () => openUrl('http://localhost:8000/docs')),
    vscode.commands.registerCommand('lumina.openWorkspace', () => {
      const { exec } = require('child_process');
      exec('xdg-open /home/oem/Documents/Lumina/workspace');
    }),
    vscode.commands.registerCommand('lumina.startMcp', () => {
      const terminal = vscode.window.createTerminal('Lumina MCP');
      terminal.sendText('source /home/oem/Documents/Lumina/workspace/venv/bin/activate && python3 /home/oem/Documents/Lumina/workspace/mcp_server/server.py');
      terminal.show();
    }),
    vscode.commands.registerCommand('lumina.openCli', () => {
      const terminal = vscode.window.createTerminal('Lumina CLI');
      terminal.show();
      terminal.sendText('lumina help');
    }),
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
