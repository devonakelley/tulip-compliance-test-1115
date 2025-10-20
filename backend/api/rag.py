"""
RAG API for Regulatory Document Management
Handles upload and processing of ISO, FDA, and other regulatory documents
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.auth import get_current_user
from core.rag_service import rag_service
from core.audit_logger import audit_logger
from models.regulatory import RegulatoryFramework
import io
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Database will be injected
db: AsyncIOMotorDatabase = None

def set_database(database):
    global db
    db = database

async def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from uploaded file"""
    file_ext = filename.lower().split('.')[-1]
    
    try:
        if file_ext == 'docx':
            doc = DocxDocument(io.BytesIO(file_content))
            return '\n'.join([para.text for para in doc.paragraphs])
        elif file_ext == 'pdf':
            # Extract text from PDF using PyPDF2
            import PyPDF2
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            return text_content
        elif file_ext == 'txt':
            return file_content.decode('utf-8', errors='ignore')
        else:
            # Try UTF-8 decode as fallback
            return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Text extraction failed for {filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Could not extract text from {filename}: {str(e)}")

@router.post("/upload-regulatory-doc")
async def upload_regulatory_document(
    file: UploadFile = File(...),
    framework: str = Form(...),
    doc_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a regulatory document (ISO, FDA, MDR, etc.)
    Will be chunked and added to RAG system for compliance checking
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Validate framework
        try:
            fw = RegulatoryFramework(framework)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")
        
        # Read file
        content = await file.read()
        
        # Extract text
        text_content = await extract_text_from_file(content, file.filename)
        
        if len(text_content) < 100:
            raise HTTPException(status_code=400, detail="Document too short or could not extract text")
        
        # Generate doc_id
        import uuid
        doc_id = f"reg_{framework}_{str(uuid.uuid4())[:8]}"
        
        # Add to RAG system
        result = rag_service.add_regulatory_document(
            tenant_id=tenant_id,
            doc_id=doc_id,
            doc_name=doc_name or file.filename,
            content=text_content,
            framework=framework,
            metadata={
                'uploaded_by': user_id,
                'filename': file.filename
            }
        )
        
        # Store metadata in MongoDB
        reg_doc_meta = {
            'doc_id': doc_id,
            'tenant_id': tenant_id,
            'doc_name': doc_name or file.filename,
            'framework': framework,
            'filename': file.filename,
            'uploaded_by': user_id,
            'chunks_count': result['chunks_added'],
            'file_size': len(content),
            'char_count': len(text_content)
        }
        await db.regulatory_documents.insert_one(reg_doc_meta)
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="upload_regulatory_doc",
            target=file.filename,
            metadata={
                'framework': framework,
                'chunks': result['chunks_added'],
                'doc_id': doc_id
            }
        )
        
        logger.info(f"Uploaded regulatory doc: {file.filename} ({result['chunks_added']} chunks)")
        
        return {
            'success': True,
            'doc_id': doc_id,
            'doc_name': doc_name or file.filename,
            'framework': framework,
            'chunks_added': result['chunks_added'],
            'total_chars': result['total_chars']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regulatory document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-compliance")
async def check_compliance(
    qsp_doc_id: str = Form(...),
    framework: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Check QSP compliance against uploaded regulatory documents
    Uses RAG to find semantic matches
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Get QSP document
        qsp_doc = await db.qsp_documents.find_one({
            'id': qsp_doc_id,
            'tenant_id': tenant_id
        })
        
        if not qsp_doc:
            raise HTTPException(status_code=404, detail="QSP document not found")
        
        # Get content
        content = qsp_doc.get('content', '')
        
        if not content:
            raise HTTPException(status_code=400, detail="QSP document has no content")
        
        # Run compliance check
        result = rag_service.compare_documents(
            tenant_id=tenant_id,
            qsp_content=content,
            framework=framework or 'ISO_13485',
            threshold=0.6
        )
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            action="check_compliance_rag",
            target=qsp_doc_id,
            metadata={
                'framework': framework,
                'matches': result['matches_found'],
                'coverage': result['coverage_percentage']
            }
        )
        
        return {
            'success': True,
            'qsp_doc_id': qsp_doc_id,
            'qsp_filename': qsp_doc.get('filename'),
            'analysis': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulatory-docs")
async def list_regulatory_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List all uploaded regulatory documents for tenant
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Get from RAG service
        docs = rag_service.list_regulatory_documents(tenant_id)
        
        return {
            'success': True,
            'count': len(docs),
            'documents': docs
        }
        
    except Exception as e:
        logger.error(f"Failed to list regulatory docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/regulatory-docs/{doc_id}")
async def delete_regulatory_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a regulatory document
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Delete from RAG
        success = rag_service.delete_document(tenant_id, doc_id)
        
        # Delete metadata from MongoDB
        await db.regulatory_documents.delete_one({
            'doc_id': doc_id,
            'tenant_id': tenant_id
        })
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete_regulatory_doc",
            target=doc_id
        )
        
        return {
            'success': success,
            'doc_id': doc_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete regulatory doc: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regulatory-docs/batch-delete")
async def batch_delete_regulatory_documents(
    doc_ids: list = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete multiple regulatory documents in batch
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        if not doc_ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")
        
        deleted_count = 0
        failed_ids = []
        
        for doc_id in doc_ids:
            try:
                # Delete from RAG
                success = rag_service.delete_document(tenant_id, doc_id)
                
                if success:
                    # Delete metadata from MongoDB
                    await db.regulatory_documents.delete_one({
                        'doc_id': doc_id,
                        'tenant_id': tenant_id
                    })
                    deleted_count += 1
                else:
                    failed_ids.append(doc_id)
                    
            except Exception as e:
                logger.error(f"Failed to delete regulatory doc {doc_id}: {e}")
                failed_ids.append(doc_id)
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="batch_delete_regulatory_docs",
            target=f"{deleted_count}_documents",
            metadata={
                'requested_count': len(doc_ids),
                'deleted_count': deleted_count,
                'failed_ids': failed_ids
            }
        )
        
        logger.info(f"Batch deleted {deleted_count}/{len(doc_ids)} regulatory documents")
        
        return {
            'success': True,
            'message': f'Deleted {deleted_count} of {len(doc_ids)} documents',
            'deleted_count': deleted_count,
            'failed_count': len(failed_ids),
            'failed_ids': failed_ids
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch delete regulatory docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/regulatory-docs/all")
async def delete_all_regulatory_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    Delete ALL regulatory documents for current tenant - Use with caution!
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Get all regulatory documents for this tenant
        docs = rag_service.list_regulatory_documents(tenant_id)
        
        if not docs:
            return {
                'success': True,
                'message': 'No documents to delete',
                'deleted_count': 0
            }
        
        deleted_count = 0
        for doc in docs:
            try:
                rag_service.delete_document(tenant_id, doc['doc_id'])
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete doc {doc['doc_id']}: {e}")
        
        # Delete all metadata from MongoDB
        result = await db.regulatory_documents.delete_many({'tenant_id': tenant_id})
        
        # Log audit
        await audit_logger.log_action(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete_all_regulatory_docs",
            target=f"all_{deleted_count}_documents",
            metadata={
                'deleted_count': deleted_count
            }
        )
        
        logger.warning(f"Deleted ALL {deleted_count} regulatory documents for tenant {tenant_id}")
        
        return {
            'success': True,
            'message': f'Deleted all {deleted_count} documents',
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to delete all regulatory docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_requirements(
    query: str = Form(...),
    framework: Optional[str] = Form(None),
    n_results: int = Form(5),
    current_user: dict = Depends(get_current_user)
):
    """
    Search regulatory requirements semantically
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        results = rag_service.search_regulatory_requirements(
            tenant_id=tenant_id,
            query_text=query,
            framework=framework,
            n_results=n_results
        )
        
        return {
            'success': True,
            'query': query,
            'results_count': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reprocess-document/{doc_id}")
async def reprocess_regulatory_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Reprocess a regulatory document with improved chunking strategy
    This will delete old chunks and recreate with better accuracy
    """
    try:
        tenant_id = current_user["tenant_id"]
        user_id = current_user["user_id"]
        
        # Get document metadata from MongoDB
        reg_doc = await db.regulatory_documents.find_one({
            'doc_id': doc_id,
            'tenant_id': tenant_id
        })
        
        if not reg_doc:
            raise HTTPException(status_code=404, detail="Regulatory document not found")
        
        # We need the original file content to reprocess
        # For now, return error if we don't have it stored
        # In production, you'd retrieve from storage
        raise HTTPException(
            status_code=400, 
            detail="Document reprocessing requires the original file. Please re-upload the document to use improved chunking."
        )
        
        # TODO: Implement file retrieval from storage and reprocessing
        # filename = reg_doc.get('filename')
        # file_path = storage_service.get_file_path(tenant_id, filename)
        # content = extract_text_from_file(file_path)
        # result = rag_service.reprocess_document(...)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunking-quality")
async def get_chunking_quality_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get metrics about chunking quality for all regulatory documents
    Shows chunk counts, average sizes, and distribution
    """
    try:
        tenant_id = current_user["tenant_id"]
        
        # Get all regulatory documents
        docs = rag_service.list_regulatory_documents(tenant_id)
        
        if not docs:
            return {
                'success': True,
                'total_documents': 0,
                'metrics': {}
            }
        
        # Calculate metrics
        total_chunks = sum(doc['chunk_count'] for doc in docs)
        avg_chunks_per_doc = total_chunks // len(docs) if docs else 0
        
        # Get detailed chunk size distribution
        from core.rag_service import rag_service as rag
        collection_name = f"regulatory_{tenant_id}".replace("-", "_")
        try:
            collection = rag.chroma_client.get_collection(collection_name)
            results = collection.get()
            
            chunk_lengths = [len(doc) for doc in results['documents']]
            avg_chunk_length = sum(chunk_lengths) // len(chunk_lengths) if chunk_lengths else 0
            min_chunk_length = min(chunk_lengths) if chunk_lengths else 0
            max_chunk_length = max(chunk_lengths) if chunk_lengths else 0
            
            # Analyze section headers
            section_headers = [meta.get('section_header', '') for meta in results['metadatas']]
            unique_sections = len(set(h for h in section_headers if h))
            
            metrics = {
                'total_documents': len(docs),
                'total_chunks': total_chunks,
                'avg_chunks_per_doc': avg_chunks_per_doc,
                'avg_chunk_length': avg_chunk_length,
                'min_chunk_length': min_chunk_length,
                'max_chunk_length': max_chunk_length,
                'unique_sections': unique_sections,
                'documents': docs
            }
            
        except Exception as e:
            logger.warning(f"Could not get detailed metrics: {e}")
            metrics = {
                'total_documents': len(docs),
                'total_chunks': total_chunks,
                'avg_chunks_per_doc': avg_chunks_per_doc,
                'documents': docs
            }
        
        return {
            'success': True,
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get chunking metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

