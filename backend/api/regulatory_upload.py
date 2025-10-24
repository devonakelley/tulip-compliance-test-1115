"""
Regulatory Document Upload and Diff API
Handles upload of old/new regulatory PDFs and diff processing
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import logging
import os
from pathlib import Path
import shutil
from datetime import datetime
from core.iso_diff_processor import get_iso_diff_processor
from core.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/regulatory", tags=["regulatory_docs"])

# Database will be injected
db: AsyncIOMotorDatabase = None

def set_database(database):
    global db
    db = database

# Storage paths
UPLOAD_DIR = Path("/app/backend/data")
INTERNAL_DOCS_DIR = UPLOAD_DIR / "internal_docs"
REGULATORY_DOCS_DIR = UPLOAD_DIR / "regulatory_docs"
DELTAS_DIR = UPLOAD_DIR / "deltas"

# Ensure directories exist
for directory in [INTERNAL_DOCS_DIR, REGULATORY_DOCS_DIR, DELTAS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


@router.post("/upload/internal")
async def upload_internal_document(
    file: UploadFile = File(...),
    version: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload internal compliance document (QSP, SOP, form)
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Create tenant directory
        tenant_dir = INTERNAL_DOCS_DIR / tenant_id
        tenant_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = tenant_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded internal document: {file.filename}")
        
        # TODO: Store metadata in MongoDB
        # await db.uploaded_internal_docs.insert_one({
        #     'tenant_id': tenant_id,
        #     'filename': file.filename,
        #     'version': version,
        #     'file_path': str(file_path),
        #     'uploaded_at': datetime.utcnow(),
        #     'uploaded_by': current_user['user_id']
        # })
        
        return {
            'success': True,
            'filename': file.filename,
            'size': file_path.stat().st_size,
            'message': 'Internal document uploaded successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to upload internal document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/regulatory")
async def upload_regulatory_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # 'old' or 'new'
    standard_name: Optional[str] = Form("ISO 13485"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload regulatory standard PDF (old or new version)
    
    Args:
        file: PDF file
        doc_type: 'old' or 'new'
        standard_name: Name of the standard (e.g., 'ISO 13485')
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        if doc_type not in ['old', 'new']:
            raise HTTPException(status_code=400, detail="doc_type must be 'old' or 'new'")
        
        # Validate PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create tenant directory
        tenant_dir = REGULATORY_DOCS_DIR / tenant_id
        tenant_dir.mkdir(exist_ok=True)
        
        # Save with standardized name
        safe_name = f"{doc_type}_{file.filename}"
        file_path = tenant_dir / safe_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded {doc_type} regulatory document: {file.filename}")
        
        # TODO: Store metadata in MongoDB
        # await db.uploaded_regulatory_docs.insert_one({
        #     'tenant_id': tenant_id,
        #     'filename': file.filename,
        #     'doc_type': doc_type,
        #     'standard_name': standard_name,
        #     'file_path': str(file_path),
        #     'uploaded_at': datetime.utcnow(),
        #     'uploaded_by': current_user['user_id']
        # })
        
        return {
            'success': True,
            'filename': file.filename,
            'doc_type': doc_type,
            'size': file_path.stat().st_size,
            'file_path': str(file_path),
            'message': f'{doc_type.capitalize()} regulatory document uploaded successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload regulatory document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preprocess/iso_diff")
async def process_iso_diff(
    old_file_path: str = Form(...),
    new_file_path: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Process diff between old and new regulatory PDFs
    Generates deltas JSON file and stores in MongoDB
    
    Args:
        old_file_path: Path to old version PDF
        new_file_path: Path to new version PDF
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Validate files exist
        if not os.path.exists(old_file_path):
            raise HTTPException(status_code=404, detail=f"Old file not found: {old_file_path}")
        
        if not os.path.exists(new_file_path):
            raise HTTPException(status_code=404, detail=f"New file not found: {new_file_path}")
        
        logger.info(f"Processing ISO diff for tenant {tenant_id}")
        logger.info(f"  Old: {old_file_path}")
        logger.info(f"  New: {new_file_path}")
        
        # Process diff
        processor = get_iso_diff_processor()
        
        # Generate output path
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_filename = f"deltas_{tenant_id}_{timestamp}.json"
        output_path = DELTAS_DIR / output_filename
        
        # Run diff processing
        deltas = processor.process_documents(
            old_pdf_path=old_file_path,
            new_pdf_path=new_file_path,
            output_path=str(output_path)
        )
        
        # Generate summary
        added = sum(1 for d in deltas if d['change_type'] == 'added')
        modified = sum(1 for d in deltas if d['change_type'] == 'modified')
        deleted = sum(1 for d in deltas if d['change_type'] == 'deleted')
        
        # Store in MongoDB for Gap Analysis reference
        import uuid
        diff_result_id = str(uuid.uuid4())
        
        diff_document = {
            'diff_id': diff_result_id,
            'tenant_id': tenant_id,
            'old_file_path': old_file_path,
            'new_file_path': new_file_path,
            'deltas': deltas,
            'total_changes': len(deltas),
            'summary': {
                'added': added,
                'modified': modified,
                'deleted': deleted
            },
            'created_at': datetime.utcnow(),
            'created_by': user_id
        }
        
        await db.diff_results.insert_one(diff_document)
        
        logger.info(f"✅ Diff processing complete: {len(deltas)} changes detected, stored in MongoDB")
        
        return {
            'success': True,
            'diff_id': diff_result_id,
            'deltas_file': str(output_path),
            'total_changes': len(deltas),
            'summary': {
                'added': added,
                'modified': modified,
                'deleted': deleted
            },
            'deltas': deltas[:10],  # Return first 10 for preview
            'message': f'Found {len(deltas)} changes between old and new versions'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process ISO diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/internal")
async def list_internal_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List uploaded internal documents for current tenant
    """
    try:
        tenant_id = current_user["tenant_id"]
        tenant_dir = INTERNAL_DOCS_DIR / tenant_id
        
        if not tenant_dir.exists():
            return {'success': True, 'documents': []}
        
        documents = []
        for file_path in tenant_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'uploaded_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'file_path': str(file_path)
                })
        
        return {
            'success': True,
            'count': len(documents),
            'documents': documents
        }
        
    except Exception as e:
        logger.error(f"Failed to list internal documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/regulatory")
