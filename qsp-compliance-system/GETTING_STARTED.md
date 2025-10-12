# Getting Started with QSP Compliance Checker

## 🚀 5-Minute Setup Guide

### Step 1: Clone and Configure
```bash
git clone <your-repo-url>
cd qsp-compliance-system

# Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your EMERGENT_LLM_KEY
```

### Step 2: Start the System
```bash
# Automated deployment (recommended)
./scripts/deploy.sh

# OR manual start
docker-compose up --build -d
```

### Step 3: Verify Everything Works
```bash
./scripts/test.sh
```

### Step 4: Access the Application
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8001/api/docs
- **Health Check**: http://localhost:8001/health

## 📤 Upload Your First QSP Document

### Via Dashboard (Recommended)
1. Go to http://localhost:3000
2. Click "Upload QSP Document"
3. Select your QSP file (.docx, .pdf, .txt)
4. Wait for processing to complete

### Via API
```bash
curl -X POST "http://localhost:8001/api/documents/upload" \
  -F "file=@QSP_4.2-1_Document_Control.docx" \
  -F "document_type=qsp"
```

## 📋 Process Regulatory Changes

### Step 1: Upload ISO Change Summary
```bash
curl -X POST "http://localhost:8001/api/regulatory/batch-analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "changes": [
      {
        "clause_id": "4.2.3",
        "clause_title": "Document Control",
        "description": "New requirements for electronic document control systems with audit trails and version management.",
        "impact_level": "high",
        "effective_date": "2024-03-01"
      }
    ]
  }'
```

### Step 2: View Generated Alerts
```bash
curl "http://localhost:8001/api/alerts/open" | jq '.'
```

## 🎯 Expected Results

You should see alerts like:
```json
{
  "message": "ISO change detected that impacts QSP 4.2-1 Document Control in section 2.3 (Document Approval). Regulatory change in clause 4.2.3 requires review and potential updates.",
  "priority": "high",
  "affected_document": {
    "document_title": "QSP 4.2-1 Document Control.docx",
    "section_number": "2.3",
    "section_title": "Document Approval"
  },
  "required_actions": [
    "Update document approval procedures for electronic signatures",
    "Implement audit trail requirements"
  ]
}
```

## 🔧 Troubleshooting

### System Health Check
```bash
curl http://localhost:8001/health | jq '.'
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Common Issues

1. **"LLM service not available"**
   - Check `EMERGENT_LLM_KEY` in `backend/.env`
   - Restart: `docker-compose restart backend`

2. **"Database connection failed"**
   - Check MongoDB is running: `docker-compose ps`
   - Restart: `docker-compose restart mongodb`

3. **Frontend not loading**
   - Check ports 3000 and 8001 are available
   - Restart: `docker-compose restart frontend`

## 📊 Next Steps

1. **Upload all your QSP documents** via the dashboard
2. **Configure email alerts** in backend/.env (optional)
3. **Set up regular regulatory monitoring** with your compliance team
4. **Review the DEPLOYMENT.md** for production setup
5. **Check ARCHITECTURE.md** for technical details

## 🆘 Need Help?

- **System Status**: http://localhost:8001/health
- **API Documentation**: http://localhost:8001/api/docs
- **Metrics**: http://localhost:8001/metrics
- **Logs**: `docker-compose logs -f`

---

**Ready to automate your QSP compliance monitoring!** 🎉