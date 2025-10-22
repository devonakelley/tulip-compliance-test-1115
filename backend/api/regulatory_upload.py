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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/regulatory", tags=["regulatory_docs"])

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
    Generates deltas JSON file
    
    Args:
        old_file_path: Path to old version PDF
        new_file_path: Path to new version PDF
    """
    try:
        tenant_id = current_user["tenant_id"]
        
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
        
        logger.info(f"✅ Diff processing complete: {len(deltas)} changes detected")
        
        return {
            'success': True,
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
