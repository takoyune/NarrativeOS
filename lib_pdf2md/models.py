from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class BlockType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

class SemanticType(str, Enum):
    PARAGRAPH = "paragraph"
    H1 = "h1"       
    H2 = "h2"       
    H3 = "h3"       

class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class BaseBlock(BaseModel):
    block_type: BlockType
    bbox: BBox
    page_num: int

class TextBlock(BaseBlock):
    block_type: Literal[BlockType.TEXT] = BlockType.TEXT
    content: str
    semantic_type: SemanticType = SemanticType.PARAGRAPH
    font_size: float = 0.0
    is_bold: bool = False

class ImageBlock(BaseBlock):
    block_type: Literal[BlockType.IMAGE] = BlockType.IMAGE
    image_filename: Optional[str] = None
    image_index: int
    xref: int = 0

class PageLayout(BaseModel):
    page_num: int
    width: float
    height: float
    text_blocks: List[TextBlock] = Field(default_factory=list)
    image_blocks: List[ImageBlock] = Field(default_factory=list)
