# Real Kalibr SDK Deployment Guide

This guide shows how to use the **actual Kalibr SDK** (v1.0.7) from PyPI to deploy applications across all AI models.

## 🚀 Quick Start

### Install Kalibr
```bash
pip install kalibr==1.0.7
```

### Run Locally
```bash
# Simple task manager example
python -m kalibr serve task_manager_example.py

# Full QSP Compliance Checker
python -m kalibr serve qsp_compliance_kalibr.py
```

## 📊 What You Get

When you run `python -m kalibr serve`, the Kalibr SDK automatically provides:

### 🎯 Multi-Model Support
- **Claude MCP**: WebSocket endpoint for Claude Desktop
- **GPT Actions**: OpenAPI schema for ChatGPT
- **Gemini Extensions**: Function schemas for Google Gemini
- **Microsoft Copilot**: Plugin manifests for Microsoft 365

### 🛠️ API Features  
- **Function-based API**: Clean `@app.action()` decorators
- **Type Safety**: Pydantic models for request/response validation
- **Auto Documentation**: Schemas generated from function signatures
- **Error Handling**: Consistent error responses across all AI models

## 📝 Code Comparison

### ❌ Our Previous Custom MCP (700+ lines)
```python
# Complex WebSocket handling
@app.websocket("/mcp")
async def mcp_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # ... 100+ lines of MCP protocol handling

# Manual schema generation  
def get_claude_tools_schema() -> List[dict]:
    return [
        {
            "name": "upload_qsp_document",
            "description": "Upload a QSP document",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    # ... 20+ lines per tool
                }
            }
        }
    ]

# Duplicate implementations for each AI model
async def execute_claude_tool(tool_name: str, arguments: dict):
    # Claude-specific handling...
    
async def execute_gpt_action(action_name: str, params: dict):
    # GPT-specific handling...
```

### ✅ Kalibr SDK (80 lines)
```python
from kalibr.kalibr_app import KalibrApp

app = KalibrApp(title="QSP Compliance Checker")

@app.action(
    name="upload_qsp_document",
    description="Upload a QSP document (.docx or .txt) for ISO 13485 compliance analysis"
)
def upload_qsp_document(filename: str, content_base64: str, file_type: str) -> dict:
    """Upload and process a QSP document"""
    # Just write your business logic - Kalibr handles the rest!
    return {"success": True, "message": "Document uploaded"}
```

## 🔧 Real Implementation Examples

### 1. Task Manager (Simple)
```python
from kalibr.kalibr_app import KalibrApp

app = KalibrApp(title="Task Manager")

@app.action("create_task", "Create a new task")
def create_task(title: str, priority: str = "medium") -> dict:
    # Your logic here
    return {"success": True, "task_id": "123"}

@app.action("list_tasks", "List all tasks")  
def list_tasks(completed: bool = None) -> dict:
    # Your logic here
    return {"tasks": [], "count": 0}
```

### 2. QSP Compliance (Advanced)
```python
from kalibr.kalibr_app import KalibrApp

app = KalibrApp(title="QSP Compliance Checker")

@app.action("upload_qsp_document", "Upload QSP document for analysis")
def upload_qsp_document(filename: str, content_base64: str, file_type: str) -> dict:
    # Decode content, extract text, parse sections
    return {"success": True, "document_id": "abc123"}

@app.action("run_compliance_analysis", "Analyze compliance gaps")
def run_compliance_analysis() -> dict:
    # AI-powered analysis logic
    return {"gaps_found": 3, "overall_score": 87.5}
```

## 🎯 Key Benefits

### Development Speed
- **Write Once**: Single function definitions work across all AI models
- **No Boilerplate**: No WebSocket handling, schema generation, or protocol management
- **Type Safe**: Pydantic validation built-in

### Deployment Simplicity  
- **Single Command**: `python -m kalibr serve` runs everything
- **Auto Endpoints**: All AI model endpoints generated automatically
- **Production Ready**: Built-in error handling and validation

### Maintenance
- **One Codebase**: No duplicate implementations per AI model
- **Framework Updates**: Kalibr handles protocol changes and new AI models
- **Clean APIs**: Easy to test, debug, and extend

## 📈 Scaling Comparison

| Feature | Custom MCP | Kalibr SDK |
|---------|------------|------------|
| **Lines of Code** | 700+ | 80 |
| **AI Models** | 1 (Claude) | 4+ (GPT, Claude, Gemini, Copilot) |
| **WebSocket Code** | ~200 lines | 0 lines |
| **Schema Generation** | Manual | Automatic |
| **Error Handling** | Custom | Built-in |
| **New AI Models** | Weeks of work | Automatic support |
| **Maintenance** | High | Low |

## 🚀 Next Steps

1. **Try the Examples**: Run both `task_manager_example.py` and `qsp_compliance_kalibr.py`
2. **Test AI Models**: Use the generated endpoints with Claude, GPT, etc.
3. **Deploy**: Use `kalibr deploy` for production (when available)
4. **Extend**: Add more `@app.action()` functions for your use cases

## 🎉 Summary

The Kalibr SDK transforms multi-model AI integration from a complex engineering challenge into simple function definitions. What took us 700+ lines of custom code is now accomplished in 80 lines with better functionality and broader AI model support.

**The same QSP Compliance features that required:**
- ❌ Custom WebSocket servers
- ❌ Manual protocol handling  
- ❌ Duplicate code per AI model
- ❌ Complex deployment setup

**Now work with just:**
- ✅ Clean function definitions
- ✅ Automatic multi-model support
- ✅ Built-in validation and errors
- ✅ One-command deployment