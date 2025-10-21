# Change Impact Detection System

## Overview

The Change Impact Detection system identifies which internal QSP (Quality System Procedure) sections are affected by regulatory changes. Instead of reviewing entire standards, QA/RA teams can focus on specific changes (e.g., ISO 13485:2024 → 2016 summary of changes) and quickly identify impacted procedures.

## Features

- **Change Input**: Upload JSON file with regulatory changes (clause_id, change_text, change_type)
- **Vector Search**: Uses OpenAI text-embedding-3-large for semantic matching
- **Confidence Scoring**: Cosine similarity threshold (0.55) to minimize false positives
- **Automatic Rationale**: Explains why each QSP section is flagged
- **Export Reports**: Download results as CSV for review
- **Audit Trail**: Every analysis run tracked with unique run_id

## Quick Start

### 1. Prepare Change Data

Create a JSON file with regulatory changes:

```json
[
  {
    "clause_id": "4.2.4",
    "change_text": "ISO 13485:2024 now requires organizations to establish procedures for electronic records...",
    "change_type": "modified"
  },
  {
    "clause_id": "7.5.1.1",
    "change_text": "New requirement: Organizations must implement risk-based validation...",
    "change_type": "new"
  }
]
```

### 2. Run Demo (Without Database)

```bash
cd /app/backend
export OPENAI_API_KEY="your-key"
python demo_change_impact.py
```

**Output**: 
- Console analysis report
- CSV file: `impact_analysis_demo.csv`

### 3. Use API (With Postgres)

**A. Ingest QSP Sections**:
```bash
curl -X POST http://localhost:8001/api/impact/ingest_qsp \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d @sample_qsp_sections.json
```

**B. Analyze Changes**:
```bash
curl -X POST http://localhost:8001/api/impact/analyze \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d @sample_deltas.json
```

**C. Download Report**:
```bash
curl http://localhost:8001/api/impact/report/{run_id}?format=csv \
  -H "Authorization: Bearer {token}" > report.csv
```

### 4. Use Frontend UI

1. Login to application
2. Navigate to "Change Impact" tab
3. Upload regulatory changes JSON
4. (Optional) Upload QSP sections JSON and click "Ingest"
5. Click "Run Impact Analysis"
6. Review results and export CSV

## Sample Data

### Regulatory Changes (`sample_deltas.json`)
- 5 real ISO 13485:2024 changes
- Includes: electronic records, process validation, cybersecurity, post-market surveillance

### QSP Sections (`sample_qsp_sections.json`)
- 10 realistic QSP sections
- Covers: document control, validation, surveillance, infrastructure

## Architecture

```
JSON Deltas → OpenAI Embeddings → Vector Search (pgvector) → Cosine Similarity → Top-K Results → Rationale Generation → CSV/JSON Export
```

**Components**:
- `core/change_impact_service.py` - Core logic (450 lines)
- `api/change_impact.py` - FastAPI router
- `components/ChangeImpactDetector.js` - React UI
- `demo_change_impact.py` - Standalone demo

## Confidence Scoring

- **High (>75%)**: Strong semantic match, likely needs review
- **Medium (60-75%)**: Moderate match, review recommended
- **Low (55-60%)**: Potential match, may be tangential
- **Threshold**: 0.55 (tunable based on validation)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/impact/ingest_qsp` | POST | Upload & embed QSP sections |
| `/api/impact/analyze` | POST | Run impact analysis |
| `/api/impact/report/{run_id}` | GET | Get JSON or CSV report |
| `/api/impact/upload_json` | POST | Upload deltas file directly |
| `/api/impact/runs` | GET | List analysis history |

## Database Schema (Postgres + pgvector)

**Tables**:
- `document_sections` - QSP sections with embeddings
- `section_embeddings` - Vector embeddings (1536-dim)
- `impact_results` - Clause→QSP mappings
- `analysis_runs` - Run metadata

## Validation

**Expected Results** (with sample data):
- 5 changes → 6-8 impacts detected
- Confidence range: 58% - 83%
- Average: 1-2 QSP sections per change
- Top match: 8.2.6 → 8.2.2 (Post-Market Surveillance) at 82.8%

## Next Steps (PRD-02 & PRD-03)

### Evaluation Harness (PRD-02)
- Build gold dataset (20-50 labeled examples)
- Measure Recall@5, Precision@1, MRR
- Tune confidence threshold
- Add calibration (optional)

### HITL Workflow (PRD-03)
- Review UI with Accept/Reject/Comment
- Reviewer audit trail
- Continuous improvement feedback loop

## Troubleshooting

**Issue**: `OPENAI_API_KEY not set`  
**Fix**: Export key in environment or add to `.env`

**Issue**: Postgres connection failed  
**Fix**: Use `demo_change_impact.py` for testing without database

**Issue**: Low confidence scores  
**Fix**: Tune threshold in `change_impact_service.py` (line 34)

**Issue**: No impacts found  
**Fix**: Verify QSP sections are ingested first, check embeddings generated

## Production Deployment

**Requirements**:
- PostgreSQL 15+ with pgvector extension
- OpenAI API key
- 2GB+ RAM for embeddings
- Audit logging enabled

**Configuration**:
- Set `POSTGRES_URL` in environment
- Adjust `impact_threshold` (default: 0.55)
- Configure `top_k` results per change (default: 5)

## License

Proprietary - Tulip Medical / Certaro

## Support

For questions or issues, contact the development team.
