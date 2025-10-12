# QSP Compliance Checker

**Automated regulatory impact analysis for medical device Quality System Procedures (QSPs)**

## 🎯 What This System Does

The QSP Compliance Checker automatically identifies when regulatory changes (like ISO 13485:2024 updates) impact your internal QSP documents, generating specific alerts like:

> **"ISO change detected that impacts QSP doc 4.2-1 in section 2.3 (Document Approval)"**

### Core Problem Solved
Medical device companies have 40+ QSP documents that must comply with evolving regulations. When ISO/FDA/EU releases updates, compliance teams need to know exactly which QSP sections require review and updates.

## 🚀 Key Features

### 📄 **Document Processing**
- Upload QSP documents (.docx, .txt, PDF) 
- Upload regulatory change summaries from ISO/FDA/EU
- Intelligent parsing preserves QSP section structure
- RAG-powered semantic analysis for accuracy

### 🤖 **AI-Powered Impact Analysis** 
- Multi-model AI (GPT, Claude, Gemini) via Emergent LLM
- Semantic search finds relevant sections (not just keywords)
- Confidence scoring ensures reliable alerts (70%+ threshold)
- Handles unlimited document sizes via chunking strategy

### 🚨 **Specific Alert Generation**
- Pinpoints exact QSP document and section affected
- Provides actionable recommendations for compliance teams
- Prioritizes alerts by impact level (critical/high/medium/low)
- Tracks alert status and resolution

### 📊 **Compliance Dashboard**
- Real-time view of open regulatory alerts
- Document impact history tracking  
- Compliance status overview across all QSPs
- Progress monitoring for alert resolution

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │────│   FastAPI        │────│   MongoDB       │
│   (Dashboard)   │    │   (RAG Engine)   │    │   (Documents)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ ChromaDB         │────│ Emergent LLM    │
                       │ (Vector Store)   │    │ (Multi-Model)   │
                       └──────────────────┘    └─────────────────┘
```

### Technology Stack
- **Backend**: FastAPI + MongoDB + ChromaDB (vector database)
- **Frontend**: React + Tailwind CSS + Professional UI components
- **AI**: Emergent LLM integration (GPT/Claude/Gemini)
- **RAG Engine**: Sentence transformers + semantic search
- **Deployment**: Docker + Docker Compose

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+  
- MongoDB 7.0+
- Docker & Docker Compose
- Emergent LLM API Key

### 1. Automated Setup
```bash
git clone <repository-url>
cd qsp-compliance-system
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 2. Manual Setup
```bash
# Environment configuration
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Add your Emergent LLM key to backend/.env
EMERGENT_LLM_KEY=your-emergent-llm-key-here

# Start services
docker-compose up --build -d

# Verify system
./scripts/test.sh
```

### 3. Access Application
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/api/docs  
- **System Health**: http://localhost:8001/health

## 📋 Usage Workflow

### Step 1: Upload QSP Documents
```bash
curl -X POST "http://localhost:8001/api/documents/upload" \
  -F "file=@QSP_4.2-1_Document_Control.docx" \
  -F "document_type=qsp"
```

### Step 2: Process Documents for RAG
```bash
curl -X POST "http://localhost:8001/api/documents/{document_id}/process-rag"
```

### Step 3: Upload Regulatory Changes  
```bash
curl -X POST "http://localhost:8001/api/regulatory/batch-analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "changes": [
      {
        "clause_id": "4.2.3",
        "clause_title": "Document Control", 
        "description": "New electronic document control requirements...",
        "impact_level": "high"
      }
    ]
  }'
```

### Step 4: View Generated Alerts
```bash
curl "http://localhost:8001/api/alerts/open"
```

## 🔧 Key API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload QSP or regulatory documents
- `POST /api/documents/{id}/process-rag` - Process document for semantic search
- `GET /api/documents` - List uploaded documents
- `DELETE /api/documents/{id}` - Delete document

