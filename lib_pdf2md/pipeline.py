import fitz
import os
import logging
from .layout_mapper import map_layout
from .noise_filter import filter_noise
from .image_extractor import extract_and_crop
from .structure_parser import parse_semantics
from .markdown_assembler import assemble

logger = logging.getLogger(__name__)

def run_pipeline(pdf_path: str, base_output_dir: str = "./output", output_md_name: str = "output.md"):
    logger.info(f"[*] Starting pipeline for: {pdf_path}")
    image_dir = os.path.join(base_output_dir, "images")
    doc = fitz.open(pdf_path)
    
    logger.info("[1/5] Mapping layout and extracting raw blocks...")
    pages_layout = map_layout(doc)
    
    logger.info("[2/5] Filtering headers, footers, and page numbers...")
    pages_layout = filter_noise(pages_layout)
    
    logger.info("[3/5] Extracting and cropping images...")
    pages_layout = extract_and_crop(doc, pages_layout, image_dir)
    
    logger.info("[4/5] Parsing semantic structures and headings...")
    pages_layout = parse_semantics(pages_layout)
    
    logger.info("[5/5] Assembling final Markdown document...")
    output_path = assemble(pages_layout, base_output_dir, output_md_name)
    
    logger.info(f"[DONE] Pipeline complete. Output saved to: {output_path}")
    return output_path
