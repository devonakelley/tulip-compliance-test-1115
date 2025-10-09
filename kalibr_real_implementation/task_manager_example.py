"""
Simple Task Manager - Real Kalibr SDK Example
This demonstrates the basics of using the actual Kalibr SDK from PyPI.
"""

from kalibr.kalibr_app import KalibrApp
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Initialize Kalibr App
app = KalibrApp(
    title="Universal Task Manager",
    description="Simple task management that works with all AI models"
)

# Data model
class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    completed: bool = False
    priority: str = "medium"  # low, medium, high
    created_at: datetime

# In-memory storage
tasks: dict[str, Task] = {}

@app.action(
    name="create_task",
    description="Create a new task with title, description and priority"
)
def create_task(title: str, description: str = "", priority: str = "medium") -> dict:
    """Create a new task"""
    task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        priority=priority,
        created_at=datetime.now()
    )
    
    tasks[task.id] = task
    
    return {
        "success": True,
        "task_id": task.id,
        "message": f"Created task: {title}"
    }

@app.action(
    name="list_tasks",
    description="List all tasks, optionally filter by completion status"
)
def list_tasks(completed: Optional[bool] = None) -> dict:
    """List tasks with optional filtering"""
    task_list = list(tasks.values())
    
    if completed is not None:
        task_list = [t for t in task_list if t.completed == completed]
    
    # Sort by creation time (newest first)
    task_list.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "tasks": [task.dict() for task in task_list],
        "count": len(task_list),
        "filter": f"completed={completed}" if completed is not None else "all"
    }

@app.action(
    name="update_task",
    description="Update a task by ID - change title, description, completion status, or priority"
)
def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
    priority: Optional[str] = None
) -> dict:
    """Update an existing task"""
    if task_id not in tasks:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    task = tasks[task_id]
    
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
        "message": f"Updated task: {task.title}"
    }

@app.action(
    name="delete_task",
    description="Delete a task by ID"
)
def delete_task(task_id: str) -> dict:
    """Delete a task"""
    if task_id not in tasks:
        return {"success": False, "error": f"Task {task_id} not found"}
    
    task = tasks.pop(task_id)
    
    return {
        "success": True,
        "message": f"Deleted task: {task.title}"
    }

@app.action(
    name="get_stats",
    description="Get task statistics - total, completed, by priority"
)
def get_stats() -> dict:
    """Get task statistics"""
    all_tasks = list(tasks.values())
    completed_tasks = [t for t in all_tasks if t.completed]
    
    priority_counts = {"high": 0, "medium": 0, "low": 0}
    for task in all_tasks:
        priority_counts[task.priority] += 1
    
    return {
        "total_tasks": len(all_tasks),
        "completed_tasks": len(completed_tasks),
        "pending_tasks": len(all_tasks) - len(completed_tasks),
        "completion_rate": round((len(completed_tasks) / len(all_tasks) * 100) if all_tasks else 0, 1),
        "priority_breakdown": priority_counts
    }

if __name__ == "__main__":
    print("Task Manager - Kalibr SDK Example")
    print("Run with: python -m kalibr serve task_manager_example.py")
    print("\nFeatures:")
    print("✅ Create, list, update, delete tasks")
    print("✅ Task statistics and filtering")
    print("✅ Automatic multi-model support (GPT, Claude, Gemini, Copilot)")
    print("✅ Clean function-based API definitions")