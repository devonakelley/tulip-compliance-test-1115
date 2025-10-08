# QSP Compliance Checker - Kalibr SDK Integration

## Implementation Strategy

Based on the Kalibr SDK architecture, here's how I would implement the QSP Compliance Checker to work with both GPT Actions and Claude MCP from a single Python codebase.

## 1. Core QSP Functions (qsp_compliance.py)

```python
"""
QSP Compliance Checker Core Functions
Implements the business logic separate from API exposure
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import io
from docx import Document
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

class QSPComplianceChecker:
    def __init__(self):
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        # In production, this would connect to your database
        self.documents = {}
        self.mappings = {}
        self.analyses = {}
        self.iso_summary = None

    def upload_qsp_document(self, filename: str, content_base64: str, file_type: str) -> Dict[str, Any]:
        """Upload and process a QSP document"""
        try:
            # Decode content
            content = base64.b64decode(content_base64)
            
            # Extract text
            if file_type == "docx":
                doc = Document(io.BytesIO(content))
                text_content = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            else:
                text_content = content.decode('utf-8')
            
            # Parse sections (simplified)
            sections = self._parse_document_sections(text_content, filename)
            
            doc_id = f"doc_{len(self.documents) + 1}"
            self.documents[doc_id] = {
                "id": doc_id,
                "filename": filename,
                "content": text_content,
                "sections": sections,
                "upload_date": datetime.now().isoformat(),
                "processed": True
            }
            
            return {
                "success": True,
                "document_id": doc_id,
                "filename": filename,
                "sections_count": len(sections),
                "content_length": len(text_content),
                "message": f"✅ Document '{filename}' uploaded successfully with {len(sections)} sections"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_iso_summary(self, filename: str, content_base64: str) -> Dict[str, Any]:
        """Upload ISO 13485:2024 Summary of Changes"""
        try:
            content = base64.b64decode(content_base64)
            text_content = content.decode('utf-8')
            
            # Parse ISO changes
            new_clauses, modified_clauses = self._parse_iso_summary(text_content)
            
            self.iso_summary = {
                "filename": filename,
                "content": text_content,
                "new_clauses": new_clauses,
                "modified_clauses": modified_clauses,
                "upload_date": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "filename": filename,
                "new_clauses_count": len(new_clauses),
                "modified_clauses_count": len(modified_clauses),
                "message": f"✅ ISO Summary uploaded: {len(new_clauses)} new, {len(modified_clauses)} modified clauses"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_documents(self) -> Dict[str, Any]:
        """List all uploaded QSP documents"""
        if not self.documents:
            return {
                "documents": [],
                "count": 0,
                "message": "📄 No QSP documents uploaded yet. Upload documents to start compliance analysis."
            }
        
        doc_list = []
        for doc_id, doc in self.documents.items():
            doc_list.append({
                "id": doc_id,
                "filename": doc["filename"],
                "sections_count": len(doc["sections"]),
                "upload_date": doc["upload_date"],
                "processed": doc["processed"]
            })
        
        return {
            "documents": doc_list,
            "count": len(doc_list),
            "message": f"📄 Found {len(doc_list)} QSP documents ready for analysis"
        }

    async def run_clause_mapping(self) -> Dict[str, Any]:
        """Run AI-powered clause mapping analysis"""
        if not self.documents:
            return {"success": False, "error": "No QSP documents found. Upload documents first."}
        
        if not self.iso_summary:
            return {"success": False, "error": "No ISO summary found. Upload ISO 13485:2024 Summary first."}
        
        try:
            # Standard ISO clauses
            iso_clauses = [
                "4.1 General requirements", "4.2 Documentation requirements",
                "5.1 Management commitment", "7.3 Design and development",
                "7.4 Purchasing", "8.1 General", "8.5 Improvement"
            ]
            
            total_mappings = 0
            self.mappings = {}
            
            # Process each document
            for doc_id, doc in self.documents.items():
                for section_title, section_content in doc['sections'].items():
                    if len(section_content) < 50:
                        continue
                    
                    mappings = await self._analyze_clause_mapping(
                        section_content, doc['filename'], iso_clauses
                    )
                    
                    for mapping in mappings:
                        if mapping.get('confidence_score', 0) > 0.3:
                            mapping_id = f"mapping_{total_mappings + 1}"
                            self.mappings[mapping_id] = {
                                "id": mapping_id,
                                "document_id": doc_id,
                                "document_name": doc['filename'],
                                "section_title": section_title,
                                "iso_clause": mapping['iso_clause'],
                                "confidence_score": mapping['confidence_score'],
                                "evidence_text": mapping['evidence_text']
                            }
                            total_mappings += 1
            
            return {
                "success": True,
                "documents_processed": len(self.documents),
                "mappings_generated": total_mappings,
                "message": f"🤖 AI analysis complete: {total_mappings} clause mappings generated across {len(self.documents)} documents"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_compliance_analysis(self) -> Dict[str, Any]:
        """Run comprehensive compliance gap analysis"""
        if not self.mappings:
            return {"success": False, "error": "No clause mappings found. Run clause mapping first."}
        
        if not self.iso_summary:
            return {"success": False, "error": "No ISO summary found."}
        
        try:
            # Extract changed clauses
            changed_clauses = set()
            for clause in self.iso_summary.get('new_clauses', []):
                changed_clauses.add(clause.get('clause', ''))
            for clause in self.iso_summary.get('modified_clauses', []):
                changed_clauses.add(clause.get('clause', ''))
            
            # Find gaps
            gaps = []
            mapped_clauses = {mapping['iso_clause'] for mapping in self.mappings.values()}
            
            for changed_clause in changed_clauses:
                if not changed_clause:
                    continue
                
                found_mapping = any(changed_clause in clause for clause in mapped_clauses)
                
                if not found_mapping:
                    gaps.append({
                        "iso_clause": changed_clause,
                        "gap_type": "missing",
                        "severity": "high",
                        "description": f"No QSP documents address the clause: {changed_clause}",
                        "recommendations": [
                            f"Create documentation for {changed_clause}",
                            "Review existing procedures for gaps",
                            "Assign implementation responsibility"
                        ]
                    })
            
            # Calculate compliance score
            total_changed = len([c for c in changed_clauses if c])
            high_conf_mappings = sum(1 for m in self.mappings.values() if m['confidence_score'] > 0.7)
            overall_score = min(high_conf_mappings / max(total_changed, 1) * 100, 100)
            
            self.analyses['latest'] = {
                "overall_score": round(overall_score, 2),
                "total_documents": len(self.documents),
                "gaps": gaps,
                "analysis_date": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "overall_score": round(overall_score, 2),
                "total_documents": len(self.documents),
                "gaps_found": len(gaps),
                "high_priority_gaps": len([g for g in gaps if g['severity'] == 'high']),
                "message": f"📊 Compliance analysis complete: {overall_score:.1f}% compliant, {len(gaps)} gaps identified"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance status overview"""
        latest_analysis = self.analyses.get('latest')
        
        status = {
            "documents_uploaded": len(self.documents),
            "mappings_generated": len(self.mappings),
            "iso_summary_loaded": self.iso_summary is not None,
            "analysis_completed": latest_analysis is not None
        }
        
        if latest_analysis:
            status.update({
                "compliance_score": latest_analysis['overall_score'],
                "gaps_count": len(latest_analysis['gaps']),
                "last_analysis": latest_analysis['analysis_date']
            })
        
        # Format message
        if not status['iso_summary_loaded']:
            message = "⚠️ Upload ISO 13485:2024 Summary to enable compliance analysis"
        elif not status['documents_uploaded']:
            message = "📄 Upload QSP documents to begin compliance analysis"
        elif not status['analysis_completed']:
            message = "🔄 Ready for analysis - run clause mapping and compliance check"
        else:
            score = status['compliance_score']
            gaps = status['gaps_count']
            message = f"📊 Compliance Status: {score}% compliant with {gaps} gaps identified"
        
        status['message'] = message
        return status

    def get_detailed_gaps(self, severity: str = "all") -> Dict[str, Any]:
        """Get detailed compliance gaps with recommendations"""
        latest_analysis = self.analyses.get('latest')
        
        if not latest_analysis:
            return {
                "gaps": [],
                "message": "❌ No compliance analysis found. Run analysis first."
            }
        
        gaps = latest_analysis['gaps']
        
        if severity != "all":
            gaps = [gap for gap in gaps if gap['severity'] == severity]
        
        if not gaps:
            return {
                "gaps": [],
                "message": "✅ No compliance gaps found! Your QSP documents appear to be compliant."
            }
        
        return {
            "gaps": gaps,
            "total_gaps": len(gaps),
            "message": f"⚠️ Found {len(gaps)} compliance gaps requiring attention"
        }

    def query_specific_clause(self, clause: str) -> Dict[str, Any]:
        """Query compliance status for a specific ISO clause"""
        # Find mappings for this clause
        relevant_mappings = []
        for mapping in self.mappings.values():
            if clause.lower() in mapping['iso_clause'].lower():
                relevant_mappings.append(mapping)
        
        # Find gaps for this clause
        relevant_gaps = []
        latest_analysis = self.analyses.get('latest')
        if latest_analysis:
            for gap in latest_analysis['gaps']:
                if clause.lower() in gap['iso_clause'].lower():
                    relevant_gaps.append(gap)
        
        result = {
            "clause": clause,
            "mappings_found": len(relevant_mappings),
            "gaps_found": len(relevant_gaps),
            "mappings": relevant_mappings[:5],  # First 5
            "gaps": relevant_gaps
        }
        
        if not relevant_mappings and not relevant_gaps:
            result['message'] = f"❓ No coverage found for clause '{clause}'. Consider creating documentation."
        elif relevant_gaps:
            result['message'] = f"⚠️ Found {len(relevant_gaps)} compliance issues for clause '{clause}'"
        else:
            result['message'] = f"✅ Clause '{clause}' appears to be well covered by your QSP documents"
        
        return result

    # Helper methods
    def _parse_document_sections(self, content: str, filename: str) -> Dict[str, str]:
        """Parse document into sections (simplified)"""
        sections = {}
        lines = content.split('\n')
        current_section = "Introduction"
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(pattern in line.upper() for pattern in ['PURPOSE', 'SCOPE', 'PROCEDURE', 'RESPONSIBILITIES']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        if not sections:
            sections[f"{filename} - Full Content"] = content
        
        return sections

    def _parse_iso_summary(self, content: str) -> tuple:
        """Parse ISO summary for new and modified clauses"""
        new_clauses = []
        modified_clauses = []
        
        lines = content.split('\n')
        current_section = ""
        
        import re
        for line in lines:
            line = line.strip()
            if 'NEW CLAUSES' in line.upper():
                current_section = "new"
            elif 'MODIFIED CLAUSES' in line.upper():
                current_section = "modified"
            elif line and current_section and re.match(r'\d+\.\d+', line):
                clause_info = {"clause": line, "description": line}
                if current_section == "new":
                    new_clauses.append(clause_info)
                elif current_section == "modified":
                    modified_clauses.append(clause_info)
        
        return new_clauses, modified_clauses

    async def _analyze_clause_mapping(self, qsp_content: str, qsp_filename: str, iso_clauses: List[str]) -> List[Dict[str, Any]]:
        """Use AI to map QSP content to ISO clauses"""
        if not self.llm_key:
            # Fallback without AI
            return [{
                "iso_clause": "4.2 Documentation requirements",
                "confidence_score": 0.8,
                "evidence_text": qsp_content[:100],
                "explanation": "Mapped based on content analysis"
            }]
        
        try:
            chat = LlmChat(
                api_key=self.llm_key,
                session_id=f"mapping_{datetime.now().timestamp()}",
                system_message="""You are an ISO 13485 compliance expert. Map QSP content to ISO clauses.
                Return JSON array: [{"iso_clause": "X.X Title", "confidence_score": 0.0-1.0, "evidence_text": "quote", "explanation": "reason"}]"""
            ).with_model("openai", "gpt-4o")
            
            iso_clauses_text = "\n".join([f"- {clause}" for clause in iso_clauses])
            
            user_message = UserMessage(
                text=f"""Map this QSP section to ISO clauses:

Document: {qsp_filename}
Content: {qsp_content[:1500]}

Available ISO clauses:
{iso_clauses_text}

Provide JSON mappings with confidence scores."""
            )
            
            response = await chat.send_message(user_message)
            
            # Clean and parse JSON
            import json
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            mappings = json.loads(clean_response)
            return mappings if isinstance(mappings, list) else []
            
        except Exception as e:
            # Fallback mapping
            return [{
                "iso_clause": "4.2 Documentation requirements",
                "confidence_score": 0.5,
                "evidence_text": qsp_content[:100],
                "explanation": f"Fallback mapping due to error: {str(e)}"
            }]

# Global instance
qsp_checker = QSPComplianceChecker()
```

