"use strict";var h=Object.create;var d=Object.defineProperty;var x=Object.getOwnPropertyDescriptor;var w=Object.getOwnPropertyNames;var b=Object.getPrototypeOf,f=Object.prototype.hasOwnProperty;var y=(t,n)=>{for(var e in n)d(t,e,{get:n[e],enumerable:!0})},g=(t,n,e,a)=>{if(n&&typeof n=="object"||typeof n=="function")for(let s of w(n))!f.call(t,s)&&s!==e&&d(t,s,{get:()=>n[s],enumerable:!(a=x(n,s))||a.enumerable});return t};var k=(t,n,e)=>(e=t!=null?h(b(t)):{},g(n||!t||!t.__esModule?d(e,"default",{value:t,enumerable:!0}):e,t)),C=t=>g(d({},"__esModule",{value:!0}),t);var R={};y(R,{activate:()=>E,deactivate:()=>T});module.exports=C(R);var o=k(require("vscode")),i;function E(t){console.log("Rival Extension is now active!"),o.window.onDidChangeActiveTextEditor(e=>{e&&e.document.uri.scheme==="file"&&(i=e.document)}),o.window.activeTextEditor&&o.window.activeTextEditor.document.uri.scheme==="file"&&(i=o.window.activeTextEditor.document);let n=o.commands.registerCommand("rival-ide-extension.openChat",()=>{let e=o.window.createWebviewPanel("rivalChat","Rival.io AI Assistant",o.ViewColumn.Beside,{enableScripts:!0,retainContextWhenHidden:!0});e.webview.html=M(),e.webview.onDidReceiveMessage(async a=>{switch(a.command){case"sendMessage":let s=a.text,r="",c="",l="";if(i)r=i.getText(),c=i.uri.fsPath,l=c.split(/[/\\]/).pop()||"";else{e.webview.postMessage({command:"receiveReply",text:"\u{1F6A8} Please click inside a Python file first so I know what to look at!"});return}try{let p=await(await fetch("http://localhost:8000/ide-chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_message:s,source_code:r,file_name:l,file_path:c,user_id:"ide_user_1"})})).json();if(e.webview.postMessage({command:"receiveReply",text:p.reply}),p.new_code&&i){let u=new o.WorkspaceEdit,m=new o.Range(i.positionAt(0),i.positionAt(r.length));u.replace(i.uri,m,p.new_code),await o.workspace.applyEdit(u),o.window.showInformationMessage(`Rival AI updated ${l}!`)}}catch(v){e.webview.postMessage({command:"receiveReply",text:`\u{1F6A8} Backend Error: ${v}`})}return}},void 0,t.subscriptions)});t.subscriptions.push(n)}function T(){}function M(){return`<!DOCTYPE html>
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
</html>`}0&&(module.exports={activate,deactivate});
