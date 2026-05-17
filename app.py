import os
import socket
import threading
import time
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

PORT_WEB = 8080
messages_db = []

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>SZABIST CNDC Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #ece5dd; display: flex; flex-direction: column; height: 100vh; justify-content: space-between; }
        #status { background: #e6ffe6; color: green; padding: 10px; text-align: center; font-weight: bold; }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; }
        .msg { max-width: 70%; padding: 8px 12px; margin: 5px; border-radius: 8px; font-size: 15px; word-wrap: break-word; }
        .right { align-self: flex-end; background: #dcf8c6; }
        .left { align-self: flex-start; background: #ffffff; }
        .time { font-size: 10px; color: gray; margin-left: 10px; float: right; margin-top: 5px; }
        #input-bar { display: flex; padding: 10px; background: #f0f0f0; align-items: center; }
        #msg-input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; outline: none; font-size: 16px; }
        button { background: #128C7E; color: white; border: none; padding: 10px 15px; margin-left: 5px; border-radius: 20px; cursor: pointer; font-size: 16px; }
        #progress-container { background: #eee; display: none; padding: 5px 15px; text-align: center; }
        #progress-bar { width: 0%; height: 5px; background: #25D366; transition: width 0.1s; }
    </style>
</head>
<body>
    <div id="status">Connected (Local Network Hub)</div>
    <div id="chat"></div>
    <div id="progress-container"><div id="progress-bar"></div><span id="progress-txt" style="font-size:10px;">0%</span></div>
    <div id="input-bar">
        <input type="file" id="file-input" style="display:none;" onchange="sendFile()">
        <button onclick="document.getElementById('file-input').click()">📎</button>
        <input type="text" id="msg-input" placeholder="Type a message...">
        <button onclick="sendText()">Send</button>
    </div>

    <script>
        let clientID = Math.random().toString(36).substring(7);

        function fetchMessages() {
            fetch('/get_messages')
                .then(res => res.json())
                .then(msgs => {
                    let chat = document.getElementById('chat');
                    chat.innerHTML = '';
                    msgs.forEach(m => {
                        let side = (m.sender === clientID) ? 'right' : 'left';
                        let div = document.createElement('div');
                        div.className = 'msg ' + side;
                        div.innerHTML = m.body + '<span class="time">' + m.time + '</span>';
                        chat.appendChild(div);
                    });
                });
        }

        function sendText() {
            let input = document.getElementById('msg-input');
            if (input.value.trim() !== '') {
                let msgData = { sender: clientID, body: input.value, time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) };
                fetch('/send_message', { method: 'POST', body: JSON.stringify(msgData) })
                    .then(() => {
                        input.value = '';
                        fetchMessages();
                    });
            }
        }

        function sendFile() {
            let file = document.getElementById('file-input').files[0];
            if (!file) return;
            
            document.getElementById('progress-container').style.display = 'block';
            let pct = 0;
            let interval = setInterval(() => {
                pct += 25;
                document.getElementById('progress-bar').style.width = pct + '%';
                document.getElementById('progress-txt').innerText = 'Transferring: ' + pct + '%';
                
                if (pct >= 100) {
                    clearInterval(interval);
                    setTimeout(() => document.getElementById('progress-container').style.display = 'none', 1000);
                    
                    let msgData = { sender: clientID, body: "📁 Sent File: " + file.name, time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) };
                    fetch('/send_message', { method: 'POST', body: JSON.stringify(msgData) })
                        .then(() => fetchMessages());
                }
            }, 250);
        }

        setInterval(fetchMessages, 1000);
    </script>
</body>
</html>
"""

class HTTPMessenger(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return # Suppress default terminal log floods

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif self.path == "/get_messages":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(messages_db).encode('utf-8'))

    def do_POST(self):
        if self.path == "/send_message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            msg_obj = json.loads(post_data.decode('utf-8'))
            messages_db.append(msg_obj)
            self.send_response(200)
            self.end_headers()

def run():
    server = HTTPServer(('0.0.0.0', PORT_WEB), HTTPMessenger)
    print(f"[*] CNDC Server running on http://localhost:{PORT_WEB}")
    print(f"[*] Access from iPhone using: http://192.168.100.7:{PORT_WEB}")
    server.serve_forever()

if __name__ == "__main__":
    run()