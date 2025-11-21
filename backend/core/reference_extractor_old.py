"""
Reference Extraction Service
Extracts document references and regulatory citations from document content
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from models.regulatory import DocumentType, RegulatoryFramework

logger = logging.getLogger(__name__)

class ReferenceExtractor:
    """Extract document references and regulatory citations from text"""
    
    def __init__(self):
        # Document reference patterns
        self.doc_patterns = {
            DocumentType.QSP: [
                r'QSP\s*\d+\.\d+-\d+(?:\s+R\d+)?',
                r'Quality\s+System\s+Procedure\s+\d+\.\d+-\d+'
            ],
            DocumentType.WORK_INSTRUCTION: [
                r'WI-[A-Z]{2,3}-\d{3,4}',
                r'Work\s+Instruction\s+[A-Z]{2,3}-\d{3,4}'
            ],
            DocumentType.FORM: [
                r'F-[A-Z]+-\d+',
                r'Form\s*\d+\.\d+-\d+-[A-Z]',
                r'Form\s+[A-Z]+-\d+'
            ],
            DocumentType.REFERENCE_DOC: [
                r'RFD-\d{3,4}(?:\s+R\d+)?',
                r'Reference\s+Document\s+\d{3,4}'
            ],
            DocumentType.QUALITY_MANUAL: [
                r'QM\d+\s*R\d+',
                r'Quality\s+Manual\s+R\d+'
            ]
        }
        
        # Regulatory citation patterns
        self.regulatory_patterns = {
            RegulatoryFramework.FDA_21CFR820: [
                r'21\s*CFR\s*(?:Part\s*)?820\.\d+(?:\.\d+)?',
                r'FDA\s+QSR\s+820\.\d+'
            ],
            RegulatoryFramework.ISO_13485: [
                r'ISO\s*13485:?(?:2016)?\s*(?:Clause\s*)?(\d+(?:\.\d+)*)',
                r'ISO\s*13485\s+Section\s+(\d+(?:\.\d+)*)'
            ],
            RegulatoryFramework.MDR_2017_745: [
                r'MDR\s*(?:2017/745\s*)?Article\s*(\d+)',
                r'MDR\s*(?:2017/745\s*)?Annex\s*([IVX]+)',
                r'Medical\s+Device\s+Regulation\s+Article\s*(\d+)'
            ],
            RegulatoryFramework.ISO_14971: [
                r'ISO\s*14971:?(?:2019)?\s*(?:Clause\s*)?(\d+(?:\.\d+)*)',
                r'ISO\s*14971\s+Section\s+(\d+(?:\.\d+)*)'
            ],
            RegulatoryFramework.ISO_10993: [
                r'ISO\s*10993-?(\d+)',
                r'ISO\s*10993\s+Part\s+(\d+)'
            ],
            RegulatoryFramework.ISO_11135: [
                r'ISO\s*11135:?(?:2014)?',
                r'EtO\s+Sterilization\s+Standard'
            ],
            RegulatoryFramework.ISO_11607: [
                r'ISO\s*11607-?(\d+)?',
                r'Packaging\s+Standard\s+ISO\s*11607'
            ],
            RegulatoryFramework.CFR_PART_11: [
                r'21\s*CFR\s*(?:Part\s*)?11',
                r'FDA\s+Part\s+11'
            ],
            RegulatoryFramework.MDSAP: [
                r'MDSAP',
                r'Medical\s+Device\s+Single\s+Audit\s+Program'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_doc_patterns = {}
        for doc_type, patterns in self.doc_patterns.items():
            self.compiled_doc_patterns[doc_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        self.compiled_reg_patterns = {}
        for framework, patterns in self.regulatory_patterns.items():
            self.compiled_reg_patterns[framework] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def extract_document_references(self, content: str) -> List[Dict[str, any]]:
        """
        Extract all document references from content
        
        Returns:
            List of {doc_type, reference, context}
        """
        references = []
        content_lower = content.lower()
        
        for doc_type, patterns in self.compiled_doc_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(content)
                for match in matches:
                    ref = match.group(0)
                    # Get context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()
                    
                    references.append({
                        'doc_type': doc_type.value,
                        'reference': self._normalize_reference(ref, doc_type),
                        'context': context,
                        'position': match.start()
                    })
        
        # Remove duplicates
        seen = set()
        unique_refs = []
        for ref in references:
            key = (ref['doc_type'], ref['reference'])
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)
        
        return sorted(unique_refs, key=lambda x: x['position'])
    
    def extract_regulatory_citations(self, content: str) -> List[Dict[str, any]]:
        """
        Extract all regulatory citations from content
        
        Returns:
            List of {framework, citation, clause_id, context}
        """
        citations = []
        
        for framework, patterns in self.compiled_reg_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(content)
                for match in matches:
                    citation = match.group(0)
                    
                    # Extract clause ID if present
                    clause_id = self._extract_clause_id(citation, framework)
                    
                    # Get context
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()
                    
                    citations.append({
                        'framework': framework.value,
                        'citation': citation,
                        'clause_id': clause_id,
                        'context': context,
                        'position': match.start()
                    })
        
        # Remove duplicates
        seen = set()
        unique_citations = []
        for cit in citations:
            key = (cit['framework'], cit['clause_id'] or cit['citation'])
            if key not in seen:
                seen.add(key)
                unique_citations.append(cit)
        
        return sorted(unique_citations, key=lambda x: x['position'])
    
    def _normalize_reference(self, ref: str, doc_type: DocumentType) -> str:
        """Normalize document reference format"""
        ref = ' '.join(ref.split())  # Normalize whitespace
        ref = ref.upper()
        
        # Standardize format
        if doc_type == DocumentType.QSP:
            # QSP 7.3-1 or QSP 7.3-1 R11
            match = re.search(r'(\d+\.\d+-\d+)', ref)
            if match:
                base = f"QSP {match.group(1)}"
                rev_match = re.search(r'R\d+', ref)
                if rev_match:
                    return f"{base} {rev_match.group(0)}"
                return base
        
        elif doc_type == DocumentType.WORK_INSTRUCTION:
            # WI-ENG-003
            match = re.search(r'WI-([A-Z]{2,3})-?(\d{3,4})', ref)
            if match:
                return f"WI-{match.group(1)}-{match.group(2)}"
        
        elif doc_type == DocumentType.FORM:
            # F-DC-001 or Form 4.2-1-A
            if 'F-' in ref:
                match = re.search(r'F-([A-Z]+)-(\d+)', ref)
                if match:
                    return f"F-{match.group(1)}-{match.group(2)}"
            else:
                match = re.search(r'(\d+\.\d+-\d+-[A-Z])', ref)
                if match:
                    return f"Form {match.group(1)}"
        
        return ref
    
    def _extract_clause_id(self, citation: str, framework: RegulatoryFramework) -> Optional[str]:
        """Extract clause/article ID from citation"""
        if framework == RegulatoryFramework.ISO_13485:
            match = re.search(r'Clause\s*(\d+(?:\.\d+)*)', citation, re.IGNORECASE)
            if match:
                return match.group(1)
            match = re.search(r'(\d+(?:\.\d+)*)', citation)
            if match:
                return match.group(1)
        
        elif framework == RegulatoryFramework.FDA_21CFR820:
            match = re.search(r'820\.(\d+)', citation)
            if match:
                return f"820.{match.group(1)}"
        
        elif framework == RegulatoryFramework.MDR_2017_745:
            match = re.search(r'Article\s*(\d+)', citation, re.IGNORECASE)
            if match:
                return f"Article {match.group(1)}"
            match = re.search(r'Annex\s*([IVX]+)', citation, re.IGNORECASE)
            if match:
                return f"Annex {match.group(1)}"
        
        elif framework == RegulatoryFramework.ISO_14971:
            match = re.search(r'(\d+(?:\.\d+)*)', citation)
            if match:
                return match.group(1)
        
        return None
    
    def determine_document_type(self, doc_id: str) -> Optional[DocumentType]:
        """Determine document type from ID"""
        doc_id_upper = doc_id.upper()
        
        if 'QM' in doc_id_upper and 'R' in doc_id_upper:
            return DocumentType.QUALITY_MANUAL
        elif 'QSP' in doc_id_upper:
            return DocumentType.QSP
        elif 'WI-' in doc_id_upper or 'WI ' in doc_id_upper:
            return DocumentType.WORK_INSTRUCTION
        elif 'FORM' in doc_id_upper or 'F-' in doc_id_upper:
            return DocumentType.FORM
        elif 'RFD' in doc_id_upper:
            return DocumentType.REFERENCE_DOC
        else:
            return None
    
    def get_document_level(self, doc_type: DocumentType) -> int:
        """Get hierarchy level for document type"""
        level_map = {
            DocumentType.QUALITY_MANUAL: 1,
            DocumentType.QSP: 2,
            DocumentType.WORK_INSTRUCTION: 3,
            DocumentType.FORM: 4,
            DocumentType.REFERENCE_DOC: 5,
            DocumentType.EVIDENCE: 6
        }
        return level_map.get(doc_type, 6)

# Singleton instance
reference_extractor = ReferenceExtractor()
