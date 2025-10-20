"""
Microsoft Copilot Plugin Service
Separate service to handle Microsoft 365 Copilot plugin integration
This demonstrates the additional service needed for Copilot support
"""

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import yaml
import os
import sys

# Import business logic from main server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from multi_model_server import (
        create_task_logic, list_tasks_logic, update_task_logic, 
        delete_task_logic, upload_file_logic
    )
except ImportError:
    # Fallback for standalone execution
    print("Warning: Could not import from multi_model_server. Using mock functions.")
    
    async def create_task_logic(title: str, description: str = "", priority: str = "medium"):
        return type('Task', (), {"id": "mock-id", "title": title, "description": description})()
    
    async def list_tasks_logic(completed: Optional[bool] = None):
        return [type('Task', (), {"id": "mock-1", "title": "Mock Task", "completed": False})()]
    
    async def update_task_logic(task_id: str, **kwargs):
        return type('Task', (), {"id": task_id, "title": "Updated Task"})()
    
    async def delete_task_logic(task_id: str):
        return True
    
    async def upload_file_logic(filename: str, content: bytes, file_type: str):
        return {"id": "mock-file-id", "filename": filename, "size": len(content)}

copilot_app = FastAPI(title="Microsoft Copilot Plugin")

class CopilotRequest(BaseModel):
    action: str
    parameters: dict

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None

@copilot_app.get("/")
async def root():
    """Root endpoint for Copilot plugin"""
    return {
        "plugin": "Universal Task Manager for Microsoft Copilot",
        "version": "1.0.0",
        "description": "Task management capabilities integrated with Microsoft 365 Copilot",
        "manifest": "/.well-known/ai-plugin.json",
        "openapi": "/openapi.yaml"
    }

@copilot_app.get("/.well-known/ai-plugin.json")
async def get_copilot_manifest():
    """Microsoft Copilot plugin manifest"""
    domain = os.environ.get('DOMAIN', 'https://your-app.com')
    
    return {
        "schema_version": "v1",
        "name_for_human": "Universal Task Manager",
        "name_for_model": "task_manager",
        "description_for_human": "Comprehensive task management system - create, organize, and track your tasks with AI assistance",
        "description_for_model": "A task management system that allows creating, reading, updating and deleting tasks with priorities, descriptions, and completion tracking. Supports file uploads and provides analytics.",
        "auth": {
            "type": "none"
        },
        "api": {
            "type": "openapi",
            "url": f"{domain}/copilot/openapi.yaml"
        },
        "logo_url": f"{domain}/static/logo.png",
        "contact_email": "support@universaltaskmanager.com",
        "legal_info_url": f"{domain}/legal",
        "privacy_policy_url": f"{domain}/privacy",
        "capabilities": {
            "task_management": True,
            "file_upload": True,
            "analytics": True,
            "priority_levels": ["low", "medium", "high"]
        }
    }

