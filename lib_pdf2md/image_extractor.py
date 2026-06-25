import fitz
import os
import logging
from typing import List
from .models import PageLayout

logger = logging.getLogger(__name__)

def extract_and_crop(doc: fitz.Document, pages_layout: List[PageLayout], output_dir: str) -> List[PageLayout]:
    """Phase 3: Extract images natively using xref, falling back to pixmap if needed."""
    os.makedirs(output_dir, exist_ok=True)
    global_image_counter = 0
    global_junk_counter = 0
    extracted_xrefs = {}  
    
    for page_layout in pages_layout:
        page = doc[page_layout.page_num]
        
        valid_image_blocks = []
        for img_block in page_layout.image_blocks:
            if img_block.xref and img_block.xref in extracted_xrefs:
                img_block.image_filename = extracted_xrefs[img_block.xref]
                valid_image_blocks.append(img_block)
                continue
                
            global_image_counter += 1
            
            ext = "png"
            image_bytes = None
            
            if img_block.xref:
                try:
                    base_image = doc.extract_image(img_block.xref)
                    if base_image:
                        image_bytes = base_image["image"]
                        ext = base_image["ext"]
                except Exception:
                    pass
            
            filename = f"{global_image_counter}.{ext}"
            filepath = os.path.join(output_dir, filename)
            
            if image_bytes:
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            else:
                
                clip_rect = fitz.Rect(
                    img_block.bbox.x0, 
                    img_block.bbox.y0, 
                    img_block.bbox.x1, 
                    img_block.bbox.y1
                )
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
                pix.save(filepath)
            
            
            if os.path.getsize(filepath) < 20480:
                global_junk_counter += 1
                junk_filename = f"junk_{global_junk_counter}.{ext}"
                junk_filepath = os.path.join(output_dir, junk_filename)
                os.replace(filepath, junk_filepath)
                logger.debug(f"Filtered out junk image {junk_filename} (< 20KB)")
                global_image_counter -= 1  
                continue
            
            
            img_block.image_filename = f"images/{filename}"
            if img_block.xref:
                extracted_xrefs[img_block.xref] = img_block.image_filename
            valid_image_blocks.append(img_block)
            logger.debug(f"Extracted valid image {filename}")
            
        page_layout.image_blocks = valid_image_blocks
            
    return pages_layout
