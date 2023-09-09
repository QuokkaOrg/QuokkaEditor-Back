from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise import Tortoise, connections

from quokka_editor_back.routers import users
from quokka_editor_back.settings import TORTOISE_ORM
from quokka_editor_back.routers import documents, websockets, auth
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


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
    <title>Document Editor</title>
    <style>
        #editor {
            border: 1px solid #ccc;
            padding: 10px;
            width: 100%;
            min-height: 200px;
            box-sizing: border-box;
        }
    </style>
</head>
<body>
    <h1>Document Editor</h1>
    
    <div id="editor" contenteditable="true"></div>
    
    <button id="sync">Synchronize</button>
    
    <script>
        let editor = document.getElementById('editor');
        let syncButton = document.getElementById('sync');
        
        let operations = [];
        
        // Fetch the initial document content and version from the server
        async function fetchDocument() {
            let response = await fetch('http://localhost:8100/documents/d6313801-607a-4a7a-99b7-63df61940b15');
            let data = await response.json();
            editor.textContent = data.content;
        }
        
        // Synchronize the document with the server
        async function syncDocument() {
            let response = await fetch('http://localhost:8100/documents/d6313801-607a-4a7a-99b7-63df61940b15/edit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(operations)
            });
            
            let data = await response.json();
            editor.textContent = data.content;
            
            // Clear operations after sync
            operations = [];
        }
        
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
                operations.push(op);
            }
        });
        
        // Handle sync button click
        syncButton.addEventListener('click', syncDocument);
        
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
