"""
Universal Task Manager - Kalibr SDK Implementation
This is the KALIBR SDK METHOD showing the same functionality in 80 lines
Automatically works with GPT, Claude, Gemini, and Copilot
"""

from kalibr import KalibrApp
from kalibr.types import FileUpload
from kalibr.auth_helpers import kalibr_auth
from kalibr.analytics import kalibr_analytics
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Initialize Kalibr App with built-in analytics
@kalibr_analytics(storage="file", auto_track=True)
class UniversalTaskManager(KalibrApp):
    def __init__(self):
        super().__init__(
            title="Universal Task Manager",
            description="AI-powered task management across all major AI models"
        )

app = UniversalTaskManager()

# Data model
class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime
    priority: str = "medium"

# In-memory storage (replace with your database)
tasks_db: dict[str, Task] = {}
files_db: dict[str, dict] = {}

@app.action(
    name="create_task",
    description="Create a new task with title, description and priority level"
)
def create_task(title: str, description: str = "", priority: str = "medium") -> dict:
    """Create a new task item"""
    task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        priority=priority,
        created_at=datetime.now()
    )
    tasks_db[task.id] = task
    
    return {
        "success": True,
        "task_id": task.id,
        "message": f"Task '{task.title}' created successfully"
    }

@app.action(
    name="list_tasks", 
    description="List all tasks with optional filtering by completion status"
)
def list_tasks(completed: Optional[bool] = None) -> dict:
    """List tasks with optional filtering"""
    tasks = list(tasks_db.values())
    
    if completed is not None:
        tasks = [task for task in tasks if task.completed == completed]
    
    # Sort by creation date (newest first)
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "tasks": [task.dict() for task in tasks],
        "count": len(tasks),
        "filter_applied": f"completed={completed}" if completed is not None else "none"
    }

@app.action(
    name="update_task",
    description="Update an existing task by ID with new title, description, completion status or priority"
)
def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
    priority: Optional[str] = None
) -> dict:
    """Update an existing task"""
    if task_id not in tasks_db:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    task = tasks_db[task_id]
    
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if completed is not None:
        task.completed = completed
    if priority is not None:
        task.priority = priority
    
    return {
        "success": True,
        "message": f"Task '{task.title}' updated successfully"
    }

@app.action(
    name="delete_task",
    description="Delete a task by its ID"
)
def delete_task(task_id: str) -> dict:
    """Delete a task by ID"""
    if task_id not in tasks_db:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    task_title = tasks_db[task_id].title
    del tasks_db[task_id]
    
    return {
        "success": True,
        "message": f"Task '{task_title}' deleted successfully"
    }

@app.file_handler(
    name="upload_file",
    description="Upload and process files (documents, images, etc.)",
    allowed_extensions=["txt", "pdf", "docx", "jpg", "png"]
)
def upload_file(file: FileUpload) -> dict:
    """Handle file uploads"""
    file_id = str(uuid.uuid4())
    
    file_info = {
        "id": file_id,
        "filename": file.filename,
        "size": len(file.content),
        "upload_date": datetime.now().isoformat(),
        "content_preview": file.content[:100].decode('utf-8', errors='ignore') if file.filename.endswith('.txt') else "Binary file"
    }
    
    files_db[file_id] = file_info
    
    return {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "size": len(file.content),
        "message": f"File '{file.filename}' uploaded successfully"
    }

@app.action(
    name="get_dashboard_stats",
    description="Get overview statistics including task counts, completion rates, and file uploads"
)
def get_dashboard_stats() -> dict:
    """Get dashboard overview statistics"""
    tasks = list(tasks_db.values())
    completed_tasks = [t for t in tasks if t.completed]
    
    # Priority breakdown
    priority_counts = {"high": 0, "medium": 0, "low": 0}
    for task in tasks:
        priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
    
    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "completion_rate": round(len(completed_tasks) / len(tasks) * 100, 1) if tasks else 0,
        "pending_tasks": len(tasks) - len(completed_tasks),
        "total_files": len(files_db),
        "priority_breakdown": priority_counts,
        "recent_activity": len([t for t in tasks if (datetime.now() - t.created_at).days < 7])
    }

# Optional: Add authentication if needed
# @app.action("login", "User authentication")
# @kalibr_auth(secret_key="your-secret-key")
# def login(username: str, password: str):
#     # Handle authentication
#     pass

if __name__ == "__main__":
    # For local development
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)