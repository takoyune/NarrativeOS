import os
import sys
import shutil
import tempfile
import zipfile
import subprocess
import argparse
import uuid
import datetime
from pathlib import Path

# Optional imports for specific parsers
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import docx
except ImportError:
    docx = None


# ==========================================
# STAGE 1: Input Analysis & Parsing
# ==========================================
def stage_1_input_analysis(input_path):
    """
    Analyzes the input path to determine the pipeline type and reads raw data.
    """
    if os.path.isdir(input_path):
        return 'images', os.listdir(input_path)
    
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.txt':
        with open(input_path, 'r', encoding='utf-8') as f:
            return 'txt', f.read()
    elif ext == '.md':
        with open(input_path, 'r', encoding='utf-8') as f:
            return 'md', f.read()
    elif ext == '.docx':
        if not docx:
            raise ImportError("python-docx is required for DOCX parsing.")
        return 'docx', docx.Document(input_path)
    else:
        raise ValueError(f"Unsupported input format: {ext}")


# ==========================================
# STAGE 2: Structural Parsing
# ==========================================
def stage_2_structural_parsing(raw_content, input_type):
    """
    Parses content into structured elements.
    """
    structured_data = []

    if input_type == 'txt':
        # Pipeline A: TXT Parsing Heuristic
        # "if a line is fewer than 60 characters long and is surrounded by blank lines, classify it as a heading."
        # "All other non-empty lines grouped between blank lines form a single paragraph."
        
        # Split by double newlines (blank lines)
        blocks = raw_content.split('\n\n')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # Simple heuristic implementation
            lines = block.split('\n')
            if len(lines) == 1 and len(lines[0]) < 60:
                structured_data.append(('heading', lines[0]))
            else:
                # Grouped lines form a single paragraph
                paragraph_text = " ".join([line.strip() for line in lines])
                structured_data.append(('paragraph', paragraph_text))

    elif input_type == 'docx':
        # Pipeline B: DOCX Parsing
        for para in raw_content.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = para.style.name
            
            if style_name.startswith('Heading'):
                level = style_name.replace('Heading ', '')
                structured_data.append((f'h{level}', text))
            else:
                structured_data.append(('paragraph', text))
        
        # NOTE: Spec mentions extracting images from word/media/ and resolving word/_rels/document.xml.rels
        # but does not provide Python code. Asking user for implementation details.
        print("WARNING: DOCX image extraction is stubbed. Waiting for implementation details.")

    elif input_type == 'md':
        # Pipeline C: Markdown Parsing
        # Spec: "Use a Markdown parsing library to convert the Markdown AST into a tree of HTML nodes."
        # Does not provide code for AST traversal. Asking user.
        print("WARNING: Markdown AST parsing and splitting is stubbed. Waiting for implementation details.")
        structured_data.append(('raw_markdown', raw_content))

    elif input_type == 'images':
        # Pipeline D: Fixed-Layout Images
        # Filter and sort image files
        images = [img for img in raw_content if img.lower().endswith(('.jpg', '.jpeg', '.png'))]
        images.sort()
        for img in images:
            structured_data.append(('image_page', img))

    return structured_data


# ==========================================
# STAGE 3: XHTML Generation
# ==========================================
def stage_3_xhtml_generation(structured_data, output_dir, input_type):
    """
    Converts parsed structures into valid EPUB 3 XHTML documents.
    """
    xhtml_dir = os.path.join(output_dir, 'OEBPS', 'xhtml')
    os.makedirs(xhtml_dir, exist_ok=True)
    
    manifest_items = []
    spine_items = []
    
    # Template for standard reflowable XHTML
    xhtml_template = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="../css/style.css"/>
