import re
import statistics
import logging
from typing import List
from .models import PageLayout, SemanticType

logger = logging.getLogger(__name__)



_NUMBERED = r"(?:chapter|bab|part|bagian|volume|jilid)[\s.\-]+[\divxlc]+"

_STANDALONE = r"prologue|prolog|epilogue|epilog|afterword|penutup|foreword|preface|pengantar|kata pengantar|prakata|pendahuluan|introduction|appendix|index|glossary|table of contents|daftar isi|contents|interlude|selingan"

PATTERNS = [
    re.compile(rf"^({_NUMBERED}|{_STANDALONE})", re.IGNORECASE),
    
    re.compile(r"^(chapter|bab|part|bagian|volume|jilid)$", re.IGNORECASE)
]

def parse_semantics(pages_layout: List[PageLayout]) -> List[PageLayout]:
    """Phase 4: Apply heuristics (regex + font size) to tag structural landmarks."""
    
    all_font_sizes = []
    for page in pages_layout:
        for block in page.text_blocks:
            if block.font_size > 0:
                all_font_sizes.append(block.font_size)
                
    median_font_size = statistics.median(all_font_sizes) if all_font_sizes else 12.0

    for page in pages_layout:
        for block in page.text_blocks:
            text = block.content.strip()
            if not text:
                continue

            
            clean_text = text.replace('*', '').strip()
            
            is_larger_text = block.font_size > (median_font_size * 1.15) 
            is_very_large = block.font_size > (median_font_size * 2.0)   
            is_near_top = block.bbox.y0 <= (page.height * 0.5)           
            
            
            matched = any(p.match(clean_text) for p in PATTERNS)
            
            
            is_heading = matched and (is_near_top or is_larger_text or block.is_bold or len(clean_text) < 150)
            
            
            if re.search(r'(?:\.{4,}|·{4,})', clean_text):
                is_heading = False
                is_very_large = False
            
            if is_heading or (is_very_large and len(clean_text) < 100):
                lower_text = clean_text.lower()
                if "prolog" in lower_text or "epilog" in lower_text:
                    matched_type = SemanticType.H1
                elif "chapter" in lower_text or "bab" in lower_text:
                    if re.search(r'\d+\.\d+', clean_text):  
                        matched_type = SemanticType.H2
                    else:
                        matched_type = SemanticType.H1
                else:
                    matched_type = SemanticType.H1
            elif is_near_top and is_larger_text and block.is_bold and len(clean_text) < 100:
                
                matched_type = SemanticType.H2
                is_heading = True
            else:
                matched_type = SemanticType.PARAGRAPH
                is_heading = False
            
            if is_heading:
                block.semantic_type = matched_type
                logger.debug(f"Identified {matched_type.value}: {clean_text}")
            else:
                block.semantic_type = SemanticType.PARAGRAPH
                
    return pages_layout