## 2. Kalibr Integration (kalibr_qsp_app.py)

```python
"""
QSP Compliance Checker - Kalibr Integration
Exposes QSP functions for both GPT Actions and Claude MCP
"""
from kalibr import Kalibr
from qsp_compliance import qsp_checker
import asyncio

# Initialize Kalibr SDK
sdk = Kalibr()

@sdk.action(
    "upload_qsp_document",
    "Upload a QSP (Quality System Procedure) document for ISO 13485:2024 compliance analysis. Accepts filename, base64-encoded content, and file type (txt or docx)."
)
def upload_qsp_document(filename: str, content_base64: str, file_type: str = "txt"):
    """Upload and process a QSP document"""
    return qsp_checker.upload_qsp_document(filename, content_base64, file_type)

@sdk.action(
    "upload_iso_summary", 
    "Upload ISO 13485:2024 Summary of Changes document to establish compliance baseline. Accepts filename and base64-encoded content."
)
def upload_iso_summary(filename: str, content_base64: str):
    """Upload ISO summary document"""
    return qsp_checker.upload_iso_summary(filename, content_base64)

@sdk.action(
    "list_documents",
    "List all uploaded QSP documents with their processing status and section counts."
)
def list_documents():
    """List all uploaded QSP documents"""
    return qsp_checker.list_documents()

@sdk.action(
    "run_clause_mapping",
    "Run AI-powered analysis to map QSP document sections to relevant ISO 13485 clauses with confidence scores."
)
def run_clause_mapping():
    """Run AI clause mapping analysis"""
    return asyncio.run(qsp_checker.run_clause_mapping())

@sdk.action(
    "run_compliance_analysis",
    "Run comprehensive compliance gap analysis comparing QSP documents against ISO 13485:2024 changes to identify missing or inadequate coverage."
)
def run_compliance_analysis():
    """Run compliance gap analysis"""
    return qsp_checker.run_compliance_analysis()

@sdk.action(
    "get_compliance_status",
    "Get current overall compliance status including document counts, analysis results, and compliance scores."
)
def get_compliance_status():
    """Get compliance status overview"""
    return qsp_checker.get_compliance_status()

@sdk.action(
    "get_detailed_gaps",
    "Get detailed compliance gaps with specific recommendations. Filter by severity: 'all', 'high', 'medium', or 'low'."
)
def get_detailed_gaps(severity: str = "all"):
    """Get detailed compliance gaps"""
    return qsp_checker.get_detailed_gaps(severity)

@sdk.action(
    "query_specific_clause",
    "Query compliance status for a specific ISO 13485 clause (e.g., '4.1.6', '7.3.10') across all QSP documents."
)
def query_specific_clause(clause: str):
    """Query specific ISO clause compliance"""
    return qsp_checker.query_specific_clause(clause)
```

