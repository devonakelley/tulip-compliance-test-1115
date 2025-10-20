# QSP Compliance Checker - Production Architecture

**Status**: Under development - Production-grade refactor in progress  
**Branch**: `production-rag-refactor`

## Design Principles

This system is designed for **regulated medical device QA/RA work** and must meet:
- FDA 21 CFR Part 11 compliance (audit trails, electronic signatures)
- ISO 13485 traceability requirements
- Deterministic, reviewable outputs
- Human-in-the-loop verification
- No automated document rewriting

## Architecture Overview

### 1. Document Ingestion & Parsing
- **Parsers**: PyMuPDF (PDF), python-docx (DOCX), Tesseract OCR (scanned docs)
- **Structure**: Section tree with:
  - `doc_id`, `source`, `version`, `title`
  - `section_path` (e.g., "4.2.2.b")
  - `clause_id`, `heading`, `text`, `page`, `rev_date`
- **Normalization**: Trim boilerplate, normalize whitespace, retain numbering

### 2. Chunking Strategy
- **Size**: 800-1200 tokens (~3200-4800 chars)
- **Overlap**: 150-200 tokens (~600-800 chars)
- **Method**: Section-aware heading + paragraph chunker
- **Metadata per chunk**:
  - `section_path`, `clause_id`, `page`
  - `doc_version`, `doc_type` (ISO/CFR/QSP/SOP/Form)

### 3. Hybrid Retrieval (Required for Production)

**Why Hybrid?** Vector search alone misses exact clause references; BM25 alone misses paraphrases.

**Flow**:
1. **BM25 (pg_trgm)**: Top-50 by clause IDs, headings, keywords
2. **Vector (pgvector)**: Top-50 by `text-embedding-3-large` semantic similarity
3. **Merge + Dedup**: Combine results
4. **Rerank**: Cross-encoder (`ms-marco-MiniLM-L-6-v2`) → final top-k

### 4. Rule-Assisted Mapping

- **Clause ID Extractor**: Regex for ISO/820/MDR forms
  - Patterns: `4.2.2`, `§820.70(c)`, `Annex I 23.1`
- **Constraint**: When IDs present, prioritize same framework/domain
- **Semantic Fallback**: When IDs absent, rely on vector + reranker
- **Output per mapping**:
  ```
  - external_clause_id, external_text_span
  - internal_doc_id, internal_section_path, internal_text_span
  - signals: {bm25_score, vector_score, rerank_score, clause_id_match}
  - confidence: 0..1 (calibrated)
  - rationale: 2-3 sentence explanation (LLM-generated, deterministic)
  ```

### 5. Gap Analysis (Flag-Only, No Rewriting)

**For each external clause, classify**:
- `covered`: Internal references exist
- `partial`: Missing sub-requirements
- `missing`: No coverage found
- `conflict`: Contradictory requirements

**Output**:
- Store internal references for "covered"
- List missing elements for "partial"
- Flag only for "missing" (no draft text)

**Strictly prohibited**: Automated redlines, suggested edits, document generation

### 6. Traceability & Audit

**Audit Chain**:
```
event_id, tenant_id, actor, action, doc_id
payload_sha256, prev_event_sha256, timestamp
```

- Append-only log (S3 + DB)
- Hash chain for tamper-evidence
- Verify on read

### 7. Human-in-the-Loop (HITL)

**Reviewer Actions**:
- Accept/reject mapping
- Adjust clause assignment
- Edit rationale
- Add comments
- Assign owner

**Feedback Loop**:
- Store reviewer decisions
- Re-calibrate confidence from accepted vs rejected mappings
- Improve retrieval over time

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | PostgreSQL + pgvector | Single DB for metadata + embeddings |
| BM25/Keyword | pg_trgm | Native, no cluster overhead |
| Embeddings | text-embedding-3-large (OpenAI) | Superior semantic quality for regulatory text |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 | Proven baseline, fast |
| Workers | RQ or Celery | Background jobs for ingestion/indexing |
| Storage | S3 or GCS | Raw docs + parsed JSON |
| Secrets | .env + Vault/Doppler | No secrets in repo |

## API Endpoints

```
POST /ingest          → Upload doc; returns doc_id, parsed sections
POST /index           → Embed + store sections in pgvector
POST /map             → {external_doc_id, internal_root_doc_id} → mappings + gaps
GET  /report/{run_id} → JSON + CSV export (review pack)
GET  /trace/{doc_id}  → Full lineage and audit trail
POST /review/{run_id}/mapping/{id} → HITL accept/reject/edit
```

## Data Schemas

### ClauseMapping
```python
{
  "run_id": str,
  "external_doc_id": str,
  "external_clause_id": Optional[str],
  "external_section_path": Optional[str],
  "internal_doc_id": str,
  "internal_section_path": str,
  "confidence": float,  # 0..1 calibrated
  "signals": {
    "bm25": float,
    "vector": float,
    "rerank": float,
    "clause_id_match": bool
  },
  "rationale": str,
  "created_at": datetime
}
```

### Gap
```python
{
  "run_id": str,
  "external_doc_id": str,
  "external_clause_id": Optional[str],
  "status": "covered" | "partial" | "missing" | "conflict",
  "missing_elements": List[str],
  "confidence": float,
  "reviewer_status": "unreviewed" | "accepted" | "rejected" | "needs_followup",
  "reviewer_comment": Optional[str],
  "created_at": datetime
}
```

### AuditEvent
```python
{
  "event_id": str,
  "tenant_id": str,
  "actor": str,
  "action": str,
  "doc_id": Optional[str],
  "payload_sha256": str,
  "prev_event_sha256": Optional[str],
  "timestamp": datetime
}
```

## Testing & Acceptance

### Unit Tests
- Clause ID extraction on gold set
- Chunker preserves section boundaries
- RAG returns known internal section for 100+ labeled pairs

### Integration Tests
- End-to-end mapping on labeled pack (ISO 13485 → QSP)
- Target: Recall@5 ≥ 0.9, MRR ≥ 0.8

### Security Tests
- RBAC enforcement
- Per-tenant isolation
- Audit chain validation

## Implementation Phases

**Phase 1: Repo Cleanup** ✅ (In progress)
- Move docs/examples to `/docs/archive`
- Remove data artifacts from git
- Clean module structure

**Phase 2: Hybrid Retrieval** (Next)
- Implement pgvector + pg_trgm
- Add cross-encoder reranker
- Validate Recall@5 ≥ 0.9

**Phase 3: Clause Extraction & Traceability**
- Build regex patterns for ISO/CFR/MDR
- Implement deterministic mapping
- Gap classification logic

**Phase 4: HITL Workflow**
- Reviewer UI for accept/reject
- Audit event chain
- Confidence calibration

## Compliance Notes

**What This System Does**:
- Identifies potential gaps between external standards and internal QSPs
- Provides evidence and rationale for human review
- Maintains auditable trail of all decisions

**What This System Does NOT Do**:
- Generate or edit regulatory documents
- Make compliance determinations without human review
- Replace qualified personnel in regulatory decisions

**Regulatory Responsibility**: All outputs must be reviewed and approved by qualified QA/RA personnel before use in regulatory submissions.

---

**Last Updated**: October 2024  
**Version**: 2.0 (Production Refactor)
