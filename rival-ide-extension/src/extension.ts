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
                                    user_id: "ide_user_local"
                                })
                            });

                            const data: any = await response.json();
                            
                            // 🔥 FIX: Explicitly send all the new fields to the HTML frontend!
                            panel.webview.postMessage({ 
                                command: 'receiveReply', 
                                text: data.reply,
                                ui_state: data.ui_state,         // <-- ADD THIS
                                raw_data: data.raw_api_data      // <-- ADD THIS
                            });

                            // Auto-edit the file if needed
                            if (data.new_code && lastActiveDocument) {
                                const edit = new vscode.WorkspaceEdit();
                                const fullRange = new vscode.Range(
                                    lastActiveDocument.positionAt(0),
                                    lastActiveDocument.positionAt(currentCode.length)
                                );
                                edit.replace(lastActiveDocument.uri, fullRange, data.new_code);
                                await vscode.workspace.applyEdit(edit);
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
        .action-btn { margin-top: 8px; padding: 10px 12px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.2s; }
        .action-btn:hover { background: var(--vscode-button-hoverBackground); transform: scale(0.98); }
        .raw-data { background-color: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; margin-top: 5px; border: 1px solid #444; }
        .input-area { display: flex; gap: 10px; padding-top: 10px; border-top: 1px solid var(--vscode-widget-border); }
        input { flex-grow: 1; padding: 10px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 4px; outline: none; }
        button#sendBtn { padding: 10px 15px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>Rival.io Workflow</h2>
    <div id="chat-container">
        <div class="msg ai-msg">
            Welcome to the Rival.io pipeline! Open a file and click below to begin.
            <button class="action-btn" id="startBtn">⚙️ Create Test Cases</button>
        </div>
    </div>
    <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask AI..." />
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
            return div; 
        }

        // 🔥 Logic to auto-send the "Create test cases" prompt when the button is clicked
        const startBtn = document.getElementById('startBtn');
        if(startBtn) {
            startBtn.addEventListener('click', () => {
                startBtn.disabled = true;
                startBtn.textContent = 'Generating Tests...';
                input.value = 'Create test cases';
                btn.click();
            });
        }

        btn.addEventListener('click', () => {
            const text = input.value.trim();
            if (!text) return;
            appendMessage(text, true);
            vscode.postMessage({ command: 'sendMessage', text: text });
            input.value = '';
            appendMessage("Processing...", false).id = "loading";
        });

        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') btn.click(); });
        window.addEventListener('message', event => {
            const message = event.data;
            if (message.command === 'receiveReply') {
                const loading = document.getElementById('loading');
                if (loading) loading.remove();

                // 🔥 FIX: Find any stuck buttons and update them to show success!
                const startBtn = document.getElementById('startBtn');
                if (startBtn && startBtn.textContent === 'Generating Tests...') {
                    startBtn.textContent = '✅ Tests Generated';
                    startBtn.style.backgroundColor = '#28a745'; // Make it green!
                }

                document.querySelectorAll('.action-btn').forEach(btn => {
                    if (btn.textContent === 'Running...') {
                        btn.textContent = '✅ Tests Ran';
                        btn.style.backgroundColor = '#28a745';
                    }
                    if (btn.textContent === 'Deploying...') {
                        btn.textContent = '✅ Deployed';
                        btn.style.backgroundColor = '#28a745';
                    }
                });

                const msgDiv = appendMessage(message.text, false);

                if (message.raw_data) {
                    // 🔥 FIX: Strip out the AI's text prefixes so it's pure, valid JSON
                    let cleanString = message.raw_data
                        .replace(/^TEST_CASES_JSON:/, '')
                        .replace(/^RAW_RESULTS:/, '')
                        .trim();

                    try {
                        const parsed = JSON.parse(cleanString);
                        const dataDiv = document.createElement('div');
                        dataDiv.className = 'raw-data';
                        // The '2' here tells JavaScript to format it with beautiful multi-line indents!
                        dataDiv.textContent = JSON.stringify(parsed, null, 2); 
                        msgDiv.appendChild(dataDiv);
                    } catch(e) {
                        // Fallback if it still fails
                        const dataDiv = document.createElement('div');
                        dataDiv.className = 'raw-data';
                        dataDiv.textContent = cleanString;
                        msgDiv.appendChild(dataDiv);
                    }
                }

                if (message.ui_state === 'show_run_button') {
                    const runBtn = document.createElement('button');
                    runBtn.className = 'action-btn';
                    runBtn.textContent = '▶ Run Test Cases';
                    runBtn.onclick = () => {
                        appendMessage("Running test cases...", true);
                        vscode.postMessage({ command: 'sendMessage', text: "Run the test cases." });
                        runBtn.disabled = true;
                        runBtn.textContent = 'Running...';
                    };
                    msgDiv.appendChild(runBtn);
                }
                
                if (message.ui_state === 'show_deploy_button') {
                    const deployBtn = document.createElement('button');
                    deployBtn.className = 'action-btn';
                    deployBtn.textContent = '🚀 Deploy to CortexOne';
                    deployBtn.onclick = () => {
                        appendMessage("Deploying...", true);
                        vscode.postMessage({ command: 'sendMessage', text: "Deploy it." });
                        deployBtn.disabled = true;
                        deployBtn.textContent = 'Deploying...';
                    };
                    msgDiv.appendChild(deployBtn);
                }
                
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    </script>
</body>
</html>`;
}