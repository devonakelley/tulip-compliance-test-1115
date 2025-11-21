"""
Reference Extraction Engine
Extracts Form, WI, and QSP references from document text
"""
import re
import logging
from typing import Dict, List, Set

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
