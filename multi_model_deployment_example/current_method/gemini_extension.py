"""
Gemini Extension Service
Separate service to handle Google Gemini Extensions API
This shows the additional complexity needed for Gemini support
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import json
import os
import sys
import asyncio

# Import business logic from main server
# In real deployment, this would be a shared module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from multi_model_server import (
        create_task_logic, list_tasks_logic, update_task_logic, 
        delete_task_logic, upload_file_logic, TaskItem
    )
except ImportError:
    # Fallback for standalone execution
    print("Warning: Could not import from multi_model_server. Using mock functions.")
    
    async def create_task_logic(title: str, description: str = "", priority: str = "medium"):
        return {"id": "mock-id", "title": title, "description": description}
    
    async def list_tasks_logic(completed: bool = None):
        return [{"id": "mock-1", "title": "Mock Task", "completed": False}]
    
    async def update_task_logic(task_id: str, **kwargs):
        return {"id": task_id, "title": "Updated Task"}
    
    async def delete_task_logic(task_id: str):
        return True
    
    async def upload_file_logic(filename: str, content: bytes, file_type: str):
        return {"id": "mock-file-id", "filename": filename, "size": len(content)}

gemini_app = FastAPI(title="Gemini Extension API")

class GeminiFunction(BaseModel):
    name: str
    description: str
    parameters: dict

class GeminiRequest(BaseModel):
    function_name: str
    arguments: dict

class GeminiResponse(BaseModel):
    result: str
    success: bool = True
    data: Any = None

# Generate Gemini Extension Schema
def get_gemini_functions_schema() -> List[dict]:
    """Generate function schemas for Gemini Extensions"""
    return [
        {
            "name": "create_task",
            "description": "Create a new task with title, description and priority level",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string", 
                        "description": "The task title or main objective"
                    },
                    "description": {
                        "type": "string", 
                        "description": "Detailed description of the task",
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
        },
        {
            "name": "list_tasks",
            "description": "Retrieve all tasks or filter by completion status",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean", 
                        "description": "Filter tasks by completion status - true for completed, false for pending, null for all"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter tasks by priority level"
                    }
                }
            }
        },
        {
            "name": "update_task",
            "description": "Modify an existing task by ID with new information",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string", 
                        "description": "Unique identifier of the task to update"
                    },
                    "title": {
                        "type": "string", 
                        "description": "New task title"
                    },
                    "description": {
                        "type": "string", 
                        "description": "New task description"
                    },
                    "completed": {
                        "type": "boolean", 
                        "description": "Mark task as completed (true) or pending (false)"
                    },
                    "priority": {
                        "type": "string", 
                        "enum": ["low", "medium", "high"],
                        "description": "Update task priority level"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "delete_task",
            "description": "Permanently remove a task by its unique identifier",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Unique identifier of the task to delete"
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "get_task_statistics",
            "description": "Get summary statistics about all tasks including counts and completion rates",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_details": {
                        "type": "boolean",
                        "description": "Include detailed breakdown by priority and status",
                        "default": False
                    }
                }
            }
        }
    ]

@gemini_app.get("/")
async def root():
    """Root endpoint for Gemini Extension service"""
    return {
        "service": "Gemini Extension API",
        "version": "1.0.0",
        "description": "Google Gemini Extensions integration for Universal Task Manager",
        "endpoints": {
            "functions": "/functions",
            "execute": "/execute",
            "health": "/health"
        }
    }

@gemini_app.get("/functions")
async def get_gemini_functions():
    """Return available functions for Gemini Extensions"""
    functions = get_gemini_functions_schema()
    
    return {
        "extension_info": {
            "name": "Universal Task Manager",
            "version": "1.0.0",
            "description": "Task management extension for Google Gemini"
        },
        "functions": functions,
        "function_count": len(functions),
        "supported_operations": ["create", "read", "update", "delete", "statistics"]
    }

@gemini_app.post("/execute")
async def execute_gemini_function(request: GeminiRequest):
    """Execute a function call from Gemini"""
    try:
        func_name = request.function_name
        args = request.arguments
        
        print(f"Executing Gemini function: {func_name} with args: {args}")
        
        if func_name == "create_task":
            task = await create_task_logic(
                args["title"],
                args.get("description", ""),
                args.get("priority", "medium")
            )
            
            return GeminiResponse(
                result=f"Task created successfully: '{args['title']}'",
                success=True,
                data={
                    "task_id": task.id if hasattr(task, 'id') else task.get('id'),
                    "title": task.title if hasattr(task, 'title') else task.get('title'),
                    "priority": args.get("priority", "medium")
                }
            )
        
        elif func_name == "list_tasks":
            tasks = await list_tasks_logic(args.get("completed"))
            
            # Format tasks for Gemini response
            task_list = []
            for task in tasks[:20]:  # Limit to 20 tasks for Gemini
                if hasattr(task, 'dict'):
                    task_data = task.dict()
                else:
                    task_data = task
                
                task_list.append({
                    "id": task_data.get("id"),
                    "title": task_data.get("title"),
                    "description": task_data.get("description", ""),
                    "completed": task_data.get("completed", False),
                    "priority": task_data.get("priority", "medium")
                })
            
            filter_text = ""
            if args.get("completed") is not None:
                filter_text = f" (filtered by completed={args['completed']})"
            
            return GeminiResponse(
                result=f"Found {len(task_list)} tasks{filter_text}",
                success=True,
                data={
                    "tasks": task_list,
                    "count": len(task_list),
                    "filter_applied": args.get("completed") is not None
                }
            )
        
        elif func_name == "update_task":
            task = await update_task_logic(
                args["task_id"],
                args.get("title"),
                args.get("description"),
                args.get("completed"),
                args.get("priority")
            )
            
            return GeminiResponse(
                result=f"Task updated successfully",
                success=True,
                data={
                    "task_id": args["task_id"],
                    "updated_fields": [k for k, v in args.items() if k != "task_id" and v is not None]
                }
            )
        
        elif func_name == "delete_task":
            await delete_task_logic(args["task_id"])
            
            return GeminiResponse(
                result=f"Task deleted successfully",
                success=True,
                data={"task_id": args["task_id"]}
            )
        
        elif func_name == "get_task_statistics":
            # Get all tasks for statistics
            all_tasks = await list_tasks_logic()
            
            total = len(all_tasks)
            completed = sum(1 for task in all_tasks 
                          if (hasattr(task, 'completed') and task.completed) or 
                             (isinstance(task, dict) and task.get('completed')))
            
            stats = {
                "total_tasks": total,
                "completed_tasks": completed,
                "pending_tasks": total - completed,
                "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
            }
            
            if args.get("include_details", False):
                # Priority breakdown
                priority_counts = {"high": 0, "medium": 0, "low": 0}
                for task in all_tasks:
                    priority = task.priority if hasattr(task, 'priority') else task.get('priority', 'medium')
                    priority_counts[priority] += 1
                
                stats["priority_breakdown"] = priority_counts
            
            return GeminiResponse(
                result=f"Task statistics: {completed}/{total} completed ({stats['completion_rate']}%)",
                success=True,
                data=stats
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown function: {func_name}. Available functions: {[f['name'] for f in get_gemini_functions_schema()]}"
            )
    
    except Exception as e:
        print(f"Error executing Gemini function {func_name}: {str(e)}")
        return GeminiResponse(
            result=f"Error executing function: {str(e)}",
            success=False,
            data={"error": str(e), "function": func_name}
        )

@gemini_app.get("/health")
async def health_check():
    """Health check endpoint for Gemini service"""
    return {
        "status": "healthy",
        "service": "Gemini Extension API",
        "timestamp": "2024-01-01T00:00:00Z",
        "functions_available": len(get_gemini_functions_schema())
    }

@gemini_app.get("/schema")
async def get_extension_schema():
    """Get the complete Gemini extension schema"""
    return {
        "schema_version": "1.0",
        "extension_name": "universal_task_manager",
        "display_name": "Universal Task Manager",
        "description": "Comprehensive task management system with create, update, delete and analytics capabilities",
        "functions": get_gemini_functions_schema(),
        "endpoints": {
            "functions": "/functions",
            "execute": "/execute",
            "health": "/health"
        },
        "authentication": {
            "type": "none",
            "description": "No authentication required for demo purposes"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(gemini_app, host="0.0.0.0", port=8002)