@copilot_app.get("/openapi.yaml")
async def get_copilot_openapi():
    """OpenAPI specification for Microsoft Copilot"""
    domain = os.environ.get('DOMAIN', 'https://your-app.com')
    
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Universal Task Manager",
            "version": "1.0.0",
            "description": "Task management API for Microsoft 365 Copilot integration"
        },
        "servers": [{"url": f"{domain}/copilot"}],
        "paths": {
            "/tasks": {
                "post": {
                    "operationId": "createTask",
                    "summary": "Create a new task",
                    "description": "Create a new task with title, optional description and priority level",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Task title or main objective"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Detailed task description",
                                            "default": ""
                                        },
                                        "priority": {
                                            "type": "string", 
                                            "enum": ["low", "medium", "high"],
                                            "description": "Task priority level",
                                            "default": "medium"
                                        }
                                    },
                                    "required": ["title"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Task created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "task_id": {"type": "string"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "get": {
                    "operationId": "listTasks",
                    "summary": "List all tasks",
                    "description": "Retrieve all tasks with optional filtering by completion status",
                    "parameters": [
                        {
                            "name": "completed",
                            "in": "query",
                            "schema": {"type": "boolean"},
                            "description": "Filter by completion status"
                        },
                        {
                            "name": "priority",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["low", "medium", "high"]},
                            "description": "Filter by priority level"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of tasks",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "tasks": {"type": "array"},
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tasks/{task_id}": {
                "put": {
                    "operationId": "updateTask",
                    "summary": "Update a task",
                    "description": "Update an existing task by ID",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Unique task identifier"
                        }
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
                    "responses": {
                        "200": {"description": "Task updated successfully"}
                    }
                },
                "delete": {
                    "operationId": "deleteTask",
                    "summary": "Delete a task",
                    "description": "Permanently remove a task by ID",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Task deleted successfully"}
                    }
                }
            },
            "/analytics": {
                "get": {
                    "operationId": "getAnalytics",
                    "summary": "Get task analytics",
                    "description": "Retrieve task statistics and analytics",
                    "responses": {
                        "200": {
                            "description": "Task analytics data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "total_tasks": {"type": "integer"},
                                            "completed_tasks": {"type": "integer"},
                                            "completion_rate": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Task": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "completed": {"type": "boolean"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "created_at": {"type": "string", "format": "date-time"}
                    }
                }
            }
        }
    }
    
    yaml_content = yaml.dump(spec, default_flow_style=False)
    return Response(content=yaml_content, media_type="application/x-yaml")

# Copilot-specific endpoints
@copilot_app.post("/copilot/tasks")
async def create_task_copilot(task_data: TaskRequest):
    """Create a new task for Copilot"""
    try:
        task = await create_task_logic(
            task_data.title, 
            task_data.description, 
            task_data.priority
        )
        
        return {
            "success": True, 
            "task_id": task.id, 
            "message": f"Task '{task.title}' created successfully for Microsoft Copilot",
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task_data.priority,
                "completed": False
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@copilot_app.get("/copilot/tasks")
async def list_tasks_copilot(completed: Optional[bool] = None, priority: Optional[str] = None):
    """List tasks for Copilot with optional filtering"""
    try:
        tasks = await list_tasks_logic(completed)
        
        # Filter by priority if specified
        if priority:
            filtered_tasks = []
            for task in tasks:
                task_priority = task.priority if hasattr(task, 'priority') else 'medium'
                if task_priority == priority:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
        
        # Format tasks for Copilot
        task_list = []
        for task in tasks:
            task_dict = task.dict() if hasattr(task, 'dict') else {
                "id": getattr(task, 'id', 'unknown'),
                "title": getattr(task, 'title', 'Unknown Task'),
                "description": getattr(task, 'description', ''),
                "completed": getattr(task, 'completed', False),
                "priority": getattr(task, 'priority', 'medium')
            }
            task_list.append(task_dict)
        
        return {
            "tasks": task_list,
            "count": len(task_list),
            "filters_applied": {
                "completed": completed,
                "priority": priority
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@copilot_app.put("/copilot/tasks/{task_id}")
async def update_task_copilot(task_id: str, task_update: TaskUpdate):
    """Update a task for Copilot"""
    try:
        task = await update_task_logic(
            task_id,
            task_update.title,
            task_update.description,
            task_update.completed,
            task_update.priority
        )
        
        return {
            "success": True, 
            "message": f"Task updated successfully via Microsoft Copilot",
            "task_id": task_id,
            "updated_fields": {k: v for k, v in task_update.dict().items() if v is not None}
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@copilot_app.delete("/copilot/tasks/{task_id}")
async def delete_task_copilot(task_id: str):
    """Delete a task for Copilot"""
    try:
        await delete_task_logic(task_id)
        return {
            "success": True, 
            "message": f"Task deleted successfully via Microsoft Copilot",
            "task_id": task_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@copilot_app.get("/copilot/analytics")
async def get_analytics_copilot():
    """Get task analytics for Copilot"""
    try:
        all_tasks = await list_tasks_logic()
        
        total = len(all_tasks)
        completed = sum(1 for task in all_tasks if getattr(task, 'completed', False))
        
        # Priority breakdown
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        for task in all_tasks:
            priority = getattr(task, 'priority', 'medium')
            priority_counts[priority] += 1
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": total - completed,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
            "priority_breakdown": priority_counts,
            "analytics_timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@copilot_app.get("/copilot/health")
async def health_check_copilot():
    """Health check for Copilot plugin"""
    return {
        "status": "healthy",
        "plugin": "Microsoft Copilot Integration",
        "version": "1.0.0",
        "endpoints_available": 6,
        "manifest_url": "/.well-known/ai-plugin.json",
        "openapi_url": "/openapi.yaml"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(copilot_app, host="0.0.0.0", port=8003)