async def list_regulatory_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List uploaded regulatory documents for current tenant
    """
    try:
        tenant_id = current_user["tenant_id"]
        tenant_dir = REGULATORY_DOCS_DIR / tenant_id
        
        if not tenant_dir.exists():
            return {'success': True, 'documents': {'old': None, 'new': None}}
        
        documents = {'old': None, 'new': None}
        
        for file_path in tenant_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.pdf':
                stat = file_path.stat()
                doc_info = {
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'uploaded_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'file_path': str(file_path)
                }
                
                if file_path.name.startswith('old_'):
                    documents['old'] = doc_info
                elif file_path.name.startswith('new_'):
                    documents['new'] = doc_info
        
        return {
            'success': True,
            'documents': documents
        }
        
    except Exception as e:
        logger.error(f"Failed to list regulatory documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== QSP Document Upload and Parsing =====

QSP_DOCS_DIR = UPLOAD_DIR / "qsp_docs"
QSP_DOCS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/qsp")
async def upload_qsp_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and parse QSP document (DOCX, PDF, or TXT)
    Returns structured clause-level data
    
    Response:
    {
        "success": true,
        "document_number": "7.3-3",
        "revision": "R9",
        "filename": "QSP 7.3-3 R9 Risk Management.docx",
        "total_clauses": 12,
        "clauses": [
            {
                "document_number": "7.3-3",
                "clause_number": "7.3.5",
                "title": "Risk Analysis",
                "text": "The risk analysis can be recorded...",
                "characters": 312
            }
        ]
    }
    """
    try:
        from core.qsp_parser import get_qsp_parser
        
        tenant_id = current_user["tenant_id"]
        
        # Validate file type
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['docx', 'pdf', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail="Only DOCX, PDF, and TXT files are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Parse document
        parser = get_qsp_parser()
        parsed_data = parser.parse_file(file_content, file.filename)
        
        # Save file to disk
        tenant_dir = QSP_DOCS_DIR / tenant_id
        tenant_dir.mkdir(exist_ok=True)
        
        file_path = tenant_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Store parsed data in MongoDB
        # TODO: Implement MongoDB storage
        # await db.qsp_documents.insert_one({
        #     'tenant_id': tenant_id,
        #     'document_number': parsed_data['document_number'],
        #     'revision': parsed_data['revision'],
        #     'filename': file.filename,
        #     'file_path': str(file_path),
        #     'total_clauses': parsed_data['total_clauses'],
        #     'clauses': parsed_data['clauses'],
        #     'uploaded_at': datetime.utcnow(),
        #     'uploaded_by': current_user['user_id']
        # })
        
        logger.info(f"✅ Uploaded and parsed QSP: {file.filename} - {parsed_data['total_clauses']} clauses")
        
        return {
            'success': True,
            'file_path': str(file_path),
            **parsed_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload/parse QSP document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/qsp")
async def list_qsp_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List all uploaded QSP documents with parsed clause data
    
    Response:
    {
        "success": true,
        "count": 3,
        "documents": [
            {
                "document_number": "7.3-3",
                "revision": "R9",
                "filename": "QSP 7.3-3 R9 Risk Management.docx",
                "total_clauses": 12,
                "clauses": [...]
            }
        ]
    }
    """
    try:
        from core.qsp_parser import get_qsp_parser
        
        tenant_id = current_user["tenant_id"]
        tenant_dir = QSP_DOCS_DIR / tenant_id
        
        if not tenant_dir.exists():
            return {'success': True, 'count': 0, 'documents': []}
        
        documents = []
        parser = get_qsp_parser()
        
        for file_path in tenant_dir.iterdir():
            if file_path.is_file():
                try:
                    # Re-parse document to get structured data
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    parsed_data = parser.parse_file(file_content, file_path.name)
                    
                    # Add file metadata
                    stat = file_path.stat()
                    parsed_data['file_path'] = str(file_path)
                    parsed_data['size'] = stat.st_size
                    parsed_data['uploaded_at'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    documents.append(parsed_data)
                    
                except Exception as e:
                    logger.error(f"Failed to parse {file_path.name}: {e}")
                    continue
        
        # Sort by document number
        documents.sort(key=lambda x: x['document_number'])
        
        logger.info(f"Listed {len(documents)} QSP documents for tenant {tenant_id}")
        
        return {
            'success': True,
            'count': len(documents),
            'documents': documents
        }
        
    except Exception as e:
        logger.error(f"Failed to list QSP documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/map_clauses")
async def map_clauses(
    current_user: dict = Depends(get_current_user)
):
    """
    Generate clause mappings between regulatory deltas and QSP documents
    This endpoint processes all uploaded QSP documents and prepares them for gap analysis
    
    Response:
    {
        "success": true,
        "total_qsp_documents": 3,
        "total_clauses_mapped": 45,
        "message": "Clause mapping complete"
    }
    """
    try:
        from core.qsp_parser import get_qsp_parser
        from core.change_impact_service_mongo import get_change_impact_service
        
        tenant_id = current_user["tenant_id"]
        tenant_dir = QSP_DOCS_DIR / tenant_id
        
        if not tenant_dir.exists() or not any(tenant_dir.iterdir()):
            raise HTTPException(
                status_code=400,
                detail="No QSP documents found. Please upload QSP documents first."
            )
        
        # Clear existing QSP sections for this tenant to avoid duplicates
        # This ensures idempotency - can run clause mapping multiple times
        if db is not None:
            result = await db.qsp_sections.delete_many({"tenant_id": tenant_id})
            logger.info(f"Cleared {result.deleted_count} existing QSP sections for tenant {tenant_id}")
        
        parser = get_qsp_parser()
        impact_service = get_change_impact_service()
        
        total_documents = 0
        total_clauses = 0
        
        # Process each QSP document
        for file_path in tenant_dir.iterdir():
            if file_path.is_file():
                try:
                    # Parse document
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    parsed_data = parser.parse_file(file_content, file_path.name)
                    
                    # Ingest into change impact service for semantic matching
                    import uuid
                    doc_id = str(uuid.uuid4())
                    
                    # Convert clauses to sections format expected by impact service
                    sections = [
                        {
                            'section_path': clause['clause_number'],
                            'heading': clause['title'],
                            'text': clause['text'],
                            'version': parsed_data['revision']
                        }
                        for clause in parsed_data['clauses']
                    ]
                    
                    result = impact_service.ingest_qsp_document(
                        tenant_id=tenant_id,
                        doc_id=doc_id,
                        doc_name=f"{parsed_data['document_number']} {parsed_data['filename']}",
                        sections=sections
                    )
                    
                    # Handle MongoDB persistence if there are pending operations
                    if hasattr(impact_service, '_pending_mongo_operations'):
                        pending = impact_service._pending_mongo_operations
                        
                        # Clear existing sections for this doc first (idempotency)
                        await db.qsp_sections.delete_many({
                            'tenant_id': pending['tenant_id'],
                            'doc_id': pending['doc_id']
                        })
                        
                        # Insert new sections
                        if pending['sections']:
                            await db.qsp_sections.insert_many(pending['sections'])
                        
                        logger.info(f"✅ Persisted {pending['count']} sections to MongoDB for {file_path.name}")
                        
                        # Clear pending operations
                        delattr(impact_service, '_pending_mongo_operations')
                    
                    total_documents += 1
                    total_clauses += result['sections_embedded']
                    
                    logger.info(f"Mapped {result['sections_embedded']} clauses from {file_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to map clauses from {file_path.name}: {e}")
                    continue
        
        if total_documents == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to map any QSP documents. Please check document format."
            )
        
        logger.info(f"✅ Clause mapping complete: {total_documents} docs, {total_clauses} clauses")
        
        return {
            'success': True,
            'total_qsp_documents': total_documents,
            'total_clauses_mapped': total_clauses,
            'message': f'Successfully mapped {total_clauses} clauses from {total_documents} QSP documents'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to map clauses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/qsp/{filename}")
async def delete_qsp_document(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific QSP document by filename"""
    try:
        tenant_id = current_user["tenant_id"]
        tenant_dir = QSP_DOCS_DIR / tenant_id
        
        if not tenant_dir.exists():
            raise HTTPException(status_code=404, detail="No QSP documents found")
        
        # Find and delete the file
        deleted = False
        for file_path in tenant_dir.glob("*"):
            if file_path.name == filename or filename in file_path.name:
                file_path.unlink()
                deleted = True
                logger.info(f"Deleted QSP document: {file_path.name}")
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
        
        # Clear MongoDB qsp_sections for this tenant to force re-mapping
        if db is not None:
            await db.qsp_sections.delete_many({"tenant_id": tenant_id})
            logger.info(f"Cleared QSP sections for tenant {tenant_id}")
        
        return {
            'success': True,
            'message': f'Successfully deleted {filename}'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete QSP document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/qsp/all")
async def delete_all_qsp_documents(
    current_user: dict = Depends(get_current_user)
):
    """Delete ALL QSP documents for current tenant"""
    try:
        tenant_id = current_user["tenant_id"]
        tenant_dir = QSP_DOCS_DIR / tenant_id
        
        deleted_count = 0
        
        if tenant_dir.exists():
            # Delete all files in the QSP directory
            for file_path in tenant_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted QSP document: {file_path.name}")
        
        # Clear MongoDB qsp_sections for this tenant
        if db is not None:
            result = await db.qsp_sections.delete_many({"tenant_id": tenant_id})
            logger.info(f"Cleared {result.deleted_count} QSP sections for tenant {tenant_id}")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} QSP document(s)'
        }
        
    except Exception as e:
        logger.error(f"Failed to delete all QSP documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

