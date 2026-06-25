import re
import logging
from collections import Counter
from typing import List
from .models import PageLayout

logger = logging.getLogger(__name__)


PAGE_NUM_PATTERN = re.compile(r'^[-\s]*\d+[-\s]*$|^(?:p\s*a\s*g\s*e|hal(?:aman)?)\s*[|:-]?\s*\d+$', re.IGNORECASE)

def filter_noise(pages_layout: List[PageLayout], margin_threshold: float = 0.10) -> List[PageLayout]:
    """Phase 2: Identify and strip recurring headers and footers mathematically."""
    if not pages_layout:
        return pages_layout

    margin_texts = []
    
    for page in pages_layout:
        top_limit = page.height * margin_threshold
        bottom_limit = page.height * (1 - margin_threshold)
        
        for block in page.text_blocks:
            if block.bbox.y0 <= top_limit or block.bbox.y1 >= bottom_limit:
                normalized = block.content.replace('*', '').lower().strip()
                if normalized:
                    margin_texts.append((page.page_num, normalized))

    
    text_counts = Counter([txt for _, txt in margin_texts])
    total_pages = len(pages_layout)
    
    
    threshold = total_pages * 0.3
    noise_strings = {text for text, count in text_counts.items() if count > threshold}
    
    logger.info(f"Identified {len(noise_strings)} repetitive header/footer text patterns.")
    for t in noise_strings:
        logger.debug(f"Filtered margin text: {t}")

    for page in pages_layout:
        top_limit = page.height * margin_threshold
        bottom_limit = page.height * (1 - margin_threshold)
        
        valid_blocks = []
        for b in page.text_blocks:
            text = b.content
            is_margin = (b.bbox.y0 <= top_limit or b.bbox.y1 >= bottom_limit)
            
            
            clean_text = text.replace('*', '').strip()
            
            if clean_text.lower() in noise_strings:
                continue
            
            
            if not clean_text:
                continue
            
            
            if is_margin and PAGE_NUM_PATTERN.match(clean_text):
                continue
                
            valid_blocks.append(b)
            
        page.text_blocks = valid_blocks
        
    return pages_layout
