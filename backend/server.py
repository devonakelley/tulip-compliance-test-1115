from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import io
import re
from docx import Document
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="QSP Compliance Checker", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class QSPDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content: str
    sections: Dict[str, str] = Field(default_factory=dict)
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False

class ISOSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework: str = "ISO_13485"
    version: str = "2024_summary"
    content: str
    new_clauses: List[Dict[str, str]] = Field(default_factory=list)
    modified_clauses: List[Dict[str, str]] = Field(default_factory=list)
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClauseMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qsp_id: str
    qsp_filename: str
    section_title: str
    section_content: str
    iso_clause: str
    confidence_score: float
    evidence_text: str
    mapping_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComplianceGap(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qsp_id: str
    qsp_filename: str
    iso_clause: str
    gap_type: str  # "missing", "partial", "outdated"
    description: str
    severity: str  # "high", "medium", "low"
    recommendations: List[str] = Field(default_factory=list)

class ComplianceAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    overall_score: float
    total_documents: int
    compliant_documents: int
    gaps: List[ComplianceGap]
    affected_documents: List[str]
    analysis_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper Functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    """Convert ISO string timestamps back to datetime objects"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key.endswith('_date') and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
            elif isinstance(value, dict):
                item[key] = parse_from_mongo(value)
            elif isinstance(value, list):
                item[key] = [parse_from_mongo(sub_item) if isinstance(sub_item, dict) else sub_item for sub_item in value]
    return item

async def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file_content))
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text)
        return '\n'.join(full_text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract text from DOCX file")

async def parse_document_sections(content: str, filename: str) -> Dict[str, str]:
    """Parse document content into logical sections"""
    sections = {}
    
    # Split by common section patterns
    patterns = [
        r'\b\d+\.\s+[A-Z][^.]*\n',  # Numbered sections
        r'\b[A-Z][^.]{10,50}:?\n',   # Header patterns
        r'^[A-Z\s]{3,}\n',           # All caps headers
    ]
    
    current_section = "Introduction"
    current_content = []
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a section header
        is_header = False
        for pattern in patterns:
            if re.match(pattern, line + '\n'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.replace(':', '').strip()
                current_content = []
                is_header = True
                break
        
        if not is_header:
            current_content.append(line)
    
    # Save final section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # If no sections found, treat entire document as one section
    if not sections:
        sections[f"{filename} - Full Content"] = content
    
    return sections

async def analyze_clause_mapping(qsp_content: str, qsp_filename: str, iso_clauses: List[str]) -> List[Dict[str, Any]]:
    """Use AI to map QSP content to ISO clauses"""
    try:
        # Initialize LLM chat
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"mapping_{uuid.uuid4()}",
            system_message="""You are an expert in ISO 13485 compliance for medical devices. 
            Analyze QSP document sections and map them to relevant ISO 13485:2024 clauses.
            
            For each mapping, provide:
            1. The ISO clause number and title
            2. Confidence score (0.0-1.0) based on relevance
            3. Evidence text from the QSP that supports the mapping
            4. Brief explanation of the mapping
            
            Return results as a JSON array with this structure:
            [
                {
                    "iso_clause": "4.1 General requirements",
                    "confidence_score": 0.85,
                    "evidence_text": "relevant excerpt from QSP",
                    "explanation": "brief explanation of why this maps"
                }
            ]"""
        ).with_model("openai", "gpt-4o")
        
        iso_clauses_text = "\n".join([f"- {clause}" for clause in iso_clauses])
        
        user_message = UserMessage(
            text=f"""Analyze this QSP document content and map it to relevant ISO 13485:2024 clauses:

QSP Document: {qsp_filename}
Content:
{qsp_content[:3000]}...

ISO 13485:2024 Key Clauses to consider:
{iso_clauses_text}

Provide detailed mappings with confidence scores."""
        )
        
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        try:
            # Clean the response - remove markdown formatting if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            mappings = json.loads(clean_response)
            return mappings if isinstance(mappings, list) else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {response}")
            return []
            
    except Exception as e:
        logger.error(f"Error in AI clause mapping: {e}")
        return []

# API Routes
@api_router.get("/")
async def root():
    return {"message": "QSP Compliance Checker API", "version": "1.0.0"}

@api_router.post("/documents/upload")
async def upload_qsp_document(file: UploadFile = File(...)):
    """Upload a QSP document (.docx or .txt)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file type
        allowed_extensions = ['.docx', '.txt']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text
        if file_ext == '.docx':
            text_content = await extract_text_from_docx(content)
        else:  # .txt
            text_content = content.decode('utf-8')
        
        # Parse into sections
        sections = await parse_document_sections(text_content, file.filename)
        
        # Create QSP document
        qsp_doc = QSPDocument(
            filename=file.filename,
            content=text_content,
            sections=sections,
            processed=True
        )
        
        # Store in MongoDB
        doc_dict = prepare_for_mongo(qsp_doc.model_dump())
        result = await db.qsp_documents.insert_one(doc_dict)
        
        logger.info(f"Uploaded QSP document: {file.filename}")
        
        return {
            "message": "Document uploaded successfully",
            "document_id": qsp_doc.id,
            "filename": file.filename,
            "sections_count": len(sections),
            "content_length": len(text_content)
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/iso-summary/upload")
async def upload_iso_summary(file: UploadFile = File(...)):
    """Upload ISO 13485:2024 Summary of Changes"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext == '.docx':
            text_content = await extract_text_from_docx(content)
        else:
            text_content = content.decode('utf-8')
        
        # Parse ISO summary content
        new_clauses = []
        modified_clauses = []
        
        # Simple parsing for new and modified clauses
        lines = text_content.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if 'NEW CLAUSES' in line.upper() or 'NEW REQUIREMENTS' in line.upper():
                current_section = "new"
            elif 'MODIFIED CLAUSES' in line.upper() or 'CHANGED CLAUSES' in line.upper():
                current_section = "modified"
            elif line and current_section and re.match(r'\d+\.\d+', line):
                clause_info = {"clause": line, "description": line}
                if current_section == "new":
                    new_clauses.append(clause_info)
                elif current_section == "modified":
                    modified_clauses.append(clause_info)
        
        # Create ISO summary
        iso_summary = ISOSummary(
            content=text_content,
            new_clauses=new_clauses,
            modified_clauses=modified_clauses
        )
        
        # Store in MongoDB
        summary_dict = prepare_for_mongo(iso_summary.model_dump())
        await db.iso_summaries.insert_one(summary_dict)
        
        logger.info(f"Uploaded ISO summary: {file.filename}")
        
        return {
            "message": "ISO summary uploaded successfully",
            "summary_id": iso_summary.id,
            "new_clauses_count": len(new_clauses),
            "modified_clauses_count": len(modified_clauses)
        }
        
    except Exception as e:
        logger.error(f"Error uploading ISO summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analysis/run-mapping")
async def run_clause_mapping():
    """Run AI-powered clause mapping for all QSP documents"""
    try:
        # Get all QSP documents
        qsp_docs = await db.qsp_documents.find({}, {"_id": 0}).to_list(length=None)
        
        if not qsp_docs:
            raise HTTPException(status_code=404, detail="No QSP documents found")
        
        # Get ISO summary for clauses
        iso_summary = await db.iso_summaries.find_one({}, {"_id": 0})
        if not iso_summary:
            raise HTTPException(status_code=404, detail="No ISO summary found")
        
        # Standard ISO 13485 clauses
        iso_clauses = [
            "4.1 General requirements",
            "4.2 Documentation requirements",
            "5.1 Management commitment",
            "5.2 Customer focus",
            "5.3 Quality policy",
            "5.4 Planning",
            "5.5 Responsibility, authority and communication",
            "5.6 Management review",
            "6.1 Provision of resources",
            "6.2 Human resources",
            "6.3 Infrastructure",
            "6.4 Work environment",
            "7.1 Planning of product realization",
            "7.2 Customer-related processes",
            "7.3 Design and development",
            "7.4 Purchasing",
            "7.5 Production and service provision",
            "7.6 Control of monitoring and measuring equipment",
            "8.1 General",
            "8.2 Monitoring and measurement",
            "8.3 Control of nonconforming product",
            "8.4 Analysis of data",
            "8.5 Improvement"
        ]
        
        # Clear existing mappings
        await db.clause_mappings.delete_many({})
        
        total_mappings = 0
        
        # Process each QSP document
        for qsp_doc in qsp_docs:
            qsp_doc = parse_from_mongo(qsp_doc)
            
            # Map each section
            for section_title, section_content in qsp_doc['sections'].items():
                if len(section_content) < 50:  # Skip very short sections
                    continue
                
                mappings = await analyze_clause_mapping(
                    section_content, qsp_doc['filename'], iso_clauses
                )
                
                for mapping in mappings:
                    if mapping.get('confidence_score', 0) > 0.3:  # Only store high-confidence mappings
                        clause_mapping = ClauseMapping(
                            qsp_id=qsp_doc['id'],
                            qsp_filename=qsp_doc['filename'],
                            section_title=section_title,
                            section_content=section_content[:500],  # Truncate for storage
                            iso_clause=mapping['iso_clause'],
                            confidence_score=mapping['confidence_score'],
                            evidence_text=mapping['evidence_text']
                        )
                        
                        mapping_dict = prepare_for_mongo(clause_mapping.model_dump())
                        await db.clause_mappings.insert_one(mapping_dict)
                        total_mappings += 1
        
        logger.info(f"Generated {total_mappings} clause mappings")
        
        return {
            "message": "Clause mapping completed successfully",
            "total_documents_processed": len(qsp_docs),
            "total_mappings_generated": total_mappings
        }
        
    except Exception as e:
        logger.error(f"Error running clause mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analysis/run-compliance")
async def run_compliance_analysis():
    """Run compliance gap analysis"""
    try:
        # Get ISO summary and mappings
        iso_summary = await db.iso_summaries.find_one({}, {"_id": 0})
        if not iso_summary:
            raise HTTPException(status_code=404, detail="No ISO summary found")
        
        mappings = await db.clause_mappings.find({}, {"_id": 0}).to_list(length=None)
        qsp_docs = await db.qsp_documents.find({}, {"_id": 0}).to_list(length=None)
        
        if not mappings:
            raise HTTPException(status_code=404, detail="No clause mappings found. Run mapping first.")
        
        # Extract changed clauses from ISO summary
        changed_clauses = set()
        iso_summary = parse_from_mongo(iso_summary)
        
        for clause in iso_summary.get('new_clauses', []):
            changed_clauses.add(clause.get('clause', ''))
        for clause in iso_summary.get('modified_clauses', []):
            changed_clauses.add(clause.get('clause', ''))
        
        # Find gaps
        gaps = []
        mapped_clauses = {}
        
        # Group mappings by clause
        for mapping in mappings:
            clause = mapping['iso_clause']
            if clause not in mapped_clauses:
                mapped_clauses[clause] = []
            mapped_clauses[clause].append(mapping)
        
        # Check for gaps in changed clauses
        for changed_clause in changed_clauses:
            if not changed_clause:
                continue
                
            # Find if any existing mappings cover this clause
            found_mapping = False
            low_confidence = []
            
            for clause, clause_mappings in mapped_clauses.items():
                if changed_clause in clause or any(changed_clause in m['iso_clause'] for m in clause_mappings):
                    found_mapping = True
                    # Check confidence scores
                    for mapping in clause_mappings:
                        if mapping['confidence_score'] < 0.7:
                            low_confidence.append(mapping)
            
            if not found_mapping:
                gap = ComplianceGap(
                    qsp_id="",
                    qsp_filename="Multiple",
                    iso_clause=changed_clause,
                    gap_type="missing",
                    description=f"No QSP documents found addressing the new/modified clause: {changed_clause}",
                    severity="high",
                    recommendations=[
                        f"Create or update QSP documentation to address {changed_clause}",
                        "Review existing procedures for compliance gaps",
                        "Assign responsibility for implementing new requirements"
                    ]
                )
                gaps.append(gap)
            elif low_confidence:
                for mapping in low_confidence:
                    gap = ComplianceGap(
                        qsp_id=mapping['qsp_id'],
                        qsp_filename=mapping['qsp_filename'],
                        iso_clause=mapping['iso_clause'],
                        gap_type="partial",
                        description=f"Low confidence mapping for {mapping['iso_clause']} in {mapping['qsp_filename']}",
                        severity="medium",
                        recommendations=[
                            "Review and strengthen documentation",
                            "Add more specific requirements",
                            "Clarify procedures and responsibilities"
                        ]
                    )
                    gaps.append(gap)
        
        # Calculate compliance score
        total_changed_clauses = len([c for c in changed_clauses if c])
        high_confidence_mappings = sum(1 for mapping in mappings if mapping['confidence_score'] > 0.7)
        
        if total_changed_clauses > 0:
            overall_score = min(high_confidence_mappings / total_changed_clauses * 100, 100)
        else:
            overall_score = 100
        
        # Get affected documents
        affected_docs = list(set(gap.qsp_filename for gap in gaps if gap.qsp_filename != "Multiple"))
        
        # Create analysis
        analysis = ComplianceAnalysis(
            overall_score=round(overall_score, 2),
            total_documents=len(qsp_docs),
            compliant_documents=len(qsp_docs) - len(affected_docs),
            gaps=gaps,
            affected_documents=affected_docs
        )
        
        # Store analysis
        analysis_dict = prepare_for_mongo(analysis.model_dump())
        await db.compliance_analyses.delete_many({})  # Keep only latest
        await db.compliance_analyses.insert_one(analysis_dict)
        
        logger.info(f"Compliance analysis completed. Found {len(gaps)} gaps.")
        
        return {
            "message": "Compliance analysis completed successfully",
            "overall_score": analysis.overall_score,
            "gaps_found": len(gaps),
            "affected_documents": len(affected_docs),
            "analysis_id": analysis.id
        }
        
    except Exception as e:
        logger.error(f"Error running compliance analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard")
async def get_dashboard_data():
    """Get dashboard overview data"""
    try:
        # Get latest analysis
        analysis = await db.compliance_analyses.find_one({}, {"_id": 0}, sort=[("analysis_date", -1)])
        
        # Get document counts
        total_docs = await db.qsp_documents.count_documents({})
        total_mappings = await db.clause_mappings.count_documents({})
        
        # Get ISO summary
        iso_summary = await db.iso_summaries.find_one({}, {"_id": 0})
        
        if analysis:
            analysis = parse_from_mongo(analysis)
        
        if iso_summary:
            iso_summary = parse_from_mongo(iso_summary)
        
        return {
            "compliance_score": analysis['overall_score'] if analysis else 0,
            "total_documents": total_docs,
            "total_mappings": total_mappings,
            "gaps_count": len(analysis['gaps']) if analysis else 0,
            "affected_documents": len(analysis['affected_documents']) if analysis else 0,
            "iso_summary_loaded": iso_summary is not None,
            "new_clauses_count": len(iso_summary.get('new_clauses', [])) if iso_summary else 0,
            "modified_clauses_count": len(iso_summary.get('modified_clauses', [])) if iso_summary else 0,
            "last_analysis_date": analysis['analysis_date'] if analysis else None
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents", response_model=List[Dict[str, Any]])
async def get_qsp_documents():
    """Get all QSP documents"""
    try:
        docs = await db.qsp_documents.find({}, {"_id": 0}).to_list(length=None)
        return [parse_from_mongo(doc) for doc in docs]
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/gaps")
async def get_compliance_gaps():
    """Get detailed compliance gaps"""
    try:
        analysis = await db.compliance_analyses.find_one({}, {"_id": 0}, sort=[("analysis_date", -1)])
        
        if not analysis:
            return {"gaps": [], "message": "No compliance analysis found. Run analysis first."}
        
        analysis = parse_from_mongo(analysis)
        
        return {
            "gaps": analysis['gaps'],
            "total_gaps": len(analysis['gaps']),
            "analysis_date": analysis['analysis_date']
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/mappings")
async def get_clause_mappings():
    """Get all clause mappings"""
    try:
        mappings = await db.clause_mappings.find({}, {"_id": 0}).to_list(length=None)
        return [parse_from_mongo(mapping) for mapping in mappings]
    except Exception as e:
        logger.error(f"Error getting mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()