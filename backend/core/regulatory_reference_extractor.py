"""
Regulatory Reference Extractor
Extracts explicit regulatory citations from QSP documents
"""
import re
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class RegulatoryReferenceExtractor:
    """
    Extracts structured regulatory references from QSP text
    Example: "per ISO 14971:2019 Clause 5.1" → structured data
    """
    
    def __init__(self):
        # Regex patterns for different reference types
        self.patterns = {
            'iso_standard': r'ISO\s+(\d+)(?::(\d{4}))?',
            'clause': r'(?:Clause|Section)\s+([\d.]+)',
            'annex': r'Annex\s+([A-Z]\d*)',
            'paragraph': r'(?:paragraph|para\.?)\s+([\d.]+)',
            'mdr_article': r'(?:MDR\s+)?Art(?:icle|\.)?\s+([\d.]+)',
            'cfr_section': r'21\s+CFR\s+([\d.]+)',
        }
        
    def extract_references(
        self, 
        qsp_text: str, 
        qsp_id: str,
        qsp_section: str = ""
    ) -> List[Dict]:
        """
        Extract all regulatory references from QSP text
        
        Args:
            qsp_text: Full text of QSP section
            qsp_id: QSP document ID (e.g., "9.1-3")
            qsp_section: Section path (e.g., "5.2.1")
            
        Returns:
            List of reference dictionaries with structure:
            {
                'qsp_id': '9.1-3',
                'qsp_section': '5.2.1',
                'standard': 'ISO 14971',
                'version': '2019',
                'clause': '5.1',
                'context': 'Risk management shall be...',
                'line_number': 67,
                'confidence': 0.95
            }
        """
        references = []
        
        # Split into lines for context
        lines = qsp_text.split('\n')
        
        for idx, line in enumerate(lines):
            # Find ISO standard references
            iso_matches = re.finditer(
                self.patterns['iso_standard'], 
                line, 
                re.IGNORECASE
            )
            
            for match in iso_matches:
                standard_num = match.group(1)
                version = match.group(2) if match.group(2) else None
                
                # Look for associated clause in nearby lines
                context_start = max(0, idx - 1)
                context_end = min(len(lines), idx + 2)
                context = ' '.join(lines[context_start:context_end])
                
                # Find clause number in context
                clause_match = re.search(
                    self.patterns['clause'], 
                    context, 
                    re.IGNORECASE
                )
                
                # Find annex in context
                annex_match = re.search(
                    self.patterns['annex'],
                    context,
                    re.IGNORECASE
                )
                
                ref = {
                    'qsp_id': qsp_id,
                    'qsp_section': qsp_section,
                    'standard': f'ISO {standard_num}',
                    'version': version,
                    'clause': clause_match.group(1) if clause_match else None,
                    'annex': annex_match.group(1) if annex_match else None,
                    'reference_text': line.strip(),
                    'context': context[:200],
                    'line_number': idx + 1,
                    'confidence': self._calculate_confidence(match, context),
                    'created_at': datetime.utcnow()
                }
                
                references.append(ref)
                
        logger.info(f"Extracted {len(references)} references from QSP {qsp_id}")
        return references
    
    def _calculate_confidence(self, match, context: str) -> float:
        """
        Calculate confidence score for reference extraction
        
        High confidence (0.9+): Has version, clause, and action verb
        Medium confidence (0.7-0.9): Has some but not all elements
        Low confidence (0.5-0.7): Basic reference only
        """
        score = 0.6  # Base score
        
        # Has version year (e.g., :2019)
        if re.search(r':\d{4}', context):
            score += 0.15
            
        # Has specific clause number
        if re.search(r'(?:Clause|Section)\s+[\d.]+', context, re.IGNORECASE):
            score += 0.15
            
        # Has action verb (implements, complies, per, according to)
        action_verbs = [
            r'\bper\b',
            r'\baccording to\b',
            r'\bcomplies with\b',
            r'\bimplements\b',
            r'\bin accordance with\b'
        ]
        if any(re.search(verb, context, re.IGNORECASE) for verb in action_verbs):
            score += 0.10
            
        return min(score, 1.0)
