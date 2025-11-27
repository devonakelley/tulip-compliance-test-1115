"""
Reference Extraction Engine
Extracts Form, WI, and QSP references from document text
Supports full 5-level document hierarchy traceability
"""
import re
import logging
from typing import Dict, List, Set, Optional

from models.regulatory import DocumentType

logger = logging.getLogger(__name__)


class ReferenceExtractor:
    """
    Extract references to Forms, Work Instructions, and QSPs from document text.
    Patterns based on real Tulip Medical documents.
    """
    
    def __init__(self):
        # Pattern: Form 7.3-3-1, Forms 4.2-1-2, form 6.2-1-2
        self.form_pattern = r'Form[s]?\s+(\d+(?:\.\d+)?(?:-\d+){1,3})'
        
        # Pattern: WI-003, WI 006, Work Instruction 7.3-1
        self.wi_pattern = r'(?:WI[-\s]?|Work\s+Instruction\s+)(\d+(?:\.\d+)?(?:-\d+)?)'
        
        # Pattern: QSP 7.3-3, QSP 4.2-1
        self.qsp_pattern = r'QSP\s+(\d+\.\d+-\d+)'
    
    def extract_all_references(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all types of references from text.
        
        Args:
            text: Document text to parse
            
        Returns:
            {
                "forms": ["7.3-3-1", "7.3-3-2", "4.2-1-2"],
                "work_instructions": ["WI-003", "WI-006"],
                "qsp_references": ["7.3-1", "4.2-1"]
            }
        """
        if not text:
            return {
                "forms": [],
                "work_instructions": [],
                "qsp_references": []
            }
        
        try:
            return {
                "forms": self._extract_forms(text),
                "work_instructions": self._extract_wis(text),
                "qsp_references": self._extract_qsps(text)
            }
        except Exception as e:
            logger.error(f"Failed to extract references: {e}")
            return {
                "forms": [],
                "work_instructions": [],
                "qsp_references": []
            }
    
    def _extract_forms(self, text: str) -> List[str]:
        """
        Extract Form references like: Form 7.3-3-1, Forms 4.2-1-2
        
        Examples from real docs:
        - "documented in Form 7.3-3-2"
        - "using Forms 4.2-1-2 and 4.2-1-3"
        """
        matches = re.findall(self.form_pattern, text, re.IGNORECASE)
        return sorted(set(matches))
    
    def _extract_wis(self, text: str) -> List[str]:
        """
        Extract Work Instruction references like: WI-003, WI 006
        
        Examples from real docs:
        - "following WI-003 Visual Inspection"
        - "See Work Instruction 006"
        """
        matches = re.findall(self.wi_pattern, text, re.IGNORECASE)
        # Normalize to WI-XXX format
        normalized = []
        for match in matches:
            if not match.startswith('WI'):
                normalized.append(f"WI-{match}")
            else:
                normalized.append(match)
        return sorted(set(normalized))
    
    def _extract_qsps(self, text: str) -> List[str]:
        """
        Extract QSP cross-references like: QSP 7.3-3, QSP 4.2-1

        Examples from real docs:
        - "in accordance with QSP 7.3-1 Design and Development"
        - "see QSP 4.2-3 Change Control"
        """
        matches = re.findall(self.qsp_pattern, text, re.IGNORECASE)
        return sorted(set(matches))

    def determine_document_type(self, doc_id: str) -> Optional[DocumentType]:
        """
        Determine document type from ID string.

        Supports Tulip Medical naming conventions:
        - QM1 R26 -> Quality Manual
        - QSP 7.3-1 -> QSP
        - WI-003, WI-006 -> Work Instruction
        - Form 7.3-3-1 -> Form
        - RFD-001 -> Reference Doc

        Args:
            doc_id: Document identifier string

        Returns:
            DocumentType enum or None if unknown
        """
        if not doc_id:
            return None

        doc_id_upper = doc_id.upper()

        # Quality Manual: QM1 R26, QM R5, etc.
        if 'QM' in doc_id_upper and ('R' in doc_id_upper or 'QUALITY MANUAL' in doc_id_upper):
            return DocumentType.QUALITY_MANUAL
        # QSP: QSP 7.3-1, QSP 4.2-1, etc.
        elif 'QSP' in doc_id_upper:
            return DocumentType.QSP
        # Work Instructions: WI-003, WI-006, WI – Training Records
        elif 'WI-' in doc_id_upper or 'WI ' in doc_id_upper or doc_id_upper.startswith('WI'):
            return DocumentType.WORK_INSTRUCTION
        # Forms: Form 7.3-3-1, F-DC-001, Form – Electronic Approval
        elif 'FORM' in doc_id_upper or doc_id_upper.startswith('F-'):
            return DocumentType.FORM
        # Reference Docs: RFD-001, RSK-04.1, CER-002, GSPR-2024
        elif any(prefix in doc_id_upper for prefix in ['RFD', 'RSK-', 'CER-', 'GSPR-', 'PMS', 'PMCF', 'PMSR', 'DMR']):
            return DocumentType.REFERENCE_DOC
        # Evidence: certificates, validation reports, etc.
        elif any(term in doc_id_upper for term in ['CERT', 'REPORT', 'VALIDATION', 'NAMSA', 'STERIS']):
            return DocumentType.EVIDENCE
        else:
            return None

    def get_document_level(self, doc_type: DocumentType) -> int:
        """
        Get hierarchy level for document type.

        Levels based on medical device QMS hierarchy:
        1 - Quality Manual (QM)
        2 - Quality System Procedures (QSP)
        3 - Work Instructions (WI)
        4 - Forms
        5 - Reference Documents (RFD)
        6 - Evidence/Records

        Args:
            doc_type: DocumentType enum

        Returns:
            Hierarchy level (1-6), defaults to 6 for unknown
        """
        level_map = {
            DocumentType.QUALITY_MANUAL: 1,
            DocumentType.QSP: 2,
            DocumentType.WORK_INSTRUCTION: 3,
            DocumentType.FORM: 4,
            DocumentType.REFERENCE_DOC: 5,
            DocumentType.EVIDENCE: 6
        }
        return level_map.get(doc_type, 6)

    def get_level_name(self, level: int) -> str:
        """Get human-readable name for hierarchy level"""
        level_names = {
            1: "Quality Manual",
            2: "Quality System Procedure (QSP)",
            3: "Work Instruction (WI)",
            4: "Form",
            5: "Reference Document",
            6: "Evidence/Record"
        }
        return level_names.get(level, "Unknown")


# Singleton pattern
_reference_extractor = None

def get_reference_extractor() -> ReferenceExtractor:
    """Get singleton reference extractor instance"""
    global _reference_extractor
    if _reference_extractor is None:
        _reference_extractor = ReferenceExtractor()
    return _reference_extractor


# Backwards compatibility: export singleton instance
reference_extractor = get_reference_extractor()
