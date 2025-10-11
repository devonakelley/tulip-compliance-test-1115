"""
Test version of Enterprise QSP Compliance System
Simplified for testing basic functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime
from typing import Dict, Any
import os

# Import core components
from .database import DatabaseManager, get_db_session
from .config import settings
from .ai import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize core components
database_manager = DatabaseManager()
llm_service = LLMService()

# Create FastAPI application
app = FastAPI(
    title="Enterprise QSP Compliance System (Test)",
    description="Test version of the regulatory compliance analysis system",
    version="2.0.0-test",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting Enterprise QSP Compliance System (Test)")
    
    try:
        # Initialize database
        await database_manager.initialize()
        logger.info("Database initialized successfully")
        
        # Test LLM service
        if llm_service.is_available():
            logger.info("LLM service available")
        else:
            logger.warning("LLM service not available")
        
        logger.info("System startup completed successfully")
        
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Enterprise QSP Compliance System")
    await database_manager.cleanup()
    logger.info("System shutdown completed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Check database
        db_health = await database_manager.health_check()
        
        return {
            "status": "healthy" if db_health.get("status") == "healthy" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0-test",
            "components": {
                "database": db_health,
                "llm_service": {
                    "available": llm_service.is_available(),
                    "models": llm_service.available_models if llm_service.is_available() else []
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Enterprise QSP Compliance System (Test)",
        "version": "2.0.0-test",
        "description": "Test version of advanced regulatory compliance analysis system",
        "docs_url": "/api/docs",
        "health_url": "/health",
        "features": [
            "Document Upload & Processing",
            "AI-Powered Compliance Analysis",
            "Regulatory Change Tracking",
            "MongoDB Integration",
            "Multi-model AI Support"
        ],
        "supported_standards": ["ISO 13485:2024"],
        "timestamp": datetime.utcnow().isoformat()
    }

# Test endpoint for AI service
@app.get("/api/test/ai")
async def test_ai():
    """Test AI service functionality"""
    try:
        if not llm_service.is_available():
            return {"error": "LLM service not available"}
        
        # Simple test prompt
        response = await llm_service.generate(
            prompt="What is ISO 13485?",
            max_tokens=100,
            temperature=0.1
        )
        
        return {
            "status": "success",
            "response": response,
            "model_used": "emergent_llm",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI test failed: {e}")
        return {"status": "error", "error": str(e)}

# Test endpoint for database
@app.get("/api/test/database")
async def test_database():
    """Test database functionality"""
    try:
        async with database_manager.get_session() as db:
            # Test write
            test_doc = {
                "_id": "test_doc_123",
                "name": "Test Document",
                "created_at": datetime.utcnow(),
                "test": True
            }
            
            await db.test_documents.insert_one(test_doc)
            
            # Test read
            retrieved = await db.test_documents.find_one({"_id": "test_doc_123"})
            
            # Cleanup
            await db.test_documents.delete_one({"_id": "test_doc_123"})
            
            return {
                "status": "success",
                "write_test": "passed",
                "read_test": "passed" if retrieved else "failed",
                "cleanup": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {"status": "error", "error": str(e)}

# Simple document upload test
@app.post("/api/test/upload")
async def test_upload(filename: str, content: str):
    """Test document upload functionality"""
    try:
        async with database_manager.get_session() as db:
            document = {
                "_id": f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "filename": filename,
                "content": content,
                "document_type": "qsp",
                "uploaded_at": datetime.utcnow(),
                "status": "uploaded",
                "test_upload": True
            }
            
            result = await db.documents.insert_one(document)
            
            return {
                "status": "success",
                "document_id": document["_id"],
                "message": "Document uploaded successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Upload test failed: {e}")
        return {"status": "error", "error": str(e)}

# List test documents
@app.get("/api/test/documents")
async def list_test_documents():
    """List test documents"""
    try:
        async with database_manager.get_session() as db:
            cursor = db.documents.find({"test_upload": True}).sort("uploaded_at", -1).limit(10)
            documents = await cursor.to_list(length=None)
            
            return {
                "status": "success",
                "documents": [
                    {
                        "id": doc["_id"],
                        "filename": doc.get("filename"),
                        "uploaded_at": doc.get("uploaded_at"),
                        "status": doc.get("status")
                    }
                    for doc in documents
                ],
                "count": len(documents),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"List documents test failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "test_main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )