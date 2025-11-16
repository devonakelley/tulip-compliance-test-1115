"""
ISO Diff Processor
Extracts text from old and new regulatory PDFs and generates deltas
"""
import fitz  # PyMuPDF
import difflib
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import json
from .standard_identifier import (
    identify_standard,
    should_diff_or_map,
    create_cross_reference_response,
    create_incompatibility_error
)

logger = logging.getLogger(__name__)


class ISODiffProcessor:
    """
    Process regulatory document changes between versions
    Extracts sections, performs diff, generates change deltas
    """
    
    def __init__(self):
        """Initialize processor"""
        self.clause_pattern = re.compile(r'(\d+(?:\.\d+)*)\s+([A-Z][^.\n]+)')
    
    def analyze_documents(
        self, 
        doc1_path: str, 
        doc2_path: str
    ) -> Dict[str, Any]:
        """
        Main entry point for document analysis. Routes to appropriate handler based on standard identification.
        
        Args:
            doc1_path: Path to first PDF document
            doc2_path: Path to second PDF document
            
        Returns:
            dict with analysis results or error message
            
        Raises:
            ValueError: If documents are incompatible for comparison
        """
        
        # Extract text from both documents
        doc1_text = self.extract_text_from_pdf(doc1_path)
        doc2_text = self.extract_text_from_pdf(doc2_path)
        
        # Identify both documents
        doc1_id = identify_standard(doc1_text)
        doc2_id = identify_standard(doc2_text)
        
        # Determine analysis mode
        analysis_mode = should_diff_or_map(doc1_id, doc2_id)
        
        # Route to appropriate handler
        if analysis_mode == 'VERSION_DIFF':
            logger.info(f"✅ Running version diff: {doc1_id['full_id']} vs {doc2_id['full_id']}")
            return self.run_version_diff(doc1_text, doc2_text, doc1_id, doc2_id)
        
        elif analysis_mode == 'CROSS_REFERENCE':
            logger.warning(f"⚠️ Different standards detected: {doc1_id['full_id']} and {doc2_id['full_id']}")
            logger.info(f"   Part {doc1_id['part']} and Part {doc2_id['part']} are companion standards.")
            logger.info(f"   Generating cross-reference response instead of diff.")
            return create_cross_reference_response(doc1_id, doc2_id)
        
        elif analysis_mode == 'INCOMPATIBLE':
            error_response = create_incompatibility_error(doc1_id, doc2_id)
            logger.error(f"❌ {error_response['message']}: {error_response['reason']}")
            
            # Raise exception with clear user-facing message
            raise ValueError(
                f"Cannot compare {error_response['doc1']} with {error_response['doc2']}.\n\n"
                f"Reason: {error_response['reason']}\n\n"
                f"To diff standards:\n"
                f"  ✅ Upload: ISO 10993-18:2005 and ISO 10993-18:2020\n"
                f"  ❌ Avoid: ISO 10993-18:2020 and ISO 10993-17:2023\n\n"
                f"Part 18 and Part 17 are companion standards, not versions."
            )
        
        # Should never reach here
        return {'error': True, 'message': 'Unknown analysis mode'}
    
    def run_version_diff(
        self,
        doc1_text: str,
        doc2_text: str,
        doc1_id: Dict[str, str],
        doc2_id: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Perform clause-by-clause diff for two versions of the same standard.
        This is the original diff logic for version comparison.
        
        Args:
            doc1_text: Full text of old version
            doc2_text: Full text of new version
            doc1_id: Standard identification dict for old version
            doc2_id: Standard identification dict for new version
            
        Returns:
            dict with diff results including deltas
        """
        # Extract clauses from both documents
        old_clauses = self.extract_clauses(doc1_text)
        new_clauses = self.extract_clauses(doc2_text)
        
        # Compute diff
        deltas = self.compute_diff(old_clauses, new_clauses)
        
        return {
            'success': True,
            'analysis_type': 'VERSION_DIFF',
            'old_standard': doc1_id['full_id'],
            'new_standard': doc2_id['full_id'],
            'old_year': doc1_id['year'],
            'new_year': doc2_id['year'],
            'total_changes': len(deltas),
            'deltas': deltas
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            logger.info(f"Extracted {len(text)} characters from {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def extract_clauses(self, text: str) -> Dict[str, str]:
        """
        Extract numbered clauses from regulatory text
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary mapping clause_id to clause text
        """
        clauses = {}
        lines = text.split('\n')
        current_clause = None
        current_text = []
        
        for line in lines:
            # Check if line starts a new clause
            match = self.clause_pattern.match(line.strip())
            
            if match:
                # Save previous clause
                if current_clause:
                    clauses[current_clause] = '\n'.join(current_text).strip()
                
                # Start new clause
                current_clause = match.group(1)
                current_text = [line.strip()]
            elif current_clause:
                # Continue current clause
                current_text.append(line.strip())
        
        # Save last clause
        if current_clause:
            clauses[current_clause] = '\n'.join(current_text).strip()
        
        logger.info(f"Extracted {len(clauses)} clauses")
        return clauses
    
    def compute_diff(
        self, 
        old_clauses: Dict[str, str], 
        new_clauses: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Compute differences between old and new clauses
        
        Args:
            old_clauses: Clauses from old version
            new_clauses: Clauses from new version
            
        Returns:
            List of deltas with change information
        """
        deltas = []
        
        # Find all clause IDs
        all_clause_ids = set(old_clauses.keys()) | set(new_clauses.keys())
        
        for clause_id in sorted(all_clause_ids):
            old_text = old_clauses.get(clause_id, '')
            new_text = new_clauses.get(clause_id, '')
            
            if not old_text and new_text:
                # New clause added
                deltas.append({
                    'clause_id': clause_id,
                    'change_type': 'added',
                    'old_text': '',
                    'new_text': new_text,
                    'change_text': new_text
                })
                
            elif old_text and not new_text:
                # Clause deleted
                deltas.append({
                    'clause_id': clause_id,
                    'change_type': 'deleted',
                    'old_text': old_text,
                    'new_text': '',
                    'change_text': old_text
                })
                
            elif old_text != new_text:
                # Clause modified
                # Generate detailed diff
                diff = self._generate_diff_text(old_text, new_text)
                
                deltas.append({
                    'clause_id': clause_id,
                    'change_type': 'modified',
                    'old_text': old_text,
                    'new_text': new_text,
                    'change_text': new_text,
                    'diff_html': diff
                })
        
        logger.info(f"Generated {len(deltas)} deltas")
        return deltas
    
    def _generate_diff_text(self, old_text: str, new_text: str) -> str:
        """
        Generate HTML-formatted diff between two texts
        
        Args:
            old_text: Original text
            new_text: Updated text
            
        Returns:
            HTML diff markup
        """
        differ = difflib.HtmlDiff()
        html_diff = differ.make_table(
            old_text.split('\n'),
            new_text.split('\n'),
            fromdesc='Old Version',
            todesc='New Version'
        )
        return html_diff
    
    def process_documents(
        self,
        old_pdf_path: str,
        new_pdf_path: str,
        output_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Process old and new regulatory PDFs to generate deltas.
        Now includes standard identification to prevent incorrect diffing.
        
        Args:
            old_pdf_path: Path to old version PDF
            new_pdf_path: Path to new version PDF
            output_path: Optional path to save deltas JSON
            
        Returns:
            List of delta objects
            
        Raises:
            ValueError: If documents are incompatible (e.g., different parts of same series)
        """
        try:
            logger.info("Starting ISO diff processing with standard identification...")
            
            # Use new analyze_documents method which includes standard identification
            analysis_result = self.analyze_documents(old_pdf_path, new_pdf_path)
            
            # Check analysis type
            if analysis_result.get('analysis_type') == 'VERSION_DIFF':
                # Extract deltas from successful version diff
                deltas = analysis_result.get('deltas', [])
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(deltas, f, indent=2)
                logger.info(f"Saved deltas to {output_path}")
            
            # Generate summary
            added = sum(1 for d in deltas if d['change_type'] == 'added')
            modified = sum(1 for d in deltas if d['change_type'] == 'modified')
            deleted = sum(1 for d in deltas if d['change_type'] == 'deleted')
            
            logger.info(f"✅ Diff complete: {added} added, {modified} modified, {deleted} deleted")
            
            return deltas
            
        except Exception as e:
            logger.error(f"Failed to process documents: {e}")
            raise
    
    def generate_unified_diff(self, old_text: str, new_text: str) -> str:
        """
        Generate unified diff format (for display)
        
        Args:
            old_text: Original text
            new_text: Updated text
            
        Returns:
            Unified diff string
        """
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='Old Version',
            tofile='New Version',
            lineterm=''
        )
        
        return '\n'.join(diff)


# Singleton instance
iso_diff_processor = ISODiffProcessor()


def get_iso_diff_processor() -> ISODiffProcessor:
    """Get singleton instance"""
    return iso_diff_processor
