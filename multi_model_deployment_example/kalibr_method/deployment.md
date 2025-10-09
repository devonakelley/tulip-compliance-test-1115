# Kalibr SDK Deployment Guide

This demonstrates the **KALIBR SDK METHOD** for deploying the same application across all major AI models with dramatically less complexity.

## 🎯 Single File, All Models

**Total Implementation:** 1 file, 80 lines of code
**Supports:** GPT Actions, Claude MCP, Gemini Extensions, Microsoft Copilot

## 🚀 Quick Deployment

### Local Development
```bash
# Install Kalibr SDK
pip install kalibr

# Run the application - automatically supports ALL AI models
kalibr serve universal_task_manager.py
```

This single command provides:
- ✅ **Claude MCP**: `ws://localhost:8000/mcp`
- ✅ **GPT Actions**: `http://localhost:8000/openapi.json` 
- ✅ **Gemini Extensions**: `http://localhost:8000/schemas/gemini`
- ✅ **Microsoft Copilot**: `http://localhost:8000/schemas/copilot`

### Production Deployment

```bash
# Deploy to Fly.io - one command for all models
kalibr deploy universal_task_manager.py --platform fly --name universal-task-manager

# Alternative deployment options
kalibr deploy universal_task_manager.py --platform aws --region us-east-1
kalibr deploy universal_task_manager.py --platform gcp --region us-central1
kalibr deploy universal_task_manager.py --platform azure --region eastus
```

## 🔧 AI Model Setup

Once deployed, Kalibr automatically generates all necessary configurations:

### 1. Claude Desktop (Automatic)

**Generated config for Claude Desktop:**
```json
{
  "mcpServers": {
    "universal-task-manager": {
      "url": "wss://universal-task-manager.fly.dev/mcp",
      "name": "Universal Task Manager"
    }
  }
}
```

**Setup:**
1. Copy the config to your Claude Desktop configuration file
2. Restart Claude Desktop
3. Ask: "What task management tools do you have access to?"

### 2. GPT Actions (Automatic)

**Generated OpenAPI schema:** `https://universal-task-manager.fly.dev/openapi.json`

**Setup:**
1. Go to ChatGPT → Create GPT → Actions
2. Import schema from the URL above
3. Set authentication to "None"
4. Test: "Create a new task called 'Test GPT Integration'"

### 3. Gemini Extensions (Automatic)

**Generated schema:** `https://universal-task-manager.fly.dev/schemas/gemini`

**Setup:**
1. Access Gemini AI Studio
2. Import the generated function schemas
3. Configure endpoints (auto-detected)
4. Test: "List my current tasks"

### 4. Microsoft Copilot (Automatic)

**Generated manifest:** `https://universal-task-manager.fly.dev/schemas/copilot`

**Setup:**
1. Access Microsoft Copilot Studio
2. Import the auto-generated plugin manifest
3. Deploy to your Microsoft 365 tenant
4. Test: "Show me my task statistics"

## 📊 What Kalibr Handles Automatically

### Schema Generation
- **MCP Protocol**: JSON-RPC tool definitions for Claude
- **OpenAPI 3.0**: Complete specification for GPT Actions
- **Gemini Functions**: Google's function calling format
- **Copilot Plugins**: Microsoft's plugin manifest format

### Protocol Handling
- **WebSocket Management**: For Claude MCP connections
- **HTTP Endpoints**: For GPT Actions and other models
- **Authentication**: JWT tokens, API keys (when needed)
- **Error Handling**: Consistent error responses across models

### File Upload Support
- **Base64 Encoding**: Automatic for models that require it
- **Multipart Forms**: For standard HTTP uploads
- **Type Validation**: Based on `allowed_extensions`
- **Size Limits**: Configurable per endpoint

### Analytics & Monitoring
- **Request Tracking**: Automatic logging of all API calls
- **Performance Metrics**: Response times, error rates
- **Usage Analytics**: Per-function call statistics
- **Custom Events**: Via `app.record_custom_event()`

## 🔍 Testing All Models

### Test Commands

```bash
# Test Claude MCP (requires wscat: npm install -g wscat)
wscat -c wss://universal-task-manager.fly.dev/mcp

# Test GPT Actions schema
curl https://universal-task-manager.fly.dev/openapi.json

# Test Gemini functions
curl https://universal-task-manager.fly.dev/schemas/gemini

# Test Copilot manifest
curl https://universal-task-manager.fly.dev/schemas/copilot

# Test core functionality
curl -X POST https://universal-task-manager.fly.dev/proxy/create_task \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "priority": "high"}'
```

## 🛠️ Advanced Configuration

### Add Authentication
```python
from kalibr.auth_helpers import kalibr_auth, KalibrAuth

auth = KalibrAuth(secret_key="your-secret-key")

@app.action("protected_action", "Requires authentication")
@kalibr_auth(auth_system=auth)
def protected_function(user_id: str = Depends(auth.get_current_user)):
    return {"message": f"Hello {user_id}"}
```

### Custom Analytics Backend
```python
from kalibr.analytics import MongoAnalyticsBackend

@kalibr_analytics(
    storage=MongoAnalyticsBackend("mongodb://localhost:27017"),
    auto_track=True
)
class MyApp(KalibrApp):
    pass
```

### Session Management
```python
@app.session_action("stateful_action", "Maintains user session state")
def stateful_function(session: Session, data: str):
    session.set("last_data", data)
    return {"previous": session.get("last_data")}
```

### Streaming Responses
```python
@app.stream_action("generate_report", "Streams report generation progress")
async def generate_report(num_items: int):
    for i in range(num_items):
        await asyncio.sleep(0.1)
        yield {"progress": (i + 1) / num_items * 100, "item": i + 1}
```

## 📈 Scalability & Performance

### Auto-Scaling
Kalibr deployments automatically scale based on:
- Request volume
- Response times
- Memory usage
- Custom metrics

### Built-in Optimizations
- **Connection pooling** for database connections
- **Request deduplication** for identical calls
- **Response caching** for expensive operations
- **Load balancing** across multiple instances

## 🔐 Security Features

### Built-in Security
- **Input validation** based on function signatures
- **Rate limiting** per endpoint and user
- **CORS handling** for web applications
- **Request sanitization** to prevent injection attacks

### Authentication Options
- **JWT tokens** with automatic refresh
- **API keys** with scope-based permissions
- **OAuth integration** (Google, GitHub, etc.)
- **Custom auth providers** via plugins

## 💰 Cost Comparison

| Aspect | Current Method | Kalibr SDK |
|--------|----------------|------------|
| **Development Time** | 1-2 weeks | 2-3 hours |
| **Code Maintenance** | 1,200+ lines | 80 lines |
| **Infrastructure** | 4 services + proxy | 1 service |
| **Hosting Costs** | ~$200/month | ~$30/month |
| **Monitoring Setup** | Complex (4 services) | Built-in |
| **Adding New Features** | Update 4 services | Update 1 function |

## 🎉 Summary

**With Kalibr SDK:**
- ✅ **93% less code** to write and maintain
- ✅ **Single deployment** works with all AI models
- ✅ **Automatic schema generation** from function signatures
- ✅ **Built-in authentication, analytics, and error handling**
- ✅ **Future-proof** as new AI models are added to the framework
- ✅ **10x faster development** and deployment process

**The same functionality that takes 1,200+ lines and 4 services with the current method is achieved in just 80 lines and 1 service with Kalibr SDK.**