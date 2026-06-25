import fitz  
import re
from typing import List
from .models import PageLayout, TextBlock, ImageBlock, BBox

def map_layout(doc: fitz.Document) -> List[PageLayout]:
    """Phase 1: Extract raw blocks, map coordinates, and extract font properties."""
    pages_layout = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        width, height = page.rect.width, page.rect.height
        
        text_blocks = _extract_text_blocks(page, page_num)
        image_blocks = _extract_image_blocks(page, page_num)
        
        pages_layout.append(PageLayout(
            page_num=page_num,
            width=width,
            height=height,
            text_blocks=text_blocks,
            image_blocks=image_blocks
        ))
    return pages_layout

def _extract_text_blocks(page: fitz.Page, page_num: int) -> List[TextBlock]:
    blocks = []
    
    page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for blk in page_dict["blocks"]:
        if blk["type"] == 0:  
            max_font_size = 0.0
            is_bold = False
            
            block_right_edge = blk["bbox"][2]
            block_left_edge = blk["bbox"][0]
            block_width = block_right_edge - block_left_edge
            
            
            
            gap_tolerance = min(block_width * 0.35, 150)
            
            lines_info = []
            
            for line in blk["lines"]:
                line_text = ""
                line_max_font = 0.0
                for span in line["spans"]:
                    span_text = span["text"].replace('\u2026', '...')
                    if span["size"] > max_font_size:
                        max_font_size = span["size"]
                    if span["size"] > line_max_font:
                        line_max_font = span["size"]
                        
                    span_is_bold = "bold" in span["font"].lower() or (span.get("flags", 0) & 16)
                    span_is_italic = "italic" in span["font"].lower() or (span.get("flags", 0) & 2)
                    
                    if span_is_bold:
                        is_bold = True
                        
                    leading_space = " " if span_text.startswith(" ") else ""
                    trailing_space = " " if span_text.endswith(" ") else ""
                    stripped_text = span_text.strip()
                    
                    if stripped_text:
                        if span_is_bold and span_is_italic:
                            span_text = f"{leading_space}***{stripped_text}***{trailing_space}"
                        elif span_is_bold:
                            span_text = f"{leading_space}**{stripped_text}**{trailing_space}"
                        elif span_is_italic:
                            span_text = f"{leading_space}*{stripped_text}*{trailing_space}"
                            
                    line_text += span_text
                
                line_text = line_text.strip()
                
                line_width = line["bbox"][2] - line["bbox"][0]
                
                
                hit_margin = line_width >= (block_width - gap_tolerance)
                lines_info.append({"text": line_text, "hit_margin": hit_margin, "font_size": line_max_font})
            
            
            new_lines = []
            
            for i, l_info in enumerate(lines_info):
                line = l_info["text"]
                if not line:
                    if new_lines and new_lines[-1] != "":
                        new_lines.append("")
                    continue
                    
                if not new_lines:
                    new_lines.append(line)
                else:
                    prev = new_lines[-1]
                    if prev == "":
                        new_lines.append(line)
                    else:
                        is_hard_break = False
                        
                        
                        if not lines_info[i-1]["hit_margin"]:
                            is_hard_break = True
                            
                        
                        
                        if re.search(r'[.!?][\”"’\')\]~>]*$', prev):
                            is_hard_break = True
                            
                        
                        if re.match(r'^[\”"’\'\-•*]|^[0-9]+[.)]', line):
                            is_hard_break = True
                            
                        
                        
                        if re.search(r',[\”"’\')\]~>\s]*$', prev):
                            is_hard_break = False
                            
                        
                        
                        if re.match(r'^[\”"’\'\-•*]*[a-z]', line):
                            is_hard_break = False
                            
                        
                        
                        
                        if re.match(r'^[”’)\]]', line) or re.match(r'^[\”"’\')\]~>.!?]+$', line):
                            is_hard_break = False

                        
                        
                        
                        clean_prev = re.sub(r'[*_]', '', prev).strip()
                        if len(clean_prev) > 25 and not re.search(r'[.,:;!?-][\”"’\')\]~>]*$', clean_prev):
                            is_hard_break = False
                            
                        
                        
                        if abs(l_info["font_size"] - lines_info[i-1]["font_size"]) > 2.0:
                            is_hard_break = True
                            
                        if is_hard_break:
                            new_lines.append("")
                            new_lines.append(line)
                        else:
                            
                            if re.match(r'^[\”"’\')\]~>.!?]+$', line):
                                new_lines[-1] = new_lines[-1] + line
                            else:
                                new_lines[-1] = new_lines[-1] + " " + line
            
            block_text = "\n".join(new_lines).strip()
            
            if block_text:
                blocks.append(TextBlock(
                    bbox=BBox(x0=blk["bbox"][0], y0=blk["bbox"][1], x1=blk["bbox"][2], y1=blk["bbox"][3]),
                    page_num=page_num,
                    content=block_text,
                    font_size=max_font_size,
                    is_bold=is_bold
                ))
    
    merged_blocks = []
    for block in blocks:
        if not merged_blocks:
            merged_blocks.append(block)
            continue
            
        prev_block = merged_blocks[-1]
        
        font_size_match = abs(block.font_size - prev_block.font_size) < 0.5
        weight_match = block.is_bold == prev_block.is_bold
        vertical_gap = block.bbox.y0 - prev_block.bbox.y1
        gap_match = -10 <= vertical_gap < (block.font_size * 1.5)
        
        prev_clean = re.sub(r'[*_]', '', prev_block.content).strip()
        ends_with_sentence_end = re.search(r'[.!?][\”"’\')\]~>]*$', prev_clean)
        
        if font_size_match and weight_match and gap_match and not ends_with_sentence_end:
            
            prev_block.content += " " + block.content
            prev_block.bbox = BBox(
                x0=min(prev_block.bbox.x0, block.bbox.x0),
                y0=min(prev_block.bbox.y0, block.bbox.y0),
                x1=max(prev_block.bbox.x1, block.bbox.x1),
                y1=max(prev_block.bbox.y1, block.bbox.y1)
            )
        else:
            merged_blocks.append(block)
            
    return merged_blocks

def _extract_image_blocks(page: fitz.Page, page_num: int) -> List[ImageBlock]:
    blocks = []
    img_info = page.get_image_info(xrefs=True)
    for idx, img in enumerate(img_info):
        x0, y0, x1, y1 = img["bbox"]
        width = x1 - x0
        height = y1 - y0
        
        if width < 100 or height < 100:
            continue
        blocks.append(ImageBlock(
            bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
            page_num=page_num,
            image_index=idx,
            xref=img.get("xref", 0)
        ))
    return blocks
