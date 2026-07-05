const vscode = require('vscode');

function activate(context) {
    const apiUrl = vscode.workspace.getConfiguration('lumina').get('apiUrl') || 'http://localhost:8000/api';

    context.subscriptions.push(
        vscode.commands.registerCommand('lumina.generate', () => handleCommand('generate')),
        vscode.commands.registerCommand('lumina.review', () => handleCommand('review')),
        vscode.commands.registerCommand('lumina.debug', () => handleCommand('debug')),
        vscode.commands.registerCommand('lumina.refactor', () => handleCommand('refactor')),
        vscode.commands.registerCommand('lumina.explain', () => handleCommand('explain'))
    );

    vscode.window.showInformationMessage('Lumina AI OS extension activated');
}

async function handleCommand(action) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('Open a file first');
        return;
    }

    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);
    const language = editor.document.languageId;

    if (action === 'generate') {
        const prompt = await vscode.window.showInputBox({
            prompt: 'What code do you want to generate?',
            placeHolder: 'e.g., A FastAPI CRUD endpoint for users',
        });
        if (!prompt) return;
        await luminaApi(`/developer/generate`, { specification: prompt, language }, editor);
    } else if (action === 'review') {
        if (!selectedText) { vscode.window.showWarningMessage('Select code first'); return; }
        await luminaApi(`/developer/review`, { code: selectedText, language }, editor);
    } else if (action === 'debug') {
        if (!selectedText) { vscode.window.showWarningMessage('Select code first'); return; }
        const error = await vscode.window.showInputBox({ prompt: 'Paste the error message' });
        if (!error) return;
        await luminaApi(`/developer/debug`, { code: selectedText, error }, editor);
    } else if (action === 'refactor') {
        if (!selectedText) { vscode.window.showWarningMessage('Select code first'); return; }
        await luminaApi(`/developer/refactor`, { code: selectedText, target: 'performance' }, editor);
    } else if (action === 'explain') {
        if (!selectedText) { vscode.window.showWarningMessage('Select code first'); return; }
        await luminaApi(`/explain/code`, { code: selectedText, language, level: 'intermediate' }, editor);
    }
}

async function luminaApi(endpoint, body, editor) {
    try {
        const apiUrl = vscode.workspace.getConfiguration('lumina').get('apiUrl');
        const token = vscode.workspace.getConfiguration('lumina').get('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${apiUrl}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
        });
        const data = await response.json();

        const panel = vscode.window.createOutputChannel('Lumina AI');
        const content = data.explanation || data.code || data.review || data.analysis || data.refactored || data.content || JSON.stringify(data, null, 2);
        panel.clear();
        panel.appendLine(`=== Lumina AI: ${endpoint} ===`);
        panel.appendLine('');
        panel.appendLine(content);
        panel.show();
    } catch (err) {
        vscode.window.showErrorMessage(`Lumina API error: ${err.message}`);
    }
}

function deactivate() {}

module.exports = { activate, deactivate };
