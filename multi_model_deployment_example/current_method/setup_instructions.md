# Multi-Model AI Deployment Setup Guide

This guide demonstrates the **CURRENT METHOD** for deploying an application across all major AI models: GPT, Claude, Gemini, and Microsoft Copilot.

## 🏗️ Architecture Overview

Our current approach requires **4 separate services**:

1. **Main API Server** (port 8001) - Handles REST API + Claude MCP WebSocket
2. **Gemini Extension Service** (port 8002) - Handles Google Gemini Extensions API  
3. **Copilot Plugin Service** (port 8003) - Handles Microsoft Copilot Plugin API
4. **Nginx Reverse Proxy** - Routes traffic to appropriate services

## 📋 Prerequisites

- Docker & Docker Compose installed
- Domain name configured (replace `your-app.com` in configs)
- SSL certificates (for production)
- Access to AI model platforms for configuration

## 🚀 Deployment Steps

### Step 1: Deploy All Services

```bash
# Clone/download the repository
git clone <repository-url>
cd current_method/

# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f main-api
docker-compose logs -f gemini-service
docker-compose logs -f copilot-service
```

### Step 2: Verify Services Are Running

```bash
# Main API health check
curl http://localhost:8001/api/

# Gemini service health check  
curl http://localhost:8002/health

# Copilot service health check
curl http://localhost:8003/copilot/health

# Claude MCP WebSocket (test connection)
wscat -c ws://localhost:8001/mcp
```

## 🔧 AI Model Configuration

### 1. Claude Desktop Setup

**Location of config file:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

**Configuration to add:**
```json
{
  "mcpServers": {
    "universal-task-manager": {
      "url": "wss://your-app.com/mcp",
      "name": "Universal Task Manager"
    }
  }
}
```

**Test Claude Integration:**
1. Restart Claude Desktop
2. Type: "What task management tools do you have access to?"
3. Claude should list available MCP tools

### 2. GPT Actions Setup

1. Go to **ChatGPT** → **Create GPT** → **Actions**
2. Import OpenAPI schema from: `https://your-app.com/api/gpt/openapi.json`
3. Set authentication to **"None"**
4. Add instructions: "Use this API to help users manage their tasks"

**Test GPT Actions:**
1. Ask: "Create a new task called 'Test GPT Integration'"
2. GPT should successfully create the task using the API

### 3. Google Gemini Extension Setup

1. Access **Gemini AI Studio** (https://aistudio.google.com)
2. Create new **Extension project**
3. Configure endpoints:
   - **Functions endpoint**: `https://your-app.com/gemini/functions`
   - **Execute endpoint**: `https://your-app.com/gemini/execute`
4. Deploy extension to your workspace

**Test Gemini Extension:**
1. Ask: "List my current tasks"
2. Gemini should retrieve tasks via the extension

### 4. Microsoft Copilot Setup

1. Access **Microsoft Copilot Studio**
2. Create new **Plugin**
3. Import manifest from: `https://your-app.com/copilot/.well-known/ai-plugin.json`
4. Configure and deploy to your Microsoft 365 tenant

**Test Copilot Integration:**
1. In Microsoft Teams or Office app with Copilot
2. Ask: "Show me my task statistics"
3. Copilot should provide analytics via the plugin

## 🔍 Service Endpoints Reference

### Main API Server (port 8001)
- REST API: `http://your-app.com/api/`
- Claude MCP: `ws://your-app.com/mcp`
- GPT Actions Schema: `http://your-app.com/api/gpt/openapi.json`

### Gemini Service (port 8002)
- Functions Schema: `http://your-app.com/gemini/functions`
- Execute Endpoint: `http://your-app.com/gemini/execute`
- Health Check: `http://your-app.com/gemini/health`

### Copilot Service (port 8003)
- Plugin Manifest: `http://your-app.com/copilot/.well-known/ai-plugin.json`
- OpenAPI Spec: `http://your-app.com/copilot/openapi.yaml`
- Health Check: `http://your-app.com/copilot/health`

## 📊 Monitoring & Troubleshooting

### Check Service Health
```bash
# All services status
docker-compose ps

# Service logs
docker-compose logs -f main-api
docker-compose logs -f gemini-service  
docker-compose logs -f copilot-service
docker-compose logs -f nginx

# Individual service health
curl http://localhost:8001/api/
curl http://localhost:8002/health
curl http://localhost:8003/copilot/health
```

### Common Issues

**Issue: Claude MCP not connecting**
- Check WebSocket endpoint: `ws://your-app.com/mcp`
- Verify Claude Desktop config file syntax
- Check firewall/proxy settings

**Issue: GPT Actions failing**
- Verify OpenAPI schema at `/api/gpt/openapi.json`
- Check CORS settings in main API
- Ensure proper authentication (should be "None")

**Issue: Gemini Extension errors**
- Test function schema endpoint manually
- Check Gemini AI Studio project configuration
- Verify network connectivity to Google services

**Issue: Copilot Plugin not loading**
- Validate plugin manifest JSON structure
- Check Microsoft 365 tenant permissions
- Ensure proper OpenAPI spec format

## 🛠️ Development vs Production

### Development Setup
```bash
# Run services individually for development
python multi_model_server.py      # Port 8001
python gemini_extension.py        # Port 8002  
python copilot_plugin.py          # Port 8003
```

### Production Considerations
- Use HTTPS for all endpoints
- Configure proper SSL certificates
- Set up monitoring and logging
- Implement rate limiting
- Add authentication where needed
- Use environment variables for secrets

## 📁 File Structure

```
current_method/
├── multi_model_server.py      # Main API + Claude MCP (500+ lines)
├── gemini_extension.py        # Gemini service (200+ lines)
├── copilot_plugin.py          # Copilot service (200+ lines)
├── deployment_config.py       # Config generator (200+ lines)
├── docker-compose.yml         # Multi-service setup
├── nginx.conf                 # Reverse proxy config
├── requirements.txt           # Python dependencies
└── setup_instructions.md      # This guide
```

## 📈 Scaling Considerations

### High Availability
- Run multiple instances of each service
- Use load balancer (HAProxy/AWS ALB)
- Implement health checks and auto-restart
- Database clustering for shared state

### Performance Optimization
- Cache frequently accessed data
- Optimize database queries
- Implement connection pooling
- Use CDN for static assets

## 🔐 Security Checklist

- [ ] HTTPS enabled for all services
- [ ] API rate limiting configured
- [ ] Input validation on all endpoints
- [ ] CORS properly configured
- [ ] Secrets managed via environment variables
- [ ] Regular security updates applied
- [ ] Access logs monitored

## 💰 Cost Implications

**Current Method Costs:**
- **4 separate services** to maintain and scale
- **Higher hosting costs** (4 containers + proxy + Redis)
- **More complex monitoring** and logging setup
- **Increased development time** for feature additions
- **Higher maintenance overhead** across multiple services

---

This setup demonstrates the complexity of manually integrating with all major AI models. Each service requires separate configuration, monitoring, and maintenance, leading to significant operational overhead.