"""
Multi-Model Universal API Server
Demonstrates manual integration with GPT, Claude, Gemini, and Copilot
This is the CURRENT METHOD showing what I would write without Kalibr SDK
"""

from fastapi import FastAPI, APIRouter, WebSocket, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import json
import uuid
import base64
import asyncio
import os
from datetime import datetime
import logging

app = FastAPI(title="Multi-Model Universal API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Store active connections for different models
active_mcp_connections: Dict[str, WebSocket] = {}  # Claude MCP
active_gpt_connections: Dict[str, WebSocket] = {}  # GPT Actions (if WebSocket)

logger = logging.getLogger(__name__)

# ==================== CORE BUSINESS LOGIC ====================
# This would be your actual app logic (QSP, notes app, etc.)

class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    priority: str = "medium"  # low, medium, high

# In-memory storage (replace with your database)
tasks_db: Dict[str, TaskItem] = {}
uploaded_files: Dict[str, dict] = {}

async def create_task_logic(title: str, description: str = "", priority: str = "medium") -> TaskItem:
    """Core business logic for creating tasks"""
    task = TaskItem(
        title=title,
        description=description,
        priority=priority
    )
    tasks_db[task.id] = task
    return task

async def list_tasks_logic(completed: Optional[bool] = None) -> List[TaskItem]:
    """Core business logic for listing tasks"""
    tasks = list(tasks_db.values())
    if completed is not None:
        tasks = [task for task in tasks if task.completed == completed]
    return sorted(tasks, key=lambda x: x.created_at, reverse=True)

async def update_task_logic(task_id: str, title: str = None, description: str = None, 
                           completed: bool = None, priority: str = None) -> TaskItem:
    """Core business logic for updating tasks"""
    if task_id not in tasks_db:
        raise ValueError(f"Task {task_id} not found")
    
    task = tasks_db[task_id]
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if completed is not None:
        task.completed = completed
    if priority is not None:
        task.priority = priority
    
    return task

async def delete_task_logic(task_id: str) -> bool:
    """Core business logic for deleting tasks"""
    if task_id not in tasks_db:
        raise ValueError(f"Task {task_id} not found")
    
    del tasks_db[task_id]
    return True

async def upload_file_logic(filename: str, content: bytes, file_type: str) -> dict:
    """Core business logic for file uploads"""
    file_id = str(uuid.uuid4())
    file_info = {
        "id": file_id,
        "filename": filename,
        "size": len(content),
        "type": file_type,
        "upload_date": datetime.now(),
        "content": base64.b64encode(content).decode('utf-8')  # Store as base64
    }
    uploaded_files[file_id] = file_info
    return file_info

# ==================== REGULAR REST API ENDPOINTS ====================
# These work with your frontend/mobile app

@api_router.post("/tasks", response_model=TaskItem)
async def create_task_rest(title: str, description: str = "", priority: str = "medium"):
    return await create_task_logic(title, description, priority)

@api_router.get("/tasks", response_model=List[TaskItem])
async def list_tasks_rest(completed: Optional[bool] = None):
    return await list_tasks_logic(completed)

@api_router.put("/tasks/{task_id}", response_model=TaskItem)
async def update_task_rest(task_id: str, title: str = None, description: str = None, 
                          completed: bool = None, priority: str = None):
    return await update_task_logic(task_id, title, description, completed, priority)

@api_router.delete("/tasks/{task_id}")
async def delete_task_rest(task_id: str):
    await delete_task_logic(task_id)
    return {"success": True}

@api_router.post("/upload")
async def upload_file_rest(file: UploadFile = File(...)):
    content = await file.read()
    file_info = await upload_file_logic(file.filename, content, file.content_type)
    return {"file_id": file_info["id"], "filename": file_info["filename"]}

# ==================== CLAUDE MCP WEBSOCKET ENDPOINT ====================

@app.websocket("/mcp")
async def claude_mcp_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Claude MCP protocol"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    active_mcp_connections[connection_id] = websocket
    
    logger.info(f"New Claude MCP connection: {connection_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            response = await handle_claude_mcp_message(message)
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logger.error(f"Claude MCP WebSocket error: {e}")
    finally:
        if connection_id in active_mcp_connections:
            del active_mcp_connections[connection_id]

async def handle_claude_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Claude MCP protocol messages"""
    method = message.get("method")
    params = message.get("params", {})
    message_id = message.get("id")
    
    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                    "serverInfo": {"name": "universal-task-manager", "version": "1.0.0"}
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": get_claude_tools_schema()}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result_text = await execute_claude_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"content": [{"type": "text", "text": result_text}]}
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }

def get_claude_tools_schema() -> List[dict]:
    """Generate tool schemas for Claude MCP"""
    return [
        {
            "name": "create_task",
            "description": "Create a new task item",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string", "default": ""},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                },
                "required": ["title"]
            }
        },
        {
            "name": "list_tasks",
            "description": "List all tasks with optional filtering",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "completed": {"type": "boolean", "description": "Filter by completion status"}
                }
            }
        },
        {
            "name": "update_task",
            "description": "Update an existing task",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "completed": {"type": "boolean"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "delete_task",
            "description": "Delete a task by ID",
            "inputSchema": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"]
            }
        },
        {
            "name": "upload_file",
            "description": "Upload a file for processing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string", "description": "Base64 encoded file content"},
                    "file_type": {"type": "string"}
                },
                "required": ["filename", "content", "file_type"]
            }
        }
    ]

async def execute_claude_tool(tool_name: str, arguments: dict) -> str:
    """Execute tools for Claude MCP"""
    try:
        if tool_name == "create_task":
            task = await create_task_logic(
                arguments["title"],
                arguments.get("description", ""),
                arguments.get("priority", "medium")
            )
            return f"✅ Task created: '{task.title}' (ID: {task.id})"
        
        elif tool_name == "list_tasks":
            tasks = await list_tasks_logic(arguments.get("completed"))
            if not tasks:
                return "📝 No tasks found"
            
            result = f"📋 Found {len(tasks)} tasks:\n\n"
            for task in tasks[:10]:  # Limit to 10
                status = "✅" if task.completed else "⏳"
                result += f"{status} **{task.title}** ({task.priority})\n"
                if task.description:
                    result += f"   {task.description}\n"
                result += f"   ID: {task.id}\n\n"
            return result
        
        elif tool_name == "update_task":
            task = await update_task_logic(
                arguments["task_id"],
                arguments.get("title"),
                arguments.get("description"),
                arguments.get("completed"),
                arguments.get("priority")
            )
            return f"✅ Task updated: '{task.title}'"
        
        elif tool_name == "delete_task":
            await delete_task_logic(arguments["task_id"])
            return f"🗑️ Task deleted successfully"
        
        elif tool_name == "upload_file":
            content = base64.b64decode(arguments["content"])
            file_info = await upload_file_logic(
                arguments["filename"],
                content,
                arguments["file_type"]
            )
            return f"📎 File uploaded: {file_info['filename']} ({file_info['size']} bytes)"
        
        else:
            return f"❌ Unknown tool: {tool_name}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ==================== GPT ACTIONS (OpenAPI) ENDPOINTS ====================

@api_router.get("/gpt/openapi.json")
async def get_gpt_openapi_schema():
    """Generate OpenAPI schema for GPT Actions"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Universal Task Manager API",
            "version": "1.0.0",
            "description": "Task management API for GPT Actions"
        },
        "servers": [{"url": os.environ.get('DOMAIN', 'https://your-app.com')}],
        "paths": {
            "/gpt/tasks": {
                "post": {
                    "operationId": "createTask",
                    "summary": "Create a new task",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string", "default": ""},
                                        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                                    },
                                    "required": ["title"]
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Task created successfully"}}
                },
                "get": {
                    "operationId": "listTasks",
                    "summary": "List all tasks",
                    "parameters": [
                        {
                            "name": "completed",
                            "in": "query",
                            "schema": {"type": "boolean"},
                            "description": "Filter by completion status"
                        }
                    ],
                    "responses": {"200": {"description": "List of tasks"}}
                }
            },
            "/gpt/tasks/{task_id}": {
                "put": {
                    "operationId": "updateTask",
                    "summary": "Update a task",
                    "parameters": [
                        {"name": "task_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "completed": {"type": "boolean"},
                                        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Task updated"}}
                },
                "delete": {
                    "operationId": "deleteTask",
                    "summary": "Delete a task",
                    "parameters": [
                        {"name": "task_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "Task deleted"}}
                }
            },
            "/gpt/upload": {
                "post": {
                    "operationId": "uploadFile",
                    "summary": "Upload a file",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "File uploaded"}}
                }
            }
        }
    }

# GPT-specific endpoints (duplicate the business logic)
@api_router.post("/gpt/tasks")
async def create_task_gpt(title: str, description: str = "", priority: str = "medium"):
    task = await create_task_logic(title, description, priority)
    return {"success": True, "task_id": task.id, "message": f"Task '{task.title}' created"}

@api_router.get("/gpt/tasks")
async def list_tasks_gpt(completed: Optional[bool] = None):
    tasks = await list_tasks_logic(completed)
    return {"tasks": [task.dict() for task in tasks], "count": len(tasks)}

@api_router.put("/gpt/tasks/{task_id}")
async def update_task_gpt(task_id: str, title: str = None, description: str = None, 
                         completed: bool = None, priority: str = None):
    task = await update_task_logic(task_id, title, description, completed, priority)
    return {"success": True, "message": f"Task '{task.title}' updated"}

@api_router.delete("/gpt/tasks/{task_id}")
async def delete_task_gpt(task_id: str):
    await delete_task_logic(task_id)
    return {"success": True, "message": "Task deleted"}

@api_router.post("/gpt/upload")
async def upload_file_gpt(file: UploadFile = File(...)):
    content = await file.read()
    file_info = await upload_file_logic(file.filename, content, file.content_type)
    return {"success": True, "file_id": file_info["id"], "filename": file_info["filename"]}

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)