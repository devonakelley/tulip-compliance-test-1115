#!/usr/bin/env python3
"""
Test script to verify the clean QSP Compliance System
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_system():
    print("🧪 Testing Enterprise QSP Compliance System (Clean Version)")
    
    try:
        # Test configuration
        from backend.config import settings
        print("✅ Configuration loaded successfully")
        print(f"   MongoDB: {settings.MONGO_URL}")
        print(f"   LLM Key: {'Configured' if settings.EMERGENT_LLM_KEY else 'Not configured'}")
        print(f"   Debug Mode: {settings.DEBUG}")
        
        # Test models
        from backend.models import SystemStatus, UploadResponse
        print("✅ Pydantic models loaded successfully")
        
        # Test core components can be imported
        from backend.core.document_processor import DocumentProcessor
        from backend.core.compliance_engine import ComplianceEngine
        from backend.ai.llm_service import LLMService
        print("✅ Core components imported successfully")
        
        # Test LLM service
        llm = LLMService()
        print(f"✅ LLM Service initialized (Available: {llm.is_available()})")
        
        # Test database manager
        from backend.database.mongodb_manager import MongoDBManager
        print("✅ Database manager imported successfully")
        
        # Test middleware
        from backend.middleware.rate_limit import RateLimitMiddleware
        from backend.middleware.logging import LoggingMiddleware
        print("✅ Middleware components imported successfully")
        
        # Test authentication
        from backend.auth.auth_manager import AuthManager
        print("✅ Authentication manager imported successfully")
        
        print("\n🎉 All system components loaded successfully!")
        print("📋 System Summary:")
        print(f"   • Version: {settings.VERSION}")
        print(f"   • Database: MongoDB")
        print(f"   • AI Integration: {'Enabled' if llm.is_available() else 'Disabled'}")
        print(f"   • Available Models: {len(llm.available_models) if llm.is_available() else 0}")
        print("   • Components: Document Processing, Compliance Engine, AI Analysis")
        print("   • Security: JWT Auth, Rate Limiting, CORS")
        print("   • Monitoring: Health Checks, Metrics Collection")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing system: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)