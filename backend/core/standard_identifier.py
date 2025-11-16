"""
Standard Identifier Module
Identifies ISO standards and determines appropriate comparison mode
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def identify_standard(document_text: str) -> Optional[Dict[str, str]]:
    """
    Extract ISO standard series, part number, and edition year from document.
    
    Args:
        document_text: Full text of the document or at minimum the title page
        
    Returns:
        dict with 'series', 'part', 'year', 'full_id' or None if not found
        
    Example:
        Input: "ISO 10993-18:2020"
        Output: {'series': '10993', 'part': '18', 'year': '2020', 
                 'full_id': 'ISO 10993-18:2020'}
    """
    # Look for pattern: ISO <series>-<part>:<year>
    # This pattern handles common ISO formats
    match = re.search(r'ISO\s+(\d+)-(\d+):(\d{4})', document_text)
    
    if match:
        result = {
            'series': match.group(1),  # e.g., "10993"
            'part': match.group(2),     # e.g., "17" or "18"
            'year': match.group(3),     # e.g., "2023" or "2020"
            'full_id': f"ISO {match.group(1)}-{match.group(2)}:{match.group(3)}"
        }
        logger.info(f"Identified standard: {result['full_id']}")
        return result
    
    # Also try to match format without colon (less common but possible)
    match_alt = re.search(r'ISO\s+(\d+)-(\d+)\s+\((\d{4})\)', document_text)
    if match_alt:
        result = {
            'series': match_alt.group(1),
            'part': match_alt.group(2),
            'year': match_alt.group(3),
            'full_id': f"ISO {match_alt.group(1)}-{match_alt.group(2)}:{match_alt.group(3)}"
        }
        logger.info(f"Identified standard (alternative format): {result['full_id']}")
        return result
    
    logger.warning("Could not identify ISO standard in document")
    return None


def should_diff_or_map(doc1_id: Optional[Dict], doc2_id: Optional[Dict]) -> str:
    """
    Determine what type of analysis should be performed on two documents.
    
    Args:
        doc1_id: dict from identify_standard() for first document
        doc2_id: dict from identify_standard() for second document
        
    Returns:
        str: 'VERSION_DIFF', 'CROSS_REFERENCE', or 'INCOMPATIBLE'
    """
    
    # Guard against None inputs
    if doc1_id is None or doc2_id is None:
        logger.warning("Cannot identify one or both documents")
        return 'INCOMPATIBLE'
    
    # Same series, same part, different years → VERSION UPDATE
    if (doc1_id['series'] == doc2_id['series'] and 
        doc1_id['part'] == doc2_id['part'] and 
        doc1_id['year'] != doc2_id['year']):
        logger.info(f"Detected VERSION_DIFF: {doc1_id['full_id']} vs {doc2_id['full_id']}")
        return 'VERSION_DIFF'
    
    # Same series, different parts → RELATED STANDARDS
    elif (doc1_id['series'] == doc2_id['series'] and 
          doc1_id['part'] != doc2_id['part']):
        logger.info(f"Detected CROSS_REFERENCE: {doc1_id['full_id']} and {doc2_id['full_id']} are different parts")
        return 'CROSS_REFERENCE'
    
    # Different series or same document uploaded twice
    else:
        logger.warning(f"Documents are INCOMPATIBLE: {doc1_id['full_id']} vs {doc2_id['full_id']}")
        return 'INCOMPATIBLE'


def get_incompatibility_reason(doc1_id: Optional[Dict], doc2_id: Optional[Dict]) -> str:
    """
    Provide detailed reason why documents cannot be compared
    
    Args:
        doc1_id: dict from identify_standard() for first document
        doc2_id: dict from identify_standard() for second document
        
    Returns:
        str: Human-readable explanation of why documents are incompatible
    """
    
    if doc1_id is None or doc2_id is None:
        return "Could not identify ISO standard number in one or both documents."
    
    if doc1_id['series'] != doc2_id['series']:
        return f"Different standard series: ISO {doc1_id['series']} vs ISO {doc2_id['series']}"
    
    if doc1_id['part'] == doc2_id['part'] and doc1_id['year'] == doc2_id['year']:
        return "Same document uploaded twice. Please upload different versions (years) of the same standard part."
    
    return "Documents are not comparable in the current context."


def create_cross_reference_response(doc1_id: Dict, doc2_id: Dict) -> Dict:
    """
    Generate informative response for cross-reference scenario
    
    Args:
        doc1_id: dict from identify_standard() for first document
        doc2_id: dict from identify_standard() for second document
        
    Returns:
        dict: Response with explanation and recommendations
    """
    return {
        'error': False,
        'analysis_type': 'CROSS_REFERENCE',
        'message': f"Standards {doc1_id['full_id']} and {doc2_id['full_id']} are companion documents.",
        'explanation': f"Part {doc1_id['part']} and Part {doc2_id['part']} are different parts of the ISO {doc1_id['series']} series.",
        'doc1': doc1_id['full_id'],
        'doc2': doc2_id['full_id'],
        'recommendation': "These should not be diffed against each other. They serve different purposes in the regulatory process.",
        'next_steps': [
            f"Part {doc1_id['part']} and Part {doc2_id['part']} work together but cover different aspects",
            "To track compliance, verify BOTH standards are satisfied separately",
            f"To see changes over time, upload different versions of Part {doc1_id['part']} or Part {doc2_id['part']}",
            f"Example: ISO {doc1_id['series']}-{doc1_id['part']}:2005 vs ISO {doc1_id['series']}-{doc1_id['part']}:2020"
        ]
    }


def create_incompatibility_error(doc1_id: Optional[Dict], doc2_id: Optional[Dict]) -> Dict:
    """
    Generate error response for incompatible documents
    
    Args:
        doc1_id: dict from identify_standard() for first document
        doc2_id: dict from identify_standard() for second document
        
    Returns:
        dict: Error response with details and suggestions
    """
    reason = get_incompatibility_reason(doc1_id, doc2_id)
    
    return {
        'error': True,
        'message': 'Cannot compare these documents',
        'doc1': doc1_id['full_id'] if doc1_id else 'Unknown standard',
        'doc2': doc2_id['full_id'] if doc2_id else 'Unknown standard',
        'reason': reason,
        'suggestion': 'Please upload two different versions (years) of the same standard part.',
        'examples': [
            "✅ Valid: ISO 10993-18:2005 and ISO 10993-18:2020 (same part, different years)",
            "❌ Invalid: ISO 10993-18:2020 and ISO 10993-17:2023 (different parts)",
            "❌ Invalid: ISO 10993-18:2020 and ISO 14971-1:2019 (different series)"
        ]
    }
