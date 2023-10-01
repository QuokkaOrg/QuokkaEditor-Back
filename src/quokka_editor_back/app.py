from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from tortoise import Tortoise, connections

from quokka_editor_back.routers import auth, documents, users, websockets
from quokka_editor_back.settings import TORTOISE_ORM


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await connections.close_all()


app = FastAPI(lifespan=lifespan, debug=True)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
html = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Example</title>
</head>

<body>
    <div id="editor" contenteditable="true"></div>

    <hr> <!-- Horizontal line for visual separation -->

    <div id="messages">
        <h3>Received Messages:</h3>
    </div>

    <script>
        let editor = document.getElementById('editor');

        // Connect to the WebSocket
        var socket = new WebSocket('ws://localhost:8100/ws/d6313801-607a-4a7a-99b7-63df61940b15');
        
        // Fetch the initial document content and version from the server
        async function fetchDocument() {
            let response = await fetch('http://localhost:8100/documents/d6313801-607a-4a7a-99b7-63df61940b15');
            let data = await response.json();
            editor.textContent = data.content;
        }
        function insertAt(str, index, insertion) {
            if (index < 0 || index > str.length) {
                return str;
            }
            return str.slice(0, index) + insertion + str.slice(index);
        }
        
        function removeAt(str, index) {
            if (index < 0 || index >= str.length) {
                return str;
            }
            return str.slice(0, index) + str.slice(index + 1);
        }

        
        // Connection established
        socket.onopen = function (event) {
            console.log('Connected to the WebSocket server.');
        };

        // Connection closed
        socket.onclose = function (event) {
            console.log('Disconnected from the WebSocket server.');
        };

        // Handle any errors that occur.
        socket.onerror = function (error) {
            console.error(`WebSocket Error: ${error}`);
        };

        // Handle incoming messages from the server.
        socket.onmessage = function (event) {
            console.log('Received message:', event.data);
            try {
                // Parse the incoming JSON data
                const jsonData = JSON.parse(event.data);
                if(jsonData["char"]) {
                    editor.textContent = insertAt(editor.textContent, jsonData["pos"], jsonData["char"]);
                }
                if (jsonData["type"] == "DELETE") {
                    editor.textContent = removeAt(editor.textContent, jsonData["pos"])
                }
                
            } catch (error) {
                console.error("Error parsing the WebSocket JSON data:", error);
            }
            // Append the message to the "messages" div
            var msgDiv = document.createElement('div');
            msgDiv.textContent = event.data;
            document.getElementById('messages').appendChild(msgDiv);
        };
        
        // Handle local edits and record them as operations
        editor.addEventListener('input', (event) => {
            let op = null;
            if (event.inputType === 'insertText') {
                op = {
                    type: 'INSERT',
                    pos: window.getSelection().focusOffset - 1,
                    char: event.data,
                    revision: 0
                };
            } else if (event.inputType === 'deleteContentBackward') {
                op = {
                    type: 'DELETE',
                    pos: window.getSelection().focusOffset,
                    revision: 0
                };
            }
            
            if (op !== null) {
                console.log(op)
                socket.send(JSON.stringify(op));
            }
        });
        
        // Handle sync button click
        // Fetch initial document content when page loads
        fetchDocument();
    </script>
</body>

</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


app.include_router(router=websockets.router, prefix="/ws")
app.include_router(router=documents.router, prefix="/documents")
app.include_router(router=auth.router, prefix="/auth")
app.include_router(router=users.router, prefix="/users")
