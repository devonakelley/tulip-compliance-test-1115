# QSP Compliance Checker - Dual Interface Documentation

## Overview
The QSP Compliance Checker provides **two interfaces** for maximum flexibility:

1. **Web UI**: User-friendly interface for quality teams, auditors, and managers
2. **MCP Server**: Direct integration with Claude Desktop/ChatGPT for AI-powered analysis

## 🌐 Web Interface

### Access
- **URL**: https://compliantsuite.preview.emergentagent.com
- **Features**: Dashboard, Document Upload, Analysis Workflow, Gap Reports

### Web UI Capabilities
- ✅ Document upload (.docx, .txt files)
- ✅ ISO 13485:2024 Summary processing  
- ✅ Visual dashboard with compliance scores
- ✅ Interactive gap analysis with recommendations
- ✅ Progress tracking during AI analysis
- ✅ Export-ready reports

### Best for:
- Quality managers reviewing compliance status
- Auditors generating reports
- Teams needing visual dashboards
- Non-technical users

---

## 🤖 MCP Server Interface

### Setup for Claude Desktop

1. **Add to Claude Desktop Config**:
   ```json
   {
     "mcpServers": {
       "qsp-compliance-checker": {
         "command": "python3",
         "args": ["/app/backend/mcp_server.py"],
         "env": {
           "MONGO_URL": "mongodb://localhost:27017",
           "DB_NAME": "test_database",
           "EMERGENT_LLM_KEY": "sk-emergent-f33C62eB0958b4547F"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Test Connection**:
   ```
   Human: Can you list the available QSP compliance tools?
   Claude: [Lists all 10 MCP tools]
   ```

### Available MCP Tools

#### 📄 Document Management
- `upload_qsp_document` - Upload QSP files (path or base64)
- `upload_iso_summary` - Upload ISO summary document
- `list_documents` - Show all uploaded documents

#### 🔍 Analysis Tools  
- `run_clause_mapping` - AI-powered clause mapping
- `run_compliance_analysis` - Comprehensive gap analysis
- `get_compliance_status` - Current compliance metrics

#### 📊 Reporting Tools
- `get_dashboard_summary` - Overview dashboard
- `get_detailed_gaps` - Compliance gaps with recommendations
- `get_clause_mappings` - AI mappings between QSP and ISO clauses
- `query_specific_clause` - Query specific ISO clause coverage

### MCP Usage Examples

#### Basic Workflow
```
Human: Upload this QSP document and analyze it for ISO 13485:2024 compliance.
Claude: I'll help you upload and analyze your QSP document. Let me use the upload tool...
[Uses upload_qsp_document tool]
[Uses run_clause_mapping tool]
[Uses run_compliance_analysis tool]
[Provides summary with specific gaps and recommendations]
```

#### Specific Queries
```
Human: Which QSP documents cover ISO clause 7.3.10 Design transfer?
Claude: [Uses query_specific_clause tool and provides detailed analysis]