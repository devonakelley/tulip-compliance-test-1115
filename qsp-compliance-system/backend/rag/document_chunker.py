"""
Document chunker for QSP documents with semantic chunking strategy
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    content: str
    chunk_index: int
    document_id: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    chunk_type: str = "content"  # content, header, procedure, definition
    metadata: Dict[str, Any] = None
    token_count: int = 0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DocumentChunker:
    """
    Intelligent document chunker for QSP documents
    Preserves document structure and creates meaningful chunks
    """
    
    def __init__(self, max_chunk_tokens: int = 500, overlap_tokens: int = 50):
        """
        Initialize document chunker
        
        Args:
            max_chunk_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap tokens between chunks
        """
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        
        # QSP document structure patterns
        self.qsp_patterns = {
            'header': [
                r'^(Quality System Procedure|QSP)\s+\d+\.\d+[-\d]*\s+.*?$',
                r'^Tulip Medical.*?QSP.*?$'
            ],
            'section_number': [
                r'^(\d+\.\d*)\s+([A-Z][^:]+):?\s*$',  # 1.1 PURPOSE:
                r'^(\d+)\.\s+([A-Z][^:]+):?\s*$',     # 1. PURPOSE:
                r'^([A-Z]+)\.\s+([A-Z][^:]+):?\s*$'   # A. PURPOSE:
            ],
            'subsection': [
                r'^(\d+\.\d+\.\d+)\s+(.+?)$',         # 1.1.1 Subsection
                r'^([a-z]\))\s+(.+?)$',               # a) Subsection
                r'^(\([a-z]\))\s+(.+?)$'              # (a) Subsection
            ],
            'procedure_step': [
                r'^\s*(\d+)\.\s+(.+?)$',              # Numbered steps
                r'^\s*•\s+(.+?)$',                    # Bullet points
                r'^\s*-\s+(.+?)$'                     # Dashed lists
            ],
            'form_reference': [
                r'Form\s+[\d\.-]+[A-Z]*',
                r'QSP\s+[\d\.-]+[A-Z]*'
            ],
            'regulatory_reference': [
                r'ISO\s+\d+:?\d*',
                r'FDA\s+21\s+CFR\s+\d+',
                r'MDR\s+\(EU\)\s+\d+/\d+',
                r'Health\s+Canada'
            ]
        }
    
    async def chunk_document(self, document: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Chunk a QSP document preserving structure
        
        Args:
            document: Document dictionary with content, metadata
            
        Returns:
            List of document chunks
        """
        try:
            content = document.get('content', '')
            document_id = document.get('_id', document.get('id', 'unknown'))
            
            if not content.strip():
                logger.warning(f"Empty document content for {document_id}")
                return []
            
            # Split document into sections first
            sections = self._parse_qsp_sections(content)
            
            # Create chunks from sections
            chunks = []
            chunk_index = 0
            
            for section in sections:
                section_chunks = await self._chunk_section(
                    section, document_id, chunk_index
                )
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            return []
    
    def _parse_qsp_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse QSP document into logical sections"""
        lines = content.split('\n')
        sections = []
        current_section = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            section_match = self._match_section_header(line)
            
            if section_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'section_number': section_match.get('number'),
                    'section_title': section_match.get('title'),
                    'content': [],
                    'line_start': line_num,
                    'section_type': section_match.get('type', 'section')
                }
            
            # Add line to current section
            if current_section:
                current_section['content'].append(line)
            else:
                # No section yet, create a default one
                current_section = {
                    'section_number': None,
                    'section_title': 'Document Header',
                    'content': [line],
                    'line_start': line_num,
                    'section_type': 'header'
                }
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _match_section_header(self, line: str) -> Optional[Dict[str, str]]:
        """Match line against QSP section patterns"""
        
        # Check for main section numbers
        for pattern in self.qsp_patterns['section_number']:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'number': match.group(1),
                    'title': match.group(2).strip(),
                    'type': 'section'
                }
        
        # Check for subsections
        for pattern in self.qsp_patterns['subsection']:
            match = re.match(pattern, line)
            if match:
                return {
                    'number': match.group(1),
                    'title': match.group(2).strip() if len(match.groups()) > 1 else '',
                    'type': 'subsection'
                }
        
        # Check for procedure steps
        for pattern in self.qsp_patterns['procedure_step']:
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) > 1:
                    return {
                        'number': match.group(1),
                        'title': match.group(2).strip(),
                        'type': 'procedure_step'
                    }
                else:
                    return {
                        'number': None,
                        'title': match.group(1).strip(),
                        'type': 'procedure_step'
                    }
        
        return None
    
    async def _chunk_section(
        self,
        section: Dict[str, Any],
        document_id: str,
        start_chunk_index: int
    ) -> List[DocumentChunk]:
        """Chunk a single section"""
        
        section_content = '\n'.join(section['content'])
        section_tokens = len(self.tokenizer.encode(section_content))
        
        chunks = []
        
        # If section is small enough, keep as single chunk
        if section_tokens <= self.max_chunk_tokens:
            chunk = DocumentChunk(
                content=section_content,
                chunk_index=start_chunk_index,
                document_id=document_id,
                section_number=section.get('section_number'),
                section_title=section.get('section_title'),
                chunk_type=section.get('section_type', 'content'),
                token_count=section_tokens,
                metadata={
                    'line_start': section.get('line_start'),
                    'is_complete_section': True
                }
            )
            chunks.append(chunk)
        else:
            # Split large section into smaller chunks
            section_chunks = await self._split_large_section(
                section, document_id, start_chunk_index
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    async def _split_large_section(
        self,
        section: Dict[str, Any],
        document_id: str,
        start_chunk_index: int
    ) -> List[DocumentChunk]:
        """Split a large section into smaller chunks with overlap"""
        
        content_lines = section['content']
        chunks = []
        current_chunk_lines = []
        current_tokens = 0
        chunk_index = start_chunk_index
        
        for line in content_lines:
            line_tokens = len(self.tokenizer.encode(line))
            
            # Check if adding this line exceeds max tokens
            if current_tokens + line_tokens > self.max_chunk_tokens and current_chunk_lines:
                # Create chunk from current lines
                chunk_content = '\n'.join(current_chunk_lines)
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    document_id=document_id,
                    section_number=section.get('section_number'),
                    section_title=section.get('section_title'),
                    chunk_type=section.get('section_type', 'content'),
                    token_count=current_tokens,
                    metadata={
                        'is_partial_section': True,
                        'chunk_part': len(chunks) + 1
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_lines = self._get_overlap_lines(current_chunk_lines)
                current_chunk_lines = overlap_lines + [line]
                current_tokens = sum(len(self.tokenizer.encode(l)) for l in current_chunk_lines)
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_index=chunk_index,
                document_id=document_id,
                section_number=section.get('section_number'),
                section_title=section.get('section_title'),
                chunk_type=section.get('section_type', 'content'),
                token_count=current_tokens,
                metadata={
                    'is_partial_section': len(chunks) > 0,
                    'chunk_part': len(chunks) + 1
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_lines(self, lines: List[str]) -> List[str]:
        """Get overlap lines from the end of current chunk"""
        if not lines:
            return []
        
        overlap_text = '\n'.join(lines[-3:])  # Last 3 lines for context
        overlap_tokens = len(self.tokenizer.encode(overlap_text))
        
        if overlap_tokens <= self.overlap_tokens:
            return lines[-3:]
        elif len(lines) > 1:
            return lines[-2:]  # Try last 2 lines
        else:
            return lines[-1:]  # At least last line
    
    def enhance_chunk_metadata(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Enhance chunks with additional metadata"""
        
        for chunk in chunks:
            content = chunk.content.lower()
            
            # Add metadata about content type
            chunk.metadata.update({
                'has_form_references': bool(
                    any(re.search(pattern, chunk.content, re.IGNORECASE) 
                        for pattern in self.qsp_patterns['form_reference'])
                ),
                'has_regulatory_references': bool(
                    any(re.search(pattern, chunk.content, re.IGNORECASE)
                        for pattern in self.qsp_patterns['regulatory_reference'])
                ),
                'has_procedure_steps': bool(
                    any(re.search(pattern, chunk.content)
                        for pattern in self.qsp_patterns['procedure_step'])
                ),
                'content_length': len(chunk.content),
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            
            # Identify key themes in content
            themes = []
            if 'approval' in content or 'authorize' in content:
                themes.append('approval_process')
            if 'training' in content or 'competenc' in content:
                themes.append('training_requirement')
            if 'record' in content or 'document' in content:
                themes.append('documentation')
            if 'risk' in content or 'safety' in content:
                themes.append('risk_management')
            if 'design' in content or 'development' in content:
                themes.append('design_control')
            if 'nonconform' in content or 'corrective' in content:
                themes.append('quality_control')
            
            chunk.metadata['content_themes'] = themes
        
        return chunks