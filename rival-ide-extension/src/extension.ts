import * as vscode from 'vscode';

// 🔥 1. GLOBAL TRACKER: Remembers your file even when you click the chat!
let lastActiveDocument: vscode.TextDocument | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('Rival Extension is now active!');

    // Update the tracker every time the user clicks a new text file
    vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor && editor.document.uri.scheme === 'file') {
            lastActiveDocument = editor.document;
        }
    });

    // Capture the file that is open right when the extension starts
    if (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.uri.scheme === 'file') {
        lastActiveDocument = vscode.window.activeTextEditor.document;
    }

    const disposable = vscode.commands.registerCommand('rival-ide-extension.openChat', () => {
        
        const panel = vscode.window.createWebviewPanel(
            'rivalChat', 
            'Rival.io AI Assistant', 
            vscode.ViewColumn.Beside,
            { 
                enableScripts: true,
                retainContextWhenHidden: true // Keeps chat history alive
            }
        );

        panel.webview.html = getWebviewContent();

        panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'sendMessage':
                        const userText = message.text;
                        
                        // 🔥 2. GRAB FULL CONTEXT
                        let currentCode = "";
                        let filePath = "";
                        let fileName = "";

                        if (lastActiveDocument) {
                            currentCode = lastActiveDocument.getText(); // Reads the WHOLE file
                            filePath = lastActiveDocument.uri.fsPath;   // Gets full Mac directory
                            fileName = filePath.split(/[/\\]/).pop() || ""; // Gets just the file name
                        } else {
                            panel.webview.postMessage({ command: 'receiveReply', text: "🚨 Please click inside a Python file first so I know what to look at!" });
                            return;
                        }

                        try {
                            const response = await fetch('http://localhost:8000/ide-chat', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    user_message: userText,
                                    source_code: currentCode,
                                    file_name: fileName,
                                    file_path: filePath,
                                    user_id: "ide_user_1"
                                })
                            });

                            const data: any = await response.json();
                            
                            // Send chat message to UI
                            panel.webview.postMessage({ command: 'receiveReply', text: data.reply });

                            // 🔥 3. AUTO-EDIT THE FILE!
                            // If your Python backend sends back a "new_code" field, apply it instantly!
                            if (data.new_code && lastActiveDocument) {
                                const edit = new vscode.WorkspaceEdit();
                                const fullRange = new vscode.Range(
                                    lastActiveDocument.positionAt(0),
                                    lastActiveDocument.positionAt(currentCode.length)
                                );
                                // Replace the whole file with the AI's new code
                                edit.replace(lastActiveDocument.uri, fullRange, data.new_code);
                                await vscode.workspace.applyEdit(edit);
                                
                                vscode.window.showInformationMessage(`Rival AI updated ${fileName}!`);
                            }
                            
                        } catch (error) {
                            panel.webview.postMessage({ command: 'receiveReply', text: `🚨 Backend Error: ${error}` });
                        }
                        return;
                }
            },
            undefined,
            context.subscriptions
        );
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}

// (Keep your exact getWebviewContent() function here, no changes needed to the HTML!)
function getWebviewContent() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: var(--vscode-font-family); padding: 15px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
        #chat-container { flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 15px; }
        .msg { padding: 10px; border-radius: 8px; max-width: 85%; word-wrap: break-word; white-space: pre-wrap; }
        .user-msg { background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); align-self: flex-end; }
        .ai-msg { background-color: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-widget-border); align-self: flex-start; }
        .input-area { display: flex; gap: 10px; padding-top: 10px; border-top: 1px solid var(--vscode-widget-border); }
        input { flex-grow: 1; padding: 10px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; outline: none; }
        button { padding: 10px 15px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: var(--vscode-button-hoverBackground); }
    </style>
</head>
<body>
    <h2>Rival.io Agent</h2>
    <div id="chat-container">
        <div class="msg ai-msg">Hello! Open a Python file and tell me to deploy it.</div>
    </div>
    <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask to deploy, test, or review code..." />
        <button id="sendBtn">Send</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chat-container');
        const input = document.getElementById('userInput');
        const btn = document.getElementById('sendBtn');

        function appendMessage(text, isUser) {
            const div = document.createElement('div');
            div.className = 'msg ' + (isUser ? 'user-msg' : 'ai-msg');
            div.textContent = text;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        btn.addEventListener('click', () => {
            const text = input.value.trim();
            if (!text) return;
            appendMessage(text, true);
            vscode.postMessage({ command: 'sendMessage', text: text });
            input.value = '';
            appendMessage("Thinking...", false);
        });

        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') btn.click(); });

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.command === 'receiveReply') {
                chatContainer.removeChild(chatContainer.lastChild);
                appendMessage(message.text, false);
            }
        });
    </script>
</body>
</html>`;
}