# QSP Compliance Checker - End User Deployment Guide

## 🎯 For Non-Technical Users: How to Use This with Claude/ChatGPT

### Current Status:
- ✅ **Web Interface**: Ready to use at https://iso13485-tool.preview.emergentagent.com
- ⚠️ **MCP Integration**: Needs packaging for end-user deployment

## 📦 What We Need to Create for Distribution

### 1. **Standalone Installation Package**
```
qsp-compliance-mcp/
├── install.bat (Windows)
├── install.sh (Mac/Linux) 
├── mcp_server.py
├── requirements.txt
├── config_template.json
├── sample_documents/
└── README.md
```

### 2. **One-Click Installer Script**
- Installs Python dependencies
- Sets up local database (SQLite for simplicity)
- Creates Claude Desktop configuration
- Provides test commands

### 3. **User Setup Steps (After We Package It)**

#### For Claude Desktop:
1. **Download**: Download `qsp-compliance-mcp.zip`
2. **Run Installer**: Double-click `install.bat` (Windows) or `install.sh` (Mac)
3. **Claude Config**: Installer automatically adds to Claude Desktop config
4. **Restart Claude**: Restart Claude Desktop
5. **Test**: Ask Claude "What QSP compliance tools do you have?"

#### For ChatGPT:
- **Status**: GPT doesn't have native MCP support yet
- **When Available**: Same installation process will work

## 🔄 Alternative: Hosted MCP Service

### What This Would Look Like:
- **User Signs Up**: Creates account on your platform
- **Gets API Key**: Receives personal API key
- **Claude Config**: Adds hosted MCP endpoint to Claude
- **Usage**: Uses through Claude with authentication

### Example Claude Config:
```json
{
  "mcpServers": {
    "qsp-compliance": {
      "url": "wss://qsp-compliance.your-domain.com/mcp",
      "apiKey": "user-specific-api-key"
    }
  }
}
```

## 💡 Recommended Approach

### Phase 1: **Local Installer Package**
- Create downloadable installer
- Users run locally with their documents
- Full privacy - documents stay on their machine
- Works offline after initial setup

### Phase 2: **Hosted Service** (Later)
- Cloud-based MCP endpoint  
- Multi-user with authentication
- Document storage in cloud
- Subscription/usage-based pricing

## 📋 What Needs to Be Built

### Immediate (for local deployment):
1. **Package the MCP server** with local SQLite database
2. **Create installation scripts** for Windows/Mac/Linux
3. **Auto-configure Claude Desktop** during installation
4. **Provide sample documents** and test procedures
5. **Create troubleshooting guide**

### Future (for hosted service):
1. **Authentication system** for multi-user access
2. **WebSocket MCP endpoint** for remote connections
3. **Document storage** and user management
4. **Billing/subscription** system