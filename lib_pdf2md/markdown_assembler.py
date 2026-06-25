import os
import re
from typing import List, Union
from .models import PageLayout, TextBlock, ImageBlock, SemanticType

def assemble(pages_layout: List[PageLayout], output_dir: str, output_filename: str) -> str:
    """Phase 5: Sort locally per page, stitch inline images, and generate Markdown."""
    os.makedirs(output_dir, exist_ok=True)
    
    def generate_sorted_blocks():
        for page in pages_layout:
            page_blocks: List[Union[TextBlock, ImageBlock]] = []
            page_blocks.extend(page.text_blocks)
            page_blocks.extend(page.image_blocks)
            
            page_blocks.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))
            for block in page_blocks:
                yield block

    current_filename = "00_Frontmatter.md"
    current_lines = []
    file_contents = {}
    previous_block = None

    def safe_filename(name):
        
        name = re.sub(r'[\r\n\t]+', ' ', name)
        
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        
        name = name.replace('*', '').replace('_', '')
        
        
        keywords = (
            r"prologue|prolog|epilogue|epilog|afterword|penutup|foreword|preface|"
            r"pengantar|kata pengantar|prakata|pendahuluan|introduction|appendix|index|glossary|"
            r"chapter\s+\d+|volume\s+\d+|bab\s+\d+|part\s+\d+|bagian\s+\d+|jilid\s+\d+"
        )
        match = re.match(rf"^({keywords})", name, re.IGNORECASE)
        if match:
            name = match.group(0)
        
        name = name.strip()
        
        if len(name) > 100:
            name = name[:100].strip()
            
        return name + ".md"

    for block in generate_sorted_blocks():
        if isinstance(block, TextBlock):
            if block.semantic_type == SemanticType.H1:
                if current_lines:
                    file_contents[current_filename] = current_lines
                current_filename = safe_filename(block.content)
                current_lines = []
                previous_block = None

            text = block.content.strip()
            if not text:
                continue

            if block.semantic_type in (SemanticType.H1, SemanticType.H2, SemanticType.H3):
                
                text = text.replace('**', '').replace('__', '')
                text = re.sub(r'[\r\n]+', ' ', text)
            else:
                orig_count_triple = text.count('***')
                orig_count_double = text.count('**')
                orig_count_single = text.count('*')
                
                
                text = re.sub(r'\*{2,3}\s+\*{2,3}', ' ', text)
                text = re.sub(r'\*{4,}', '', text)
                
                
                text = text.replace('***"*** **', '***" ')
                
                
                
                if text.startswith('***') and text.endswith('***') and orig_count_triple > 2:
                    text = f"***{text.replace('*', '')}***"
                elif text.startswith('**') and text.endswith('**') and orig_count_double > 2:
                    text = f"**{text.replace('*', '')}**"
                elif text.startswith('*') and text.endswith('*') and orig_count_single > 2:
                    
                    if orig_count_single > orig_count_double * 2:
                        text = f"*{text.replace('*', '')}*"

            if block.semantic_type == SemanticType.H1:
                current_lines.append(f"# {text}")
            elif block.semantic_type == SemanticType.H2:
                current_lines.append(f"## {text}")
            elif block.semantic_type == SemanticType.H3:
                current_lines.append(f"### {text}")
            else:
                
                if (current_lines and previous_block and isinstance(previous_block, TextBlock) 
                    and previous_block.semantic_type not in (SemanticType.H1, SemanticType.H2, SemanticType.H3)):
                    
                    prev_text = current_lines[-1].strip()
                    is_split_across_page = (block.page_num != previous_block.page_num)
                    
                    
                    fonts_match = (abs(block.font_size - previous_block.font_size) < 1.0) and (block.is_bold == previous_block.is_bold)
                    
                    
                    
                    is_cut_off = not re.search(r'[.!?~][\”"’\')\]~>]*$', prev_text)
                    
                    if is_split_across_page and is_cut_off and fonts_match:
                        
                        current_lines[-1] = prev_text + " " + text
                        previous_block = block
                        continue
                
                current_lines.append(text)
            previous_block = block
            
        elif isinstance(block, ImageBlock) and block.image_filename:
            
            if previous_block and isinstance(previous_block, ImageBlock) and previous_block.image_filename == block.image_filename:
                continue
                
            current_lines.append(f"![Image]({block.image_filename})")
            previous_block = block
            
    if current_lines:
        file_contents[current_filename] = current_lines

    for fname, lines in file_contents.items():
        
        final_md = "\n\n".join(lines).strip() + "\n"
        output_path = os.path.join(output_dir, fname)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        
    return output_dir
