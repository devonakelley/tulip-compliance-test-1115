# 🚀 QSP Compliance Checker - MCP Integration Guide

## ✅ Status: READY FOR CLAUDE & CHATGPT

Your QSP Compliance Checker now has **dual interface** support:

1. **Web UI**: https://compliancerag-1.preview.emergentagent.com (Active ✅)
2. **MCP WebSocket**: `wss://qsp-compliance.preview.emergentagent.com/mcp` (Active ✅)

---

## 📋 For Non-Technical Users: Setup Instructions

### 🔹 **Claude Desktop Setup**

1. **Find your Claude Desktop config file:**
   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Add this configuration:**
   ```json
   {
     "mcpServers": {
       "qsp-compliance": {
         "url": "wss://qsp-compliance.preview.emergentagent.com/mcp",
         "name": "QSP Compliance Checker"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Test the connection:**
   - Ask Claude: *"What QSP compliance tools do you have access to?"*
   - Claude should list 10 available tools

### 🔹 **ChatGPT Setup** (When MCP Support Arrives)

ChatGPT doesn't have native MCP support yet, but when it does:

1. **Add MCP Server:**
   - URL: `wss://qsp-compliance.preview.emergentagent.com/mcp`
   - Name: QSP Compliance Checker

2. **Test connection same as Claude**

---

## 🛠️ **Available MCP Tools**

Once connected, you can ask Claude/ChatGPT to use these tools:

### 📄 **Document Management**
- `upload_qsp_document` - Upload QSP files
- `upload_iso_summary` - Upload ISO 13485:2024 summary  
- `list_documents` - Show uploaded documents

### 🔍 **Analysis Tools**
- `run_clause_mapping` - AI-powered clause mapping
- `run_compliance_analysis` - Comprehensive gap analysis
- `get_compliance_status` - Current compliance metrics

### 📊 **Reporting Tools**
- `get_dashboard_summary` - Overview dashboard
- `get_detailed_gaps` - Compliance gaps with recommendations
- `get_clause_mappings` - AI mappings between QSP and ISO
- `query_specific_clause` - Query specific ISO clause coverage

---

## 💬 **Usage Examples**

### Basic Workflow:
```
You: "I need to check if my QSP documents comply with ISO 13485:2024 changes"

Claude: "I'll help you analyze your QSP documents for ISO 13485:2024 compliance. Let me first check what documents you have uploaded..."
[Uses list_documents tool]
[Shows current status]
"Would you like to upload a new QSP document or run analysis on existing ones?"

You: [Pastes document content] "Analyze this QSP for compliance"

Claude: [Uses upload_qsp_document tool]
[Uses run_clause_mapping tool]
[Uses run_compliance_analysis tool]
[Provides detailed gap analysis with specific recommendations]
```

### Specific Queries:
```
You: "Which of my QSPs cover ISO clause 7.3.10 Design transfer?"
Claude: [Uses query_specific_clause tool and provides detailed analysis]

You: "What are our high-priority compliance gaps?"
Claude: [Uses get_detailed_gaps with severity="high"]

You: "Show me the current compliance dashboard"
Claude: [Uses get_dashboard_summary and formats nicely]
```

---

## 🎯 **What This Enables**

### **For Quality Managers:**
- Upload 69 QSPs via Claude conversation
- Get instant compliance analysis
- Receive specific gap recommendations
- Query specific clauses or requirements

### **For Auditors:**  
- Real-time compliance status via AI chat
- Export-ready gap analysis through conversation
- Evidence extraction for audit reports

### **For Technical Teams:**
- Programmatic access to compliance data
- Integration with existing workflows
- AI-powered regulatory guidance

---

## ✅ **Current System Status**

- **Web Interface**: ✅ Fully functional
- **MCP WebSocket**: ✅ Ready for connections
- **Document Processing**: ✅ Supports .docx, .txt
- **AI Analysis**: ✅ GPT-4o powered clause mapping
- **Gap Analysis**: ✅ ISO 13485:2024 compliance checking
- **Real-time Updates**: ✅ Live compliance scoring

**You're ready to use both interfaces!** 

Family and friends can now:
1. Use the web dashboard for visual analysis
2. Chat with Claude/ChatGPT for AI-powered compliance insights
3. Upload documents through either interface
4. Get instant regulatory guidance through conversation

---

## 🚨 **Troubleshooting**

### If Claude doesn't see the tools:
1. **Check config file location** - Different OS have different paths
2. **Restart Claude Desktop** - Required after config changes  
3. **Check JSON syntax** - Use a JSON validator
4. **Test connection** - Ask "What tools do you have access to?"

### If WebSocket fails:
1. **Check internet connection**
2. **Try https://compliancerag-1.preview.emergentagent.com** - Should show web interface
3. **Contact us** - We can check server logs

**The system is now ready for production use with both traditional and AI-native interfaces! 🎉**