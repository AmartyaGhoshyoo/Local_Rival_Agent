"use strict";var b=Object.create;var r=Object.defineProperty;var x=Object.getOwnPropertyDescriptor;var h=Object.getOwnPropertyNames;var f=Object.getPrototypeOf,w=Object.prototype.hasOwnProperty;var y=(t,o)=>{for(var e in o)r(t,e,{get:o[e],enumerable:!0})},v=(t,o,e,i)=>{if(o&&typeof o=="object"||typeof o=="function")for(let s of h(o))!w.call(t,s)&&s!==e&&r(t,s,{get:()=>o[s],enumerable:!(i=x(o,s))||i.enumerable});return t};var C=(t,o,e)=>(e=t!=null?b(f(t)):{},v(o||!t||!t.__esModule?r(e,"default",{value:t,enumerable:!0}):e,t)),k=t=>v(r({},"__esModule",{value:!0}),t);var D={};y(D,{activate:()=>B,deactivate:()=>E});module.exports=k(D);var n=C(require("vscode")),a;function B(t){console.log("Rival Extension is now active!"),n.window.onDidChangeActiveTextEditor(e=>{e&&e.document.uri.scheme==="file"&&(a=e.document)}),n.window.activeTextEditor&&n.window.activeTextEditor.document.uri.scheme==="file"&&(a=n.window.activeTextEditor.document);let o=n.commands.registerCommand("rival-ide-extension.openChat",()=>{let e=n.window.createWebviewPanel("rivalChat","Rival.io AI Assistant",n.ViewColumn.Beside,{enableScripts:!0,retainContextWhenHidden:!0});e.webview.html=_(),e.webview.onDidReceiveMessage(async i=>{switch(i.command){case"sendMessage":let s=i.text,c="",l="",p="";if(a)c=a.getText(),l=a.uri.fsPath,p=l.split(/[/\\]/).pop()||"";else{e.webview.postMessage({command:"receiveReply",text:"\u{1F6A8} Please click inside a Python file first so I know what to look at!"});return}try{let d=await(await fetch("http://localhost:8000/ide-chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_message:s,source_code:c,file_name:p,file_path:l,user_id:"ide_user_local"})})).json();if(e.webview.postMessage({command:"receiveReply",text:d.reply,ui_state:d.ui_state,raw_data:d.raw_api_data}),d.new_code&&a){let g=new n.WorkspaceEdit,m=new n.Range(a.positionAt(0),a.positionAt(c.length));g.replace(a.uri,m,d.new_code),await n.workspace.applyEdit(g)}}catch(u){e.webview.postMessage({command:"receiveReply",text:`\u{1F6A8} Backend Error: ${u}`})}return}},void 0,t.subscriptions)});t.subscriptions.push(o)}function E(){}function _(){return`<!DOCTYPE html>
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
            <button class="action-btn" id="startBtn">\u2699\uFE0F Create Test Cases</button>
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

        // \u{1F525} Logic to auto-send the "Create test cases" prompt when the button is clicked
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

                // \u{1F525} FIX: Find any stuck buttons and update them to show success!
                const startBtn = document.getElementById('startBtn');
                if (startBtn && startBtn.textContent === 'Generating Tests...') {
                    startBtn.textContent = '\u2705 Tests Generated';
                    startBtn.style.backgroundColor = '#28a745'; // Make it green!
                }

                document.querySelectorAll('.action-btn').forEach(btn => {
                    if (btn.textContent === 'Running...') {
                        btn.textContent = '\u2705 Tests Ran';
                        btn.style.backgroundColor = '#28a745';
                    }
                    if (btn.textContent === 'Deploying...') {
                        btn.textContent = '\u2705 Deployed';
                        btn.style.backgroundColor = '#28a745';
                    }
                });

                const msgDiv = appendMessage(message.text, false);

                if (message.raw_data) {
                    // \u{1F525} FIX: Strip out the AI's text prefixes so it's pure, valid JSON
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
                    runBtn.textContent = '\u25B6 Run Test Cases';
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
                    deployBtn.textContent = '\u{1F680} Deploy to CortexOne';
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
</html>`}0&&(module.exports={activate,deactivate});