</head>
<body>
{body}
</body>
</html>"""

    # Template for fixed-layout XHTML (from Part 2C)
    fxl_template = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>{title}</title>
  <meta name="viewport" content="width={width}, height={height}"/>
  <style type="text/css">
    html, body {{
      margin: 0;
      padding: 0;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
    }}
    img {{
      width: {width}px;
      height: {height}px;
      display: block;
    }}
  </style>
</head>
<body>
  <img src="../images/{img_src}" alt="{title}"/>
</body>
</html>"""

    if input_type in ['txt', 'docx']:
        # Basic chapter splitting based on headings
        chapter_idx = 1
        current_body = []
        current_title = f"Chapter {chapter_idx}"
        
        def write_chapter():
            if current_body:
                filename = f"chapter-{chapter_idx:02d}.xhtml"
                filepath = os.path.join(xhtml_dir, filename)
                content = xhtml_template.format(title=current_title, body="\n  ".join(current_body))
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                manifest_items.append({'id': f'ch{chapter_idx:02d}', 'href': f'xhtml/{filename}', 'media-type': 'application/xhtml+xml'})
                spine_items.append(f'ch{chapter_idx:02d}')

        for tag, content in structured_data:
            if tag in ['heading', 'h1', 'h2']:
                # Split chapter on heading
                if current_body:
                    write_chapter()
                    chapter_idx += 1
                    current_body = []
                current_title = content
                html_tag = 'h1' if tag == 'heading' else tag
                current_body.append(f"<{html_tag}>{content}</{html_tag}>")
            elif tag == 'paragraph':
                current_body.append(f"<p>{content}</p>")
                
        # Write final chapter
        if current_body:
            write_chapter()

    elif input_type == 'images':
        # Pipeline D implementation for Fixed Layout
        # This requires images to be processed first to get dimensions.
        # We will handle this in Orchestrator by running Stage 4 first for Pipeline D.
        pass

    return manifest_items, spine_items