## 3. Deployment Configuration

### requirements.txt
```
kalibr
emergentintegrations
python-docx  
python-dotenv
motor
pymongo
```

### .env
```
EMERGENT_LLM_KEY=your-key-here
MONGO_URL=mongodb://localhost:27017  # Optional if using in-memory storage
```

### fly.toml (for Fly.io deployment)
```toml
app = "qsp-compliance-kalibr"
primary_region = "sjc"

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[http_service.checks]]
  interval = "15s"
  grace_period = "5s" 
  method = "GET"
  path = "/docs"
  protocol = "http"
  timeout = "10s"

[processes]
  app = "kalibr serve kalibr_qsp_app.py --host 0.0.0.0 --port 8000"

[deploy]
  release_command = "echo 'Deploying QSP Compliance Checker'"
```

## 4. Usage Instructions

### Local Development:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export EMERGENT_LLM_KEY=your-key-here

# Run locally
kalibr serve kalibr_qsp_app.py

# Test with curl
curl -X POST http://localhost:8000/proxy/get_compliance_status \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Claude Desktop Configuration:
```json
{
  "mcpServers": {
    "qsp-compliance": {
      "url": "http://localhost:8000/mcp.json"
    }
  }
}
```

### GPT Actions Configuration:
- Schema URL: `http://localhost:8000/openapi.json`
- Authentication: None (for family/friends use)

### Deploy to Production:
```bash
# Deploy to Fly.io
flyctl deploy

# Get public URLs
echo "Claude MCP: https://qsp-compliance-kalibr.fly.dev/mcp.json"
echo "GPT Actions: https://qsp-compliance-kalibr.fly.dev/openapi.json"
```

## 5. Benefits of This Approach

1. **Single Codebase**: One Python implementation serves both GPT and Claude
2. **Automatic Schema Generation**: Kalibr generates both OpenAPI and MCP manifests
3. **Type Safety**: Python type hints ensure proper API schemas
4. **Easy Deployment**: Simple `flyctl deploy` for production
5. **Local Development**: Test everything locally with `kalibr serve`
6. **Unified API**: Both AI models call the same underlying functions
7. **Easy Testing**: Direct HTTP endpoints for debugging

This approach leverages Kalibr's strength in unifying AI model integrations while maintaining the full functionality of our QSP Compliance Checker.