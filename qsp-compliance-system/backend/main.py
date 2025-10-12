"""
Enterprise QSP Compliance System - Main Application
A robust, production-ready system for ISO 13485:2024 regulatory compliance analysis
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import os
import uuid
from contextlib import asynccontextmanager

# Import system components
from core.document_processor import DocumentProcessor
from core.compliance_engine import ComplianceEngine
from core.regulatory_analyzer import RegulatoryAnalyzer
from core.system_orchestrator import SystemOrchestrator
from database.mongodb_manager import MongoDBManager, get_db_session
from models import (
    SystemStatus, UploadResponse, AnalysisRequest, ComplianceReport,
    DocumentMetadata, ApiResponse
)
from config import settings
from middleware.rate_limit import RateLimitMiddleware
from middleware.logging import LoggingMiddleware
from middleware.metrics import MetricsMiddleware
from auth.auth_manager import AuthManager
from cache.cache_manager import CacheManager
from monitoring.health_checker import HealthChecker
from monitoring.metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/qsp_system.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize system components
database_manager = MongoDBManager()
cache_manager = CacheManager()
auth_manager = AuthManager()
health_checker = HealthChecker()
metrics_collector = MetricsCollector()

# Initialize core processors
document_processor = DocumentProcessor()
regulatory_analyzer = RegulatoryAnalyzer()
compliance_engine = ComplianceEngine()
system_orchestrator = SystemOrchestrator(
    document_processor=document_processor,
    regulatory_analyzer=regulatory_analyzer,
    compliance_engine=compliance_engine,
    cache_manager=cache_manager
)

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Enterprise QSP Compliance System")
    
    # Initialize database
    await database_manager.initialize()
    
    # Initialize cache
    await cache_manager.initialize()
    
    # Perform system health check
    await health_checker.startup_check()
    
    # Initialize metrics collection
    await metrics_collector.initialize()
    
    logger.info("System startup completed successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Enterprise QSP Compliance System")
    await cache_manager.cleanup()
    await database_manager.cleanup()
    logger.info("System shutdown completed")

# Create FastAPI application
app = FastAPI(
    title="Enterprise QSP Compliance System",
    description="Advanced regulatory compliance analysis for medical device QSPs against ISO 13485:2024",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and get current user"""
    return await auth_manager.verify_token(credentials.credentials)

# Health and monitoring endpoints
@app.get("/health", response_model=SystemStatus)
async def health_check():
    """System health check endpoint"""
    try:
        status = await health_checker.comprehensive_check()
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    return await metrics_collector.get_prometheus_metrics()

@app.get("/api/system/status", response_model=SystemStatus)
async def system_status(
    db_session=Depends(get_db_session)
):
    """Detailed system status"""
    try:
        status = await system_orchestrator.get_system_status(db_session)
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Document management endpoints
@app.post("/api/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "qsp",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db_session=Depends(get_db_session)
):
    """Upload and process QSP or regulatory documents"""
    try:
        # Read file data
        file_data = await file.read()
        
        if not file.filename or not file_data:
            raise HTTPException(status_code=400, detail="Invalid file data")
        
        # Process document
        document_id = await document_processor.process_upload(
            file_data=file_data,
            filename=file.filename,
            document_type=document_type,
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        
        # Schedule background processing
        background_tasks.add_task(
            system_orchestrator.process_document_async,
            document_id,
            db_session
        )
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            document_type=document_type,
            status="uploaded",
            message="Document uploaded successfully and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents", response_model=List[DocumentMetadata])
async def list_documents(
    document_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_session=Depends(get_db_session)
):
    """List documents with filtering and pagination"""
    try:
        documents = await document_processor.list_documents(
            user_id="demo_user",  # In production, use current_user.id
            session=db_session,
            document_type=document_type,
            limit=limit,
            offset=offset
        )
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    db_session=Depends(get_db_session)
):
    """Delete a document and its analysis results"""
    try:
        success = await document_processor.delete_document(
            document_id=document_id,
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analysis endpoints
@app.post("/api/analysis/run", response_model=ComplianceReport)
async def run_compliance_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db_session=Depends(get_db_session)
):
    """Run comprehensive compliance analysis"""
    try:
        # Validate request
        if not request.document_ids:
            raise HTTPException(status_code=400, detail="No documents specified")
        
        # Start analysis
        analysis_id = await system_orchestrator.start_compliance_analysis(
            document_ids=request.document_ids,
            regulatory_framework=request.regulatory_framework,
            analysis_type=request.analysis_type,
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        
        # Schedule background processing
        background_tasks.add_task(
            system_orchestrator.run_analysis_async,
            analysis_id,
            db_session
        )
        
        return ComplianceReport(
            analysis_id=analysis_id,
            request_id=analysis_id,
            user_id="demo_user",
            status="running",
            regulatory_framework=request.regulatory_framework,
            analysis_type=request.analysis_type,
            started_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"Analysis failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}", response_model=ComplianceReport)
async def get_analysis_results(
    analysis_id: str,
    db_session=Depends(get_db_session)
):
    """Get analysis results by ID"""
    try:
        report = await compliance_engine.get_analysis_report(
            analysis_id=analysis_id,
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        
        if not report:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analysis")
async def list_analyses(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db_session=Depends(get_db_session)
):
    """List user's compliance analyses"""
    try:
        analyses = await compliance_engine.list_analyses(
            user_id="demo_user",  # In production, use current_user.id
            status=status,
            limit=limit,
            offset=offset,
            session=db_session
        )
        return analyses
    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Regulatory change endpoints
@app.post("/api/regulatory/initialize")
async def initialize_regulatory_system(
    db_session=Depends(get_db_session)
):
    """Initialize regulatory change system"""
    try:
        result = await regulatory_analyzer.initialize_system(
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        return result
    except Exception as e:
        logger.error(f"Regulatory system initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/regulatory/process-summary")
async def process_regulatory_summary(
    framework: str,
    summary_version: str,
    background_tasks: BackgroundTasks,
    db_session=Depends(get_db_session)
):
    """Process new regulatory summary for changes"""
    try:
        task_id = await regulatory_analyzer.process_summary(
            framework=framework,
            summary_version=summary_version,
            user_id="demo_user",  # In production, use current_user.id
            session=db_session
        )
        
        # Schedule background processing
        background_tasks.add_task(
            regulatory_analyzer.process_summary_async,
            task_id,
            framework,
            summary_version,
            "demo_user",
            db_session
        )
        
        return {
            "task_id": task_id,
            "message": "Regulatory summary processing started",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Regulatory summary processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Enterprise QSP Compliance System",
        "version": "2.0.0",
        "description": "Advanced regulatory compliance analysis for medical device QSPs",
        "docs_url": "/api/docs",
        "health_url": "/health",
        "metrics_url": "/metrics",
        "features": [
            "Document Upload & Processing",
            "AI-Powered Compliance Analysis",
            "Regulatory Change Tracking",
            "Real-time Gap Identification",
            "Comprehensive Reporting",
            "Multi-user Support",
            "API Rate Limiting",
            "Comprehensive Monitoring"
        ],
        "supported_standards": ["ISO 13485:2024", "ISO 14971", "ISO 62304"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )