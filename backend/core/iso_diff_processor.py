"""
ISO Diff Processor
Extracts text from old and new regulatory PDFs and generates deltas
"""
import fitz  # PyMuPDF
import difflib
import re
import logging
from typing import List, Dict, Any, Tuple
import json

logger = logging.getLogger(__name__)


class ISODiffProcessor:
    """
    Process regulatory document changes between versions
    Extracts sections, performs diff, generates change deltas
    """
    
    def __init__(self):
        """Initialize processor"""
        self.clause_pattern = re.compile(r'(\d+(?:\.\d+)*)\s+([A-Z][^.\n]+)')
    
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
        Process old and new regulatory PDFs to generate deltas
        
        Args:
            old_pdf_path: Path to old version PDF
            new_pdf_path: Path to new version PDF
            output_path: Optional path to save deltas JSON
            
        Returns:
            List of delta objects
        """
        try:
            logger.info("Starting ISO diff processing...")
            
            # Extract text from both PDFs
            logger.info("Extracting text from old PDF...")
            old_text = self.extract_text_from_pdf(old_pdf_path)
            
            logger.info("Extracting text from new PDF...")
            new_text = self.extract_text_from_pdf(new_pdf_path)
            
            # Extract clauses
            logger.info("Extracting clauses from old version...")
            old_clauses = self.extract_clauses(old_text)
            
            logger.info("Extracting clauses from new version...")
            new_clauses = self.extract_clauses(new_text)
            
            # Compute diff
            logger.info("Computing differences...")
            deltas = self.compute_diff(old_clauses, new_clauses)
            
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
