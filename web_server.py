from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.gemini import Gemini
from core.cli_chat import CliChat

load_dotenv()

# Gemini Config
gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
gemini_api_key = os.getenv("GEMINI_API_KEY", "")

assert gemini_model, "Error: GEMINI_MODEL cannot be empty. Update .env"
assert gemini_api_key, "Error: GEMINI_API_KEY cannot be empty. Update .env"

app = FastAPI(title="MCP Gemini Chat", description="Chat with Gemini AI using MCP")

# Global variables to hold the chat instance
chat_instance = None
exit_stack = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    error: str = None

@app.on_event("startup")
async def startup_event():
    global chat_instance, exit_stack
    
    try:
        gemini_service = Gemini(model=gemini_model, api_key=gemini_api_key)
        clients = {}

        command, args = (
            ("uv", ["run", "mcp_server.py"])
            if os.getenv("USE_UV", "0") == "1"
            else ("python", ["mcp_server.py"])
        )

        exit_stack = AsyncExitStack()
        doc_client = await exit_stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        chat_instance = CliChat(
            doc_client=doc_client,
            clients=clients,
            gemini_service=gemini_service,
        )
        
        print("🚀 MCP Gemini Chat server started successfully!")
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global exit_stack
    if exit_stack:
        await exit_stack.aclose()

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Gemini Chat</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .chat-container {
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 800px;
                height: 600px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .chat-header {
                background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .chat-header h1 {
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }
            .chat-header p {
                margin: 5px 0 0 0;
                opacity: 0.9;
                font-size: 14px;
            }
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            .message {
                margin-bottom: 15px;
                display: flex;
                align-items: flex-start;
            }
            .message.user {
                flex-direction: row-reverse;
            }
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                line-height: 1.4;
            }
            .message.user .message-content {
                background: #4285f4;
                color: white;
                margin-left: 10px;
            }
            .message.bot .message-content {
                background: white;
                color: #333;
                border: 1px solid #e0e0e0;
                margin-right: 10px;
            }
            .chat-input-container {
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            .chat-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            .chat-input:focus {
                border-color: #4285f4;
            }
            .send-button {
                background: #4285f4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: background-color 0.3s;
            }
            .send-button:hover {
                background: #3367d6;
            }
            .send-button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 10px;
                color: #666;
            }
            .error {
                background: #ffebee;
                color: #c62828;
                padding: 10px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #f44336;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h1>🤖 MCP Gemini Chat</h1>
                <p>Chat with Google Gemini AI using Model Control Protocol</p>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-content">
                        👋 Hello! I'm your Gemini AI assistant powered by MCP. Ask me anything or try document commands like "@deposition.md" or "/summarize"!
                    </div>
                </div>
            </div>
            <div class="loading" id="loading">🤔 Thinking...</div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chatInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const sendButton = document.getElementById('sendButton');
                const loading = document.getElementById('loading');
                const messages = document.getElementById('chatMessages');
                
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage(message, 'user');
                
                // Clear input and disable button
                input.value = '';
                sendButton.disabled = true;
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message }),
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        addMessage(`Error: ${data.error}`, 'bot', true);
                    } else {
                        addMessage(data.response, 'bot');
                    }
                } catch (error) {
                    addMessage(`Connection error: ${error.message}`, 'bot', true);
                } finally {
                    sendButton.disabled = false;
                    loading.style.display = 'none';
                    input.focus();
                }
            }
            
            function addMessage(text, sender, isError = false) {
                const messages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                if (isError) {
                    contentDiv.className += ' error';
                }
                contentDiv.textContent = text;
                
                messageDiv.appendChild(contentDiv);
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // Focus on input when page loads
            window.onload = function() {
                document.getElementById('chatInput').focus();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Handle chat messages"""
    global chat_instance
    
    if not chat_instance:
        raise HTTPException(status_code=500, detail="Chat service not initialized")
    
    try:
        response = await chat_instance.run(message.message)
        return ChatResponse(response=response)
    except Exception as e:
        return ChatResponse(response="", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MCP Gemini Chat"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MCP Gemini Chat Web Server...")
    print("📱 Open your browser and go to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
