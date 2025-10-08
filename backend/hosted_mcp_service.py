#!/usr/bin/env python3
"""
QSP Compliance Checker - Hosted MCP Service
WebSocket and HTTP endpoint for Claude Desktop and ChatGPT integration
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import base64
import io

from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import os

# Import our existing MCP server components
from mcp_server import (
    handle_upload_qsp_document,
    handle_upload_iso_summary, 
    handle_list_documents,
    handle_run_clause_mapping,
    handle_run_compliance_analysis,
    handle_get_compliance_status,
    handle_get_dashboard_summary,
    handle_get_detailed_gaps,
    handle_get_clause_mappings,
    handle_query_specific_clause,
    server as mcp_server
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hosted-mcp-service")

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create FastAPI app for the hosted service
app = FastAPI(
    title="QSP Compliance Checker - Hosted MCP Service",
    description="AI-powered QSP compliance analysis for Claude and ChatGPT",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For family/friends, no auth restrictions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@app.get("/")
async def root():
    """Health check and service info"""
    return {
        "service": "QSP Compliance Checker - Hosted MCP",
        "status": "active",
        "version": "1.0.0",
        "compatible_with": ["Claude Desktop", "ChatGPT (with MCP support)"],
        "endpoints": {
            "websocket": "/mcp",
            "http_tools": "/tools/{tool_name}",
            "health": "/health"
        },
        "tools_available": 10,
        "setup_instructions": "/setup"
    }

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy", "timestamp": "2025-10-08T18:30:00Z"}

@app.get("/setup")
async def setup_instructions():
    """Setup instructions for users"""
    return {
        "title": "QSP Compliance Checker - Setup Instructions",
        "claude_desktop_config": {
            "instructions": "Add this to your Claude Desktop configuration file:",
            "config": {
                "mcpServers": {
                    "qsp-compliance": {
                        "url": f"wss://{os.environ.get('DOMAIN', 'your-domain.com')}/mcp",
                        "name": "QSP Compliance Checker"
                    }
                }
            },
            "config_file_locations": {
                "macOS": "~/Library/Application Support/Claude/claude_desktop_config.json",
                "Windows": "%APPDATA%/Claude/claude_desktop_config.json"
            }
        },
        "chatgpt_config": {
            "instructions": "When ChatGPT supports MCP, use this configuration:",
            "url": f"wss://{os.environ.get('DOMAIN', 'your-domain.com')}/mcp"
        },
        "test_instructions": [
            "1. Add configuration to your AI client",
            "2. Restart Claude Desktop or ChatGPT",  
            "3. Ask: 'What QSP compliance tools do you have access to?'",
            "4. Test with: 'Show me the current compliance status'"
        ]
    }

# WebSocket endpoint for MCP protocol
@app.websocket("/mcp")
async def mcp_websocket(websocket: WebSocket):
    """WebSocket endpoint for MCP protocol communication"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    logger.info(f"New MCP connection: {connection_id}")
    
    try:
        while True:
            # Receive message from client (Claude/ChatGPT)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received MCP message: {message.get('method', 'unknown')}")
            
            # Handle MCP protocol messages
            response = await handle_mcp_message(message)
            
            # Send response back
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]
        logger.info(f"Connection closed: {connection_id}")

