#!/usr/bin/env python3
"""
Test the MCP server tools locally
"""

import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

from mcp_server import (
    handle_list_documents, 
    handle_get_compliance_status,
    handle_get_dashboard_summary
)

async def test_mcp_tools():
    """Test MCP server tools"""
    print("🧪 Testing MCP Server Tools...\n")
    
    # Test 1: List documents
    print("1️⃣ Testing list_documents...")
    try:
        result = await handle_list_documents({"format": "summary"})
        print(f"✅ Success: {result[0].text[:100]}...\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")
    
    # Test 2: Get compliance status
    print("2️⃣ Testing get_compliance_status...")
    try:
        result = await handle_get_compliance_status({"format": "summary"})
        print(f"✅ Success: {result[0].text[:100]}...\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")
    
    # Test 3: Get dashboard summary
    print("3️⃣ Testing get_dashboard_summary...")
    try:
        result = await handle_get_dashboard_summary({"format": "summary"})
        print(f"✅ Success: {result[0].text[:100]}...\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")
    
    print("🎉 MCP Server Tools Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())