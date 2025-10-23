"""
QSP Document Parser
Parses DOCX/PDF/TXT QSP files into structured clause-level data
Extracts document number, clause numbers, titles, and text content
"""
import logging
import re
from typing import List, Dict, Any, Optional
from docx import Document
from pathlib import Path
import io

logger = logging.getLogger(__name__)


class QSPParser:
    """
    Parse QSP documents into structured clause-level data
    """
    
    def __init__(self):
        self.heading_styles = ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4', 'Heading 5']
    
    def extract_document_number(self, filename: str) -> str:
        """
        Extract document number from filename
        Examples:
        - "QSP 7.3-3 R9 Risk Management.docx" -> "7.3-3"
        - "QSP 6.2-1 R16 Training and Qualification.docx" -> "6.2-1"
        - "QSP 4.2-1 R13 Document Control.docx" -> "4.2-1"
        """
        try:
            # Pattern to match: QSP X.X-X or just X.X-X
            pattern = r'(?:QSP\s+)?(\d+\.\d+-\d+)'
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
            
            # Fallback: try simpler pattern X.X
            pattern2 = r'(?:QSP\s+)?(\d+\.\d+)'
            match2 = re.search(pattern2, filename)
            if match2:
                return match2.group(1)
            
            # If no pattern matched, return filename without extension
            return Path(filename).stem
            
        except Exception as e:
            logger.error(f"Failed to extract document number from {filename}: {e}")
            return Path(filename).stem
    
    def extract_revision(self, filename: str) -> str:
        """
        Extract revision from filename
        Examples:
        - "QSP 7.3-3 R9 Risk Management.docx" -> "R9"
        - "QSP 6.2-1 R16 Training.docx" -> "R16"
        """
        try:
            pattern = r'R(\d+)'
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return f"R{match.group(1)}"
            return "Unknown"
        except Exception as e:
            logger.error(f"Failed to extract revision from {filename}: {e}")
            return "Unknown"
    
    def is_heading_paragraph(self, paragraph) -> bool:
        """Check if a paragraph is a heading"""
        if not paragraph.text.strip():
            return False
        
        # Check style name
        if paragraph.style and paragraph.style.name in self.heading_styles:
            return True
        
        # Check if text looks like a heading (short, may have numbering)
        text = paragraph.text.strip()
        if len(text) < 100 and (
            re.match(r'^\d+\.', text) or  # Starts with number
            re.match(r'^[A-Z][^.!?]*$', text) or  # All caps or title case, no sentence ending
            text.isupper()  # All uppercase
        ):
            return True
        
        return False
    
    def extract_clause_number(self, heading_text: str) -> Optional[str]:
        """
        Extract clause number from heading text
        Examples:
        - "7.3.5 Risk Analysis" -> "7.3.5"
        - "4.2.1 General Requirements" -> "4.2.1"
        - "Section 6.2 Training" -> "6.2"
        """
        try:
            # Pattern for X.X.X or X.X format at start of heading
            pattern = r'^(\d+(?:\.\d+)*)'
            match = re.search(pattern, heading_text.strip())
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"Failed to extract clause number from '{heading_text}': {e}")
            return None
    
    def parse_docx(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse DOCX file into structured clause-level data
        
        Returns:
        {
            "document_number": "7.3-3",
            "revision": "R9",
            "filename": "QSP 7.3-3 R9 Risk Management.docx",
            "clauses": [
                {
                    "document_number": "7.3-3",
                    "clause_number": "7.3.5",
                    "title": "Risk Analysis",
                    "text": "The risk analysis can be recorded on Form 7.3-3-2...",
                    "characters": 312
                }
            ]
        }
        """
        try:
            doc = Document(io.BytesIO(file_content))
            document_number = self.extract_document_number(filename)
            revision = self.extract_revision(filename)
            
            clauses = []
            current_heading = None
            current_clause_number = None
            current_text_parts = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                
                if not text:
                    continue
                
                if self.is_heading_paragraph(paragraph):
                    # Save previous section if exists
                    if current_heading:
                        section_text = '\n'.join(current_text_parts).strip()
                        if not section_text:
                            section_text = "No text found"
                        
                        clauses.append({
                            "document_number": document_number,
                            "clause_number": current_clause_number or "Unknown",
                            "title": current_heading,
                            "text": section_text,
                            "characters": len(section_text)
                        })
                    
                    # Start new section
                    current_heading = text
                    current_clause_number = self.extract_clause_number(text)
                    current_text_parts = []
                else:
                    # Accumulate paragraph text
                    if current_heading:
                        current_text_parts.append(text)
            
            # Save last section
            if current_heading:
                section_text = '\n'.join(current_text_parts).strip()
                if not section_text:
                    section_text = "No text found"
                
                clauses.append({
                    "document_number": document_number,
                    "clause_number": current_clause_number or "Unknown",
                    "title": current_heading,
                    "text": section_text,
                    "characters": len(section_text)
                })
            
            logger.info(f"✅ Parsed {filename}: {len(clauses)} clauses extracted")
            
            return {
                "document_number": document_number,
                "revision": revision,
                "filename": filename,
                "total_clauses": len(clauses),
                "clauses": clauses
            }
            
        except Exception as e:
            logger.error(f"Failed to parse DOCX file {filename}: {e}")
            raise
    
    def parse_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse PDF file into structured clause-level data
        Uses PyPDF2 for text extraction
        """
        try:
            import PyPDF2
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract all text
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
            
            # Parse text into sections (similar logic to DOCX)
            document_number = self.extract_document_number(filename)
            revision = self.extract_revision(filename)
            
            clauses = self._parse_text_into_sections(full_text, document_number)
            
            logger.info(f"✅ Parsed PDF {filename}: {len(clauses)} clauses extracted")
            
            return {
                "document_number": document_number,
                "revision": revision,
                "filename": filename,
                "total_clauses": len(clauses),
                "clauses": clauses
            }
            
        except Exception as e:
            logger.error(f"Failed to parse PDF file {filename}: {e}")
            raise
    
    def parse_txt(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse TXT file into structured clause-level data
        """
        try:
            text = file_content.decode('utf-8', errors='ignore')
            document_number = self.extract_document_number(filename)
            revision = self.extract_revision(filename)
            
            clauses = self._parse_text_into_sections(text, document_number)
            
            logger.info(f"✅ Parsed TXT {filename}: {len(clauses)} clauses extracted")
            
            return {
                "document_number": document_number,
                "revision": revision,
                "filename": filename,
                "total_clauses": len(clauses),
                "clauses": clauses
            }
            
        except Exception as e:
            logger.error(f"Failed to parse TXT file {filename}: {e}")
            raise
    
    def _parse_text_into_sections(self, text: str, document_number: str) -> List[Dict[str, Any]]:
        """
        Parse plain text into sections based on heading patterns
        Used for PDF and TXT files
        """
        clauses = []
        lines = text.split('\n')
        
        current_heading = None
        current_clause_number = None
        current_text_parts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a heading
            # Criteria: short line (< 100 chars), starts with number, or all caps
            is_heading = (
                len(line) < 100 and (
                    re.match(r'^\d+\.', line) or
                    line.isupper()
                )
            )
            
            if is_heading:
                # Save previous section
                if current_heading:
                    section_text = '\n'.join(current_text_parts).strip()
                    if not section_text:
                        section_text = "No text found"
                    
                    clauses.append({
                        "document_number": document_number,
                        "clause_number": current_clause_number or "Unknown",
                        "title": current_heading,
                        "text": section_text,
                        "characters": len(section_text)
                    })
                
                # Start new section
                current_heading = line
                current_clause_number = self.extract_clause_number(line)
                current_text_parts = []
            else:
                # Accumulate text
                if current_heading:
                    current_text_parts.append(line)
        
        # Save last section
        if current_heading:
            section_text = '\n'.join(current_text_parts).strip()
            if not section_text:
                section_text = "No text found"
            
            clauses.append({
                "document_number": document_number,
                "clause_number": current_clause_number or "Unknown",
                "title": current_heading,
                "text": section_text,
                "characters": len(section_text)
            })
        
        return clauses
    
    def parse_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse file based on extension
        Supports: .docx, .pdf, .txt
        """
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'docx':
            return self.parse_docx(file_content, filename)
        elif file_ext == 'pdf':
            return self.parse_pdf(file_content, filename)
        elif file_ext == 'txt':
            return self.parse_txt(file_content, filename)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: docx, pdf, txt")


# Singleton instance
_qsp_parser = None

def get_qsp_parser() -> QSPParser:
    """Get singleton QSP parser instance"""
    global _qsp_parser
    if _qsp_parser is None:
        _qsp_parser = QSPParser()
    return _qsp_parser