async def handle_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP protocol messages"""
    
    method = message.get("method")
    params = message.get("params", {})
    message_id = message.get("id")
    
    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "prompts": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "qsp-compliance-checker",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = [
                {
                    "name": "upload_qsp_document",
                    "description": "Upload a QSP document for compliance analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string", "description": "Base64 encoded file content"},
                            "file_type": {"type": "string", "enum": ["txt", "docx"]}
                        },
                        "required": ["filename", "content", "file_type"]
                    }
                },
                {
                    "name": "upload_iso_summary", 
                    "description": "Upload ISO 13485:2024 Summary of Changes",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string", "description": "Base64 encoded file content"},
                            "file_type": {"type": "string", "enum": ["txt", "docx", "pdf"]}
                        },
                        "required": ["filename", "content", "file_type"]
                    }
                },
                {
                    "name": "list_documents",
                    "description": "List all uploaded QSP documents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "format": {"type": "string", "enum": ["summary", "detailed", "json"], "default": "summary"}
                        }
                    }
                },
                {
                    "name": "run_clause_mapping",
                    "description": "Run AI-powered clause mapping analysis",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "run_compliance_analysis", 
                    "description": "Run comprehensive compliance gap analysis",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_compliance_status",
                    "description": "Get current compliance status and metrics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "format": {"type": "string", "enum": ["summary", "detailed", "json"], "default": "summary"}
                        }
                    }
                },
                {
                    "name": "get_dashboard_summary",
                    "description": "Get dashboard overview with key metrics",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "format": {"type": "string", "enum": ["summary", "detailed", "json"], "default": "summary"}
                        }
                    }
                },
                {
                    "name": "get_detailed_gaps",
                    "description": "Get detailed compliance gaps with recommendations",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "severity": {"type": "string", "enum": ["all", "high", "medium", "low"], "default": "all"},
                            "format": {"type": "string", "enum": ["summary", "detailed", "json"], "default": "summary"}
                        }
                    }
                },
                {
                    "name": "get_clause_mappings",
                    "description": "Get AI clause mappings between QSP and ISO clauses",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string", "description": "Filter by document ID"},
                            "iso_clause": {"type": "string", "description": "Filter by ISO clause"},
                            "min_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "format": {"type": "string", "enum": ["summary", "detailed", "json"], "default": "summary"}
                        }
                    }
                },
                {
                    "name": "query_specific_clause",
                    "description": "Query compliance for specific ISO clause",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "clause": {"type": "string", "description": "ISO clause to query"},
                            "include_recommendations": {"type": "boolean", "default": True}
                        },
                        "required": ["clause"]
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Handle file uploads with base64 content
            if tool_name == "upload_qsp_document":
                arguments["base64_content"] = arguments.pop("content", "")
            elif tool_name == "upload_iso_summary":
                arguments["base64_content"] = arguments.pop("content", "")
            
            # Call the appropriate tool handler
            result = await call_tool_handler(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0", 
                "id": message_id,
                "result": {
                    "content": [{"type": "text", "text": result}]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message_id, 
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

async def call_tool_handler(tool_name: str, arguments: dict) -> str:
    """Call the appropriate tool handler and return text result"""
    
    handlers = {
        "upload_qsp_document": handle_upload_qsp_document,
        "upload_iso_summary": handle_upload_iso_summary,
        "list_documents": handle_list_documents,
        "run_clause_mapping": handle_run_clause_mapping,
        "run_compliance_analysis": handle_run_compliance_analysis,
        "get_compliance_status": handle_get_compliance_status,
        "get_dashboard_summary": handle_get_dashboard_summary,
        "get_detailed_gaps": handle_get_detailed_gaps,
        "get_clause_mappings": handle_get_clause_mappings,
        "query_specific_clause": handle_query_specific_clause
    }
    
    if tool_name not in handlers:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        result = await handlers[tool_name](arguments)
        return result[0].text if result and len(result) > 0 else "No result"
    except Exception as e:
        logger.error(f"Error calling {tool_name}: {e}")
        return f"Error executing {tool_name}: {str(e)}"

# HTTP endpoints as fallback (for testing and alternative access)
@app.post("/tools/{tool_name}")
async def call_tool_http(tool_name: str, arguments: dict):
    """HTTP endpoint for calling tools (alternative to WebSocket)"""
    result = await call_tool_handler(tool_name, arguments)
    return {"result": result}

# Simple file upload endpoint for testing
@app.post("/upload/qsp")
async def upload_qsp_http(file: UploadFile = File(...)):
    """HTTP file upload for QSP documents"""
    content = await file.read()
    base64_content = base64.b64encode(content).decode('utf-8')
    
    file_type = "docx" if file.filename.endswith('.docx') else "txt"
    
    arguments = {
        "filename": file.filename,
        "base64_content": base64_content,
        "file_type": file_type
    }
    
    result = await call_tool_handler("upload_qsp_document", arguments)
    return {"message": result}

@app.post("/upload/iso")
async def upload_iso_http(file: UploadFile = File(...)):
    """HTTP file upload for ISO summary"""
    content = await file.read()
    base64_content = base64.b64encode(content).decode('utf-8')
    
    file_type = "docx" if file.filename.endswith('.docx') else "txt"
    
    arguments = {
        "filename": file.filename,
        "base64_content": base64_content,
        "file_type": file_type
    }
    
    result = await call_tool_handler("upload_iso_summary", arguments)
    return {"message": result}

# Start the hosted service
if __name__ == "__main__":
    uvicorn.run(
        "hosted_mcp_service:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False
    )