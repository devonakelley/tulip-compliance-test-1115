#!/bin/bash
# QSP Compliance Checker MCP Server Startup Script

echo "🚀 Starting QSP Compliance Checker MCP Server..."

# Set environment variables
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="test_database"
export EMERGENT_LLM_KEY="sk-emergent-f33C62eB0958b4547F"

# Change to backend directory
cd /app/backend

# Start MCP server
python3 mcp_server.py

echo "✅ MCP Server started successfully!"
echo "📋 Available Tools:"
echo "  • upload_qsp_document - Upload QSP documents for analysis"
echo "  • upload_iso_summary - Upload ISO 13485:2024 summary" 
echo "  • list_documents - List uploaded documents"
echo "  • run_clause_mapping - AI-powered clause mapping"
echo "  • run_compliance_analysis - Gap analysis"
echo "  • get_compliance_status - Overall status"
echo "  • get_dashboard_summary - Dashboard overview"
echo "  • get_detailed_gaps - Compliance gaps with recommendations"
echo "  • get_clause_mappings - AI mappings between QSP and ISO"
echo "  • query_specific_clause - Query specific ISO clause coverage"
echo ""
echo "🔗 Integration: Use this MCP server with Claude Desktop or ChatGPT"