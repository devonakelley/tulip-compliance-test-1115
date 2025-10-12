"""
Text processing utilities for document analysis
"""

import re
import nltk
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Section:
    """Represents a document section"""
    number: Optional[str]
    title: str
    content: str
    level: int
    confidence: float = 0.8

class TextProcessor:
    """Advanced text processing for QSP documents"""
    
    def __init__(self):
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        
        # Section patterns for different document types
        self.section_patterns = {
            'qsp': [
                r'^(\d+(?:\.\d+)*)\s+(.+?)(?:\n|$)',  # Numbered sections: 1.1 Title
                r'^([A-Z]+)\.\s+(.+?)(?:\n|$)',       # Letter sections: A. Title
                r'^([IVX]+)\.\s+(.+?)(?:\n|$)'        # Roman numerals: I. Title
            ],
            'regulatory': [
                r'^(\d+(?:\.\d+)*)\s+(.+?)(?:\n|$)',  # Standard numbering
                r'^([A-Z])\)\s+(.+?)(?:\n|$)',        # A) Title format
                r'^\(([a-z])\)\s+(.+?)(?:\n|$)'       # (a) Title format
            ],
            'iso_summary': [
                r'^Clause\s+(\d+(?:\.\d+)*):?\s+(.+?)(?:\n|$)',
                r'^(\d+(?:\.\d+)*)\s+(.+?)(?:\n|$)',
                r'^([A-Z]+\.\d+)\s+(.+?)(?:\n|$)'
            ]
        }
    
    async def parse_sections(self, content: str, document_type: str) -> List[Dict[str, Any]]:
        """Parse document content into structured sections"""
        try:
            sections = []
            
            # Clean content first
            content = self._clean_content(content)
            
            # Get patterns for document type
            patterns = self.section_patterns.get(document_type, self.section_patterns['qsp'])
            
            # Split content into paragraphs
            paragraphs = self._split_paragraphs(content)
            
            # Process sections
            current_section = None
            section_content = []
            
            for paragraph in paragraphs:
                section_match = self._match_section_header(paragraph, patterns)
                
                if section_match:
                    # Save previous section if exists
                    if current_section:
                        sections.append({
                            "number": current_section.number,
                            "title": current_section.title,
                            "content": '\n\n'.join(section_content).strip(),
                            "level": current_section.level,
                            "confidence": current_section.confidence
                        })
                    
                    # Start new section
                    current_section = section_match
                    section_content = []
                else:
                    # Add to current section content
                    if paragraph.strip():
                        section_content.append(paragraph.strip())
            
            # Add final section
            if current_section:
                sections.append({
                    "number": current_section.number,
                    "title": current_section.title,
                    "content": '\n\n'.join(section_content).strip(),
                    "level": current_section.level,
                    "confidence": current_section.confidence
                })
            
            # If no sections found, create a single section
            if not sections and content.strip():
                sections.append({
                    "number": None,
                    "title": "Document Content",
                    "content": content.strip(),
                    "level": 1,
                    "confidence": 0.6
                })
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing sections: {e}")
            # Return content as single section
            return [{
                "number": None,
                "title": "Document Content",
                "content": content.strip(),
                "level": 1,
                "confidence": 0.5
            }]
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove page numbers and headers/footers
        content = re.sub(r'^\s*Page\s+\d+.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\s*/\s*\d+\s*$', '', content, flags=re.MULTILINE)
        
        # Fix common OCR errors
        content = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', content)  # Add space between words
        
        return content.strip()
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """Split content into meaningful paragraphs"""
        # Split by double newlines first
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Further split long paragraphs at sentence boundaries
        result = []
        for para in paragraphs:
            if len(para) > 1000:  # Long paragraph
                sentences = nltk.sent_tokenize(para)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > 800 and current_chunk:
                        result.append(' '.join(current_chunk))
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)
                
                if current_chunk:
                    result.append(' '.join(current_chunk))
            else:
                result.append(para)
        
        return [p for p in result if p.strip()]
    
    def _match_section_header(self, text: str, patterns: List[str]) -> Optional[Section]:
        """Match text against section header patterns"""
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                number = match.group(1) if match.group(1) else None
                title = match.group(2).strip() if len(match.groups()) > 1 else text.strip()
                
                # Determine section level from number
                level = self._get_section_level(number) if number else 1
                
                # Calculate confidence based on pattern match
                confidence = self._calculate_confidence(text, number, title)
                
                return Section(
                    number=number,
                    title=title,
                    content="",
                    level=level,
                    confidence=confidence
                )
        
        return None
    
    def _get_section_level(self, number: str) -> int:
        """Determine section hierarchy level from number"""
        if not number:
            return 1
        
        # Count dots/levels in numbering
        if '.' in number:
            return len(number.split('.'))
        
        # Roman numerals are typically level 1
        if re.match(r'^[IVX]+$', number):
            return 1
        
        # Single letters are typically level 1 or 2
        if re.match(r'^[A-Z]$', number):
            return 1
        
        # Default
        return 1
    
    def _calculate_confidence(self, text: str, number: Optional[str], title: str) -> float:
        """Calculate confidence score for section identification"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear numbering
        if number:
            confidence += 0.2
            
            # Extra boost for structured numbering
            if re.match(r'^\d+(\.\d+)*$', number):
                confidence += 0.1
        
        # Boost for title-like formatting
        if title:
            # Capitalized titles
            if title.istitle() or title.isupper():
                confidence += 0.1
            
            # Reasonable title length
            if 5 <= len(title) <= 100:
                confidence += 0.1
        
        # Penalty for very long "titles"
        if len(title) > 200:
            confidence -= 0.2
        
        # Ensure confidence is in valid range
        return min(max(confidence, 0.0), 1.0)
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text"""
        try:
            # Tokenize and POS tag
            tokens = nltk.word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            # Extract noun phrases
            phrases = []
            current_phrase = []
            
            for word, pos in pos_tags:
                if pos.startswith('N') or pos.startswith('J'):  # Nouns and adjectives
                    current_phrase.append(word)
                else:
                    if len(current_phrase) >= 2:
                        phrases.append(' '.join(current_phrase))
                    current_phrase = []
            
            # Add final phrase
            if len(current_phrase) >= 2:
                phrases.append(' '.join(current_phrase))
            
            # Filter and score phrases
            scored_phrases = []
            for phrase in set(phrases):  # Remove duplicates
                if len(phrase.split()) >= 2:  # At least 2 words
                    score = text.lower().count(phrase)  # Simple frequency score
                    scored_phrases.append((phrase, score))
            
            # Sort by score and return top phrases
            scored_phrases.sort(key=lambda x: x[1], reverse=True)
            return [phrase for phrase, _ in scored_phrases[:max_phrases]]
            
        except Exception as e:
            logger.error(f"Error extracting key phrases: {e}")
            return []
    
    def similarity_score(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        try:
            # Simple word overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0