### Regulatory Impact Analysis  
- `POST /api/regulatory/analyze-impact` - Analyze single regulatory change
- `POST /api/regulatory/batch-analyze` - Analyze multiple changes
- `GET /api/alerts/open` - Get open regulatory alerts
- `GET /api/documents/{id}/impact-history` - View document impact history

### System Monitoring
- `GET /health` - System health check
- `GET /api/rag/statistics` - RAG system statistics
- `GET /metrics` - Prometheus metrics

## 📊 Example Alert Output

```json
{
  "alert_id": "alert_12345",
  "message": "ISO change detected that impacts QSP 4.2-1 Document Control in section 2.3 (Document Approval). Regulatory change in clause 4.2.3 (Document Control) requires review and potential updates.",
  "priority": "high",
  "regulatory_change": {
    "clause_id": "4.2.3",
    "clause_title": "Document Control",
    "description": "New electronic document control requirements..."
  },
  "affected_document": {
    "document_id": "qsp_4_2_1", 
    "document_title": "QSP 4.2-1 Document Control.docx",
    "section_number": "2.3",
    "section_title": "Document Approval"
  },
  "impact_details": {
    "impact_level": "high",
    "confidence_score": 0.87,
    "required_actions": [
      "Update document approval procedures for electronic signatures",
      "Implement audit trail requirements",
      "Review version control processes"
    ],
    "compliance_risk": "High risk of non-compliance if not addressed within 90 days"
  }
}
```

## 🔍 RAG System Benefits

### Why RAG vs Traditional Keyword Search?

**Traditional Approach Problems:**
- ❌ Can't fit 48 QSP files in LLM context window (4K-32K tokens)
- ❌ Keyword matching misses paraphrased requirements  
- ❌ No confidence scoring for reliability
- ❌ Misses semantic relationships between concepts

**Our RAG Solution:**
- ✅ **Unlimited document processing** via intelligent chunking
- ✅ **Semantic understanding** finds related concepts, not just exact matches
- ✅ **Section-level precision** maps to specific QSP sections  
- ✅ **High confidence alerts** (70%+ threshold) reduces false positives
- ✅ **Scalable architecture** handles growing document sets

### RAG Architecture Components

1. **Document Chunker**: Preserves QSP structure while creating searchable chunks
2. **Embedding Service**: Converts text to semantic vectors for similarity search
3. **Vector Store**: ChromaDB for efficient storage and retrieval  
4. **Impact Analyzer**: Uses retrieval + AI generation for accurate impact assessment

## 🔐 Security & Compliance

- **JWT Authentication** with role-based access control
- **API Rate Limiting** prevents abuse
- **Audit Logging** tracks all document and analysis actions  
- **Secure File Upload** with validation and virus scanning
- **Data Encryption** in transit and at rest
- **GDPR Compliant** data handling practices

## 📈 Monitoring & Operations

### Health Monitoring
- System health checks for database, AI services, storage
- Real-time performance metrics via Prometheus
- Automated alerting for system issues
- Uptime monitoring and SLA tracking

### Backup & Recovery
```bash
# Create backup
./scripts/backup.sh

# Restore from backup  
./scripts/restore.sh /app/backups/qsp_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Performance Optimization
- MongoDB indexing for fast document queries
- Vector database optimization for similarity search
- Async processing for large document sets
- Caching layer for frequently accessed data

## 🤝 Support & Maintenance

### Troubleshooting
```bash
# Check system status
./scripts/test.sh

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Update and restart
docker-compose down
docker-compose up --build -d
```

### Common Issues
1. **LLM Service Not Available**: Check `EMERGENT_LLM_KEY` in backend/.env
2. **Documents Not Processing**: Verify MongoDB connection and disk space
3. **Slow Analysis**: Increase RAG system resources in docker-compose.yml

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Getting Help

1. **System Issues**: Check `/health` endpoint and system logs
2. **API Questions**: Visit `/api/docs` for interactive documentation  
3. **Performance**: Use `/metrics` endpoint for system diagnostics
4. **Bug Reports**: Create GitHub issue with logs and reproduction steps

---

**Built for medical device compliance teams to automate regulatory impact analysis and ensure QSP documents stay current with evolving standards.**