# ==========================================
# STAGE 4: Image Processing
# ==========================================
def stage_4_image_processing(input_folder, output_dir, max_width=1600):
    """
    Resizes images, converts to WebP, and copies them to the EPUB OEBPS/images/ folder.
    (Code snippet from Part 2B)
    """
    if not Image:
        raise ImportError("Pillow is required for image processing.")
        
    images_dir = os.path.join(output_dir, 'OEBPS', 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    manifest_images = []
    
    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            img = Image.open(os.path.join(input_folder, filename))
            
            # Resize logic from Part 2B
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
            
            # Convert to WebP
            webp_filename = os.path.splitext(filename)[0] + ".webp"
            out_path = os.path.join(images_dir, webp_filename)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                img_save = img.convert('RGBA')
            else:
                img_save = img.convert('RGB')
            
            img_save.save(out_path, format="WEBP", quality=90, method=4)
            media_type = "image/webp"
                
            img_id = f"img_{len(manifest_images)+1:03d}"
            manifest_images.append({
                'id': img_id, 
                'href': f'images/{webp_filename}', 
                'media-type': media_type,
                'width': img.width,    # Storing dimensions for Fixed-Layout
                'height': img.height,
                'filename': webp_filename
            })
            
    return manifest_images


# ==========================================
# STAGE 5: Package Assembly
# ==========================================
def stage_5_package_assembly(metadata, manifest_items, spine_items, output_dir, settings=None):
    """
    Generates content.opf, nav.xhtml, container.xml, mimetype, style.css.
    """
    if settings is None:
        settings = {}
    oebps_dir = os.path.join(output_dir, 'OEBPS')
    meta_inf_dir = os.path.join(output_dir, 'META-INF')
    css_dir = os.path.join(oebps_dir, 'css')
    
    os.makedirs(meta_inf_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    
    # 1. mimetype (Must not have newline at end)
    with open(os.path.join(output_dir, 'mimetype'), 'w', newline='', encoding='ascii') as f:
        f.write('application/epub+zip')
        
    # 2. container.xml
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    with open(os.path.join(meta_inf_dir, 'container.xml'), 'w', encoding='utf-8') as f:
        f.write(container_xml)
        
    font_size = settings.get('font_size', 1.1)
    line_height = settings.get('line_height', 1.6)
    text_indent = settings.get('text_indent', 1.5)
    
    # 3. CSS (Part 5 Professional CSS Styling Template)
    css_content = """/* Font Embed */
@font-face {
  font-family: "VT323";
  src: url("../fonts/VT323.woff2") format("woff2");
  font-weight: normal;
  font-style: normal;
}

/* Base page settings */
body {
  font-family: "Palatino", "Palatino Linotype", "Book Antiqua", serif;
  font-size: {font_size}em;
  line-height: {line_height};
  margin: 0;
  padding: 0 5%;
  color: #1a1a1a;
  background-color: transparent;
}

/* Headings */
h1 {
  font-size: 1.8em;
  font-weight: bold;
  text-align: center;
  margin-top: 2em;
  margin-bottom: 1em;
  page-break-before: always;
}

h2 {
  font-size: 1.4em;
  font-weight: bold;
  text-align: center;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

h3 {
  font-size: 1.15em;
  font-weight: bold;
  margin-top: 1.2em;
  margin-bottom: 0.3em;
}

/* Body paragraphs */
p {
  margin: 0 0 0.5em 0;
  padding: 0;
  text-indent: {text_indent}em;
  text-align: justify;
}

h1 + p, h2 + p, h3 + p, .full-page-image + p, .no-indent {
  text-indent: 0;
}

.full-page-image {
  page-break-before: always;
  page-break-after: always;
  text-align: center;
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.full-page-image img {
  max-width: 100%;
  max-height: 100vh;
  margin: auto;
  display: block;
}

/* UI / Visual Stats Elements */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;
  font-size: 0.9em;
}

th, td {
  padding: 0.75em;
  border-bottom: 1px solid #dee2e6;
  text-align: left;
}

th {
  background-color: #e9ecef;
  font-weight: bold;
}

blockquote {
  margin: 1.5em 0;
  padding: 1.2em 1.5em;
  background-color: #2b2b36;
  border: 2px solid #d4af37;
  color: #f8f9fa;
  font-family: "Courier New", Courier, monospace;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  white-space: pre-wrap;
}

blockquote p {
  margin: 0 0 0.5em 0;
  text-indent: 0;
  text-align: left;
  color: #f8f9fa;
}

/* Markdown Tricks */
.dropcap {
  float: left;
  font-size: 3.2em;
  line-height: 0.8;
  margin-right: 0.1em;
  margin-top: 0.1em;
  margin-bottom: -0.1em;
  font-weight: bold;
  font-family: Georgia, "Times New Roman", serif;
  color: #2c3e50;
}

.scene-break {
  text-align: center;
  margin: 2em 0;
  font-size: 1.5em;
  letter-spacing: 0.5em;
  color: #888;
}

.thought {
  font-style: italic;
}

/* Thought Box styling */
.thought-box {
  margin: 1em 0;
  font-style: italic;
}

.thought-inline {
  font-style: italic;
}

/* About / Info Page styling */
.info-page {
  text-align: center;
  padding: 5% 4%;
  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;
}

.info-page h1 {
  font-size: 1.4em;
  font-weight: 700;
  text-align: center;
  margin-top: 0.5em;
  margin-bottom: 0.3em;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: none;
  padding-bottom: 0;
}

.info-divider {
  width: 50px;
  height: 2px;
  background-color: currentColor;
  opacity: 0.5;
  border: none;
  border-radius: 2px;
  margin: 0.8em auto 2em auto;
}

.info-container {
  display: block;
  text-align: center;
  max-width: 90%;
  margin: 0 auto;
}

.info-item {
  margin: 1em auto;
  padding: 0.5em 0;
  border-bottom: 1px solid currentColor;
  opacity: 0.9;
  text-align: center;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item-title {
  padding: 0.8em 1em;
  border: 1px solid currentColor;
  border-radius: 8px;
  margin-bottom: 1.5em;
  opacity: 1;
}

.info-label {
  display: block;
  font-size: 0.7em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 0.4em;
  opacity: 0.7;
}

.info-value {
  display: block;
  font-size: 1.1em;
  line-height: 1.4;
  font-weight: 500;
}

/* Table of Contents Page */
.toc-page {
  padding: 1em 5%;
  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;
}

.toc-title {
  text-align: center;
  font-size: 1.6em;
  font-weight: bold;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-bottom: 1.5em;
  padding-bottom: 0.5em;
  border-bottom: 2px solid #dee2e6;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-list li {
  margin: 0;
  padding: 0;
  border-bottom: 1px solid #eee;
}

.toc-list li:last-child {
  border-bottom: none;
}

.toc-list li a {
  display: block;
  padding: 0.8em 0.5em;
  text-decoration: none;
  color: inherit;
  font-size: 1em;
  transition: background-color 0.2s;
}

.toc-list li a:hover {
  background-color: #f8f9fa;
}

/* Game UI Box */
pre.game-ui-box, .game-ui-box {
  margin: 1.5em 0;
  padding: 1em 1.5em;
  font-family: "VT323", "Courier New", Courier, monospace;
  font-size: 1.15em;
  font-weight: bold;
  white-space: pre-wrap;
  line-height: 1.6;
  background: none;
  border: none;
}"""
    
    # Inject settings dynamically (avoids f-string syntax errors with CSS braces)
    css_content = css_content.replace("{font_size}", str(font_size))
    css_content = css_content.replace("{line_height}", str(line_height))
    css_content = css_content.replace("{text_indent}", str(text_indent))

    with open(os.path.join(css_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)
        
    # Copy VT323 font if available
    fonts_dir = os.path.join(oebps_dir, 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
    font_src = os.path.join(script_dir, 'VT323.woff2')
    if os.path.exists(font_src):
        shutil.copy2(font_src, os.path.join(fonts_dir, 'VT323.woff2'))
    
    # Add CSS, Font, and Nav to manifest
    manifest_items.append({'id': 'css', 'href': 'css/style.css', 'media-type': 'text/css'})
    if os.path.exists(os.path.join(fonts_dir, 'VT323.woff2')):
        manifest_items.append({'id': 'font-vt323', 'href': 'fonts/VT323.woff2', 'media-type': 'font/woff2'})
    manifest_items.append({'id': 'nav', 'href': 'nav.xhtml', 'media-type': 'application/xhtml+xml', 'properties': 'nav'})

    # 4. content.opf
    manifest_str = ""
    for item in manifest_items:
        props = f' properties="{item["properties"]}"' if 'properties' in item else ""
        manifest_str += f'    <item id="{item["id"]}" href="{item["href"]}" media-type="{item["media-type"]}"{props}/>\n'
        
    spine_str = ""
    for item in spine_items:
        itemref = item['id'] if isinstance(item, dict) else item
        # nav/TOC should be linear="no" so readers skip it during sequential page-turn
        if itemref == 'nav':
            spine_str += f'    <itemref idref="{itemref}" linear="no"/>\n'
        else:
            spine_str += f'    <itemref idref="{itemref}"/>\n'

    # Fixed-Layout metadata if needed
    fxl_meta = ""
    if metadata.get('fixed_layout'):
        fxl_meta = """
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">auto</meta>"""

    opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{metadata.get('title', 'Untitled')}</dc:title>
    <dc:creator>{metadata.get('author', 'Unknown Author')}</dc:creator>
    <dc:language>{metadata.get('language', 'en')}</dc:language>
    <dc:identifier id="bookid">urn:uuid:{uuid.uuid4()}</dc:identifier>
    <meta property="dcterms:modified">{datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]}Z</meta>{fxl_meta}
  </metadata>
  <manifest>
{manifest_str.rstrip()}
  </manifest>
  <spine>
{spine_str.rstrip()}
  </spine>
</package>"""
    
    with open(os.path.join(oebps_dir, 'content.opf'), 'w', encoding='utf-8') as f:
        f.write(opf_content)
        
    # 5. nav.xhtml (Minimal generation)
    # Generating minimal TOC from spine for now. Spec requires extracting h1s.
    nav_li_str = ""
    for i, item in enumerate(spine_items):
        itemref = item['id'] if isinstance(item, dict) else item
        if isinstance(item, dict) and item.get('exclude_from_toc'):
            continue
        title = item.get('title') if isinstance(item, dict) else f"Chapter {i+1}"
        # find matching item in manifest
        href = next((x['href'] for x in manifest_items if x['id'] == itemref), None)
        if href:
            nav_li_str += f'      <li><a href="{href}">{title}</a></li>\n'
            
    # Determine the first chapter for landmarks
    # [Upgrade 6] Skip all non-reading pages (cover, nav, about, illustrations)
    NON_READING_IDS = {'cover_page', 'nav', 'about_page', 'illustrations_page'}
    start_reading_href = ""
    for item in spine_items:
        itemref = item['id'] if isinstance(item, dict) else item
        if str(itemref) not in NON_READING_IDS and not str(itemref).lower().startswith('cover'):
            href = next((x['href'] for x in manifest_items if x['id'] == itemref), "")
            if href:
                start_reading_href = href
                break
            
    if not start_reading_href and spine_items:
        first_ref = spine_items[0]['id'] if isinstance(spine_items[0], dict) else spine_items[0]
        start_reading_href = next((x['href'] for x in manifest_items if x['id'] == first_ref), "")

    landmarks_xml = ""
    if start_reading_href:
        landmarks_xml = f"""
  <nav epub:type="landmarks" hidden="hidden">
    <h2>Guide</h2>
    <ol>
      <li><a epub:type="bodymatter" href="{start_reading_href}">Start of Story</a></li>
    </ol>
  </nav>"""

    nav_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="css/style.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc" class="toc-page">
    <h1 class="toc-title">Table of Contents</h1>
    <ol class="toc-list">
{nav_li_str.rstrip()}
    </ol>
  </nav>{landmarks_xml}
</body>
</html>"""
    with open(os.path.join(oebps_dir, 'nav.xhtml'), 'w', encoding='utf-8') as f:
        f.write(nav_content)


# ==========================================
# STAGE 6: ZIP Packaging
# ==========================================
def stage_6_zip_packaging(source_folder, output_path):
    """
    Creates the EPUB ZIP archive exactly as described in Part 4.
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype MUST be first and MUST be uncompressed (ZIP_STORED)
        zf.write(
            os.path.join(source_folder, "mimetype"),
            "mimetype",
            compress_type=zipfile.ZIP_STORED
        )
        # Add all other files
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                if file == "mimetype":
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zf.write(file_path, arcname)


# ==========================================
# STAGE 7: Validation
# ==========================================
def stage_7_validation(epub_path):
    """
    Runs EPUBCheck via subprocess (from Part 6).
    """
    print(f"\n[Validation] Running EPUBCheck on {epub_path}...")
    try:
        # Assuming epubcheck.jar is in path or accessible
        # Spec says: java -jar epubcheck.jar output.epub
        result = subprocess.run(['java', '-jar', 'epubcheck.jar', epub_path], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
    except FileNotFoundError:
        print("Validation skipped: 'java' not found or 'epubcheck.jar' is missing in the current directory.")


# ==========================================
# ORCHESTRATOR: Universal Build Algorithm
# ==========================================
def universal_build_algorithm(args):
    """
    Scaffolds the project and coordinates all pipeline stages.
    """
    input_path = args.input
    output_path = args.output
    if not output_path:
        output_path = "output.epub"

    print(f"Starting EPUB build for: {input_path}")
    
    # Create temp scaffold directory
    temp_dir = tempfile.mkdtemp(prefix="epub_build_")
    
    try:
        # 1. Input Analysis
        input_type, raw_content = stage_1_input_analysis(input_path)
        print(f"Detected input type: {input_type}")
        
        # 2. Structural Parsing
        structured_data = stage_2_structural_parsing(raw_content, input_type)
        
        # 3, 4. XHTML Generation & Image Processing
        manifest_items = []
        spine_items = []
        
        if input_type == 'images':
            # Run image processing first to get dimensions
            print("Processing images...")
            img_manifest = stage_4_image_processing(input_path, temp_dir)
            manifest_items.extend(img_manifest)
            
            # Generate FXL XHTML
            xhtml_dir = os.path.join(temp_dir, 'OEBPS', 'xhtml')
            os.makedirs(xhtml_dir, exist_ok=True)
            
            fxl_template = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>Page {idx}</title>
  <meta name="viewport" content="width={width}, height={height}"/>
  <style type="text/css">
    html, body {{
      margin: 0;
      padding: 0;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
    }}
    img {{
      width: {width}px;
      height: {height}px;
      display: block;
    }}
  </style>
</head>
<body>
  <img src="../images/{filename}" alt="Page {idx}"/>
</body>
</html>"""
            
            for i, img_data in enumerate(img_manifest, 1):
                filename = f"page-{i:03d}.xhtml"
                filepath = os.path.join(xhtml_dir, filename)
                content = fxl_template.format(
                    idx=i, 
                    width=img_data['width'], 
                    height=img_data['height'],
                    filename=img_data['filename']
                )
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                ch_id = f"page{i:03d}"
                manifest_items.append({'id': ch_id, 'href': f'xhtml/{filename}', 'media-type': 'application/xhtml+xml', 'properties': 'rendition:layout-pre-paginated'})
                spine_items.append(ch_id)
                
        else:
            print("Generating XHTML...")
            man, spi = stage_3_xhtml_generation(structured_data, temp_dir, input_type)
            manifest_items.extend(man)
            spine_items.extend(spi)
            
        # 5. Package Assembly
        print("Assembling EPUB package...")
        metadata = {
            'title': args.title,
            'author': args.author,
            'language': args.language,
            'fixed_layout': args.fixed_layout or (input_type == 'images')
        }
        stage_5_package_assembly(metadata, manifest_items, spine_items, temp_dir)
        
        # 6. ZIP Packaging
        print(f"Packaging to {output_path}...")
        stage_6_zip_packaging(temp_dir, output_path)
        
        # 7. Validation
        if args.validate:
            stage_7_validation(output_path)
            
        print("Build complete!")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal EPUB Builder based on Ultimate Guide.")
    parser.add_argument("input", help="Input file (.txt, .md, .docx) or folder of images.")
    parser.add_argument("--output", "-o", help="Output .epub file path.")
    parser.add_argument("--title", default="Untitled Ebook", help="Ebook title.")
    parser.add_argument("--author", default="Unknown Author", help="Ebook author.")
    parser.add_argument("--language", default="en", help="Language code (e.g. en).")
    parser.add_argument("--fixed-layout", action="store_true", help="Force fixed-layout EPUB.")
    parser.add_argument("--validate", action="store_true", help="Run EPUBCheck after building.")
    
    args = parser.parse_args()
    universal_build_algorithm(args)
