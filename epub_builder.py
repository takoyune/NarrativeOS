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
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import docx
except ImportError:
    docx = None

def stage_1_input_analysis(input_path):
    """
    Analyzes the input path to determine the pipeline type and reads raw data.
    """
    if os.path.isdir(input_path):
        return ('images', os.listdir(input_path))
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.txt':
        with open(input_path, 'r', encoding='utf-8') as f:
            return ('txt', f.read())
    elif ext == '.md':
        with open(input_path, 'r', encoding='utf-8') as f:
            return ('md', f.read())
    elif ext == '.docx':
        if not docx:
            raise ImportError('python-docx is required for DOCX parsing.')
        return ('docx', docx.Document(input_path))
    else:
        raise ValueError(f'Unsupported input format: {ext}')

def stage_2_structural_parsing(raw_content, input_type):
    """
    Parses content into structured elements.
    """
    structured_data = []
    if input_type == 'txt':
        blocks = raw_content.split('\n\n')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.split('\n')
            if len(lines) == 1 and len(lines[0]) < 60:
                structured_data.append(('heading', lines[0]))
            else:
                paragraph_text = ' '.join([line.strip() for line in lines])
                structured_data.append(('paragraph', paragraph_text))
    elif input_type == 'docx':
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
        print('WARNING: DOCX image extraction is stubbed. Waiting for implementation details.')
    elif input_type == 'md':
        print('WARNING: Markdown AST parsing and splitting is stubbed. Waiting for implementation details.')
        structured_data.append(('raw_markdown', raw_content))
    elif input_type == 'images':
        images = [img for img in raw_content if img.lower().endswith(('.jpg', '.jpeg', '.png'))]
        images.sort()
        for img in images:
            structured_data.append(('image_page', img))
    return structured_data

def stage_3_xhtml_generation(structured_data, output_dir, input_type):
    """
    Converts parsed structures into valid EPUB 3 XHTML documents.
    """
    xhtml_dir = os.path.join(output_dir, 'OEBPS', 'xhtml')
    os.makedirs(xhtml_dir, exist_ok=True)
    manifest_items = []
    spine_items = []
    xhtml_template = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n<head>\n  <title>{title}</title>\n  <link rel="stylesheet" type="text/css" href="../css/style.css"/>\n</head>\n<body>\n{body}\n</body>\n</html>'
    fxl_template = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n<head>\n  <title>{title}</title>\n  <meta name="viewport" content="width={width}, height={height}"/>\n  <style type="text/css">\n    html, body {{\n      margin: 0;\n      padding: 0;\n      width: {width}px;\n      height: {height}px;\n      overflow: hidden;\n    }}\n    img {{\n      width: {width}px;\n      height: {height}px;\n      display: block;\n    }}\n  </style>\n</head>\n<body>\n  <img src="../images/{img_src}" alt="{title}"/>\n</body>\n</html>'
    if input_type in ['txt', 'docx']:
        chapter_idx = 1
        current_body = []
        current_title = f'Chapter {chapter_idx}'

        def write_chapter():
            if current_body:
                filename = f'chapter-{chapter_idx:02d}.xhtml'
                filepath = os.path.join(xhtml_dir, filename)
                content = xhtml_template.format(title=current_title, body='\n  '.join(current_body))
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                manifest_items.append({'id': f'ch{chapter_idx:02d}', 'href': f'xhtml/{filename}', 'media-type': 'application/xhtml+xml'})
                spine_items.append(f'ch{chapter_idx:02d}')
        for tag, content in structured_data:
            if tag in ['heading', 'h1', 'h2']:
                if current_body:
                    write_chapter()
                    chapter_idx += 1
                    current_body = []
                current_title = content
                html_tag = 'h1' if tag == 'heading' else tag
                current_body.append(f'<{html_tag}>{content}</{html_tag}>')
            elif tag == 'paragraph':
                current_body.append(f'<p>{content}</p>')
        if current_body:
            write_chapter()
    elif input_type == 'images':
        pass
    return (manifest_items, spine_items)

def stage_4_image_processing(input_folder, output_dir, max_width=1600):
    """
    Resizes images, converts to WebP, and copies them to the EPUB OEBPS/images/ folder.
    (Code snippet from Part 2B)
    """
    if not Image:
        raise ImportError('Pillow is required for image processing.')
    images_dir = os.path.join(output_dir, 'OEBPS', 'images')
    os.makedirs(images_dir, exist_ok=True)
    manifest_images = []
    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            img = Image.open(os.path.join(input_folder, filename))
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
            webp_filename = os.path.splitext(filename)[0] + '.webp'
            out_path = os.path.join(images_dir, webp_filename)
            if img.mode in ('RGBA', 'LA', 'P'):
                img_save = img.convert('RGBA')
            else:
                img_save = img.convert('RGB')
            img_save.save(out_path, format='WEBP', quality=90, method=4)
            media_type = 'image/webp'
            img_id = f'img_{len(manifest_images) + 1:03d}'
            manifest_images.append({'id': img_id, 'href': f'images/{webp_filename}', 'media-type': media_type, 'width': img.width, 'height': img.height, 'filename': webp_filename})
    return manifest_images

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
    with open(os.path.join(output_dir, 'mimetype'), 'w', newline='', encoding='ascii') as f:
        f.write('application/epub+zip')
    container_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n  <rootfiles>\n    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n  </rootfiles>\n</container>'
    with open(os.path.join(meta_inf_dir, 'container.xml'), 'w', encoding='utf-8') as f:
        f.write(container_xml)
    font_size = settings.get('font_size', 1.1)
    line_height = settings.get('line_height', 1.6)
    text_indent = settings.get('text_indent', 1.5)
    css_content = '/* Font Embed */\n@font-face {\n  font-family: "VT323";\n  src: url("../fonts/VT323.woff2") format("woff2");\n  font-weight: normal;\n  font-style: normal;\n}\n\n/* Base page settings */\nbody {\n  font-family: "Palatino", "Palatino Linotype", "Book Antiqua", serif;\n  font-size: {font_size}em;\n  line-height: {line_height};\n  margin: 0;\n  padding: 0 5%;\n  color: #1a1a1a;\n  background-color: transparent;\n}\n\n/* Headings */\nh1 {\n  font-size: 1.8em;\n  font-weight: bold;\n  text-align: center;\n  margin-top: 2em;\n  margin-bottom: 1em;\n  page-break-before: always;\n}\n\nh2 {\n  font-size: 1.4em;\n  font-weight: bold;\n  text-align: center;\n  margin-top: 1.5em;\n  margin-bottom: 0.5em;\n}\n\nh3 {\n  font-size: 1.15em;\n  font-weight: bold;\n  margin-top: 1.2em;\n  margin-bottom: 0.3em;\n}\n\n/* Body paragraphs */\np {\n  margin: 0 0 0.5em 0;\n  padding: 0;\n  text-indent: {text_indent}em;\n  text-align: justify;\n}\n\nh1 + p, h2 + p, h3 + p, .full-page-image + p, .no-indent {\n  text-indent: 0;\n}\n\n.full-page-image {\n  page-break-before: always;\n  page-break-after: always;\n  text-align: center;\n  margin: 0;\n  padding: 0;\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  height: 100vh;\n}\n\n.full-page-image img {\n  max-width: 100%;\n  max-height: 100vh;\n  margin: auto;\n  display: block;\n}\n\n/* UI / Visual Stats Elements */\ntable {\n  width: 100%;\n  border-collapse: collapse;\n  margin: 1.5em 0;\n  background-color: #f8f9fa;\n  border: 1px solid #dee2e6;\n  border-radius: 4px;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n  font-size: 0.9em;\n}\n\nth, td {\n  padding: 0.75em;\n  border-bottom: 1px solid #dee2e6;\n  text-align: left;\n}\n\nth {\n  background-color: #e9ecef;\n  font-weight: bold;\n}\n\nblockquote {\n  margin: 1.5em 0;\n  padding: 1.2em 1.5em;\n  background-color: #2b2b36;\n  border: 2px solid #d4af37;\n  color: #f8f9fa;\n  font-family: "Courier New", Courier, monospace;\n  border-radius: 8px;\n  box-shadow: 0 4px 8px rgba(0,0,0,0.3);\n  white-space: pre-wrap;\n}\n\nblockquote p {\n  margin: 0 0 0.5em 0;\n  text-indent: 0;\n  text-align: left;\n  color: #f8f9fa;\n}\n\n/* Markdown Tricks */\n.dropcap {\n  float: left;\n  font-size: 3.2em;\n  line-height: 0.8;\n  margin-right: 0.1em;\n  margin-top: 0.1em;\n  margin-bottom: -0.1em;\n  font-weight: bold;\n  font-family: Georgia, "Times New Roman", serif;\n  color: #2c3e50;\n}\n\n.scene-break {\n  text-align: center;\n  margin: 2em 0;\n  font-size: 1.5em;\n  letter-spacing: 0.5em;\n  color: #888;\n}\n\n.thought {\n  font-style: italic;\n}\n\n/* Thought Box styling */\n.thought-box {\n  margin: 1em 0;\n  font-style: italic;\n}\n\n.thought-inline {\n  font-style: italic;\n}\n\n/* About / Info Page styling */\n.info-page {\n  text-align: center;\n  padding: 5% 4%;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n}\n\n.info-page h1 {\n  font-size: 1.4em;\n  font-weight: 700;\n  text-align: center;\n  margin-top: 0.5em;\n  margin-bottom: 0.3em;\n  letter-spacing: 0.12em;\n  text-transform: uppercase;\n  border: none;\n  padding-bottom: 0;\n}\n\n.info-divider {\n  width: 50px;\n  height: 2px;\n  background-color: currentColor;\n  opacity: 0.5;\n  border: none;\n  border-radius: 2px;\n  margin: 0.8em auto 2em auto;\n}\n\n.info-container {\n  display: block;\n  text-align: center;\n  max-width: 90%;\n  margin: 0 auto;\n}\n\n.info-item {\n  margin: 1em auto;\n  padding: 0.5em 0;\n  border-bottom: 1px solid currentColor;\n  opacity: 0.9;\n  text-align: center;\n}\n\n.info-item:last-child {\n  border-bottom: none;\n}\n\n.info-item-title {\n  padding: 0.8em 1em;\n  border: 1px solid currentColor;\n  border-radius: 8px;\n  margin-bottom: 1.5em;\n  opacity: 1;\n}\n\n.info-label {\n  display: block;\n  font-size: 0.7em;\n  font-weight: 600;\n  text-transform: uppercase;\n  letter-spacing: 0.15em;\n  margin-bottom: 0.4em;\n  opacity: 0.7;\n}\n\n.info-value {\n  display: block;\n  font-size: 1.1em;\n  line-height: 1.4;\n  font-weight: 500;\n}\n\n/* TakoYune Watermark */\n.info-watermark {\n  margin-top: 3em;\n  text-align: center;\n  opacity: 0.18;\n}\n\n.watermark-link {\n  font-size: 0.65em;\n  font-weight: 600;\n  letter-spacing: 0.25em;\n  text-transform: uppercase;\n  text-decoration: none;\n  color: inherit;\n  border-bottom: 1px solid currentColor;\n  padding-bottom: 1px;\n}\n\n.watermark-link:hover {\n  opacity: 0.5;\n}\n\n\n.toc-page {\n  padding: 1em 5%;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n}\n\n.toc-title {\n  text-align: center;\n  font-size: 1.6em;\n  font-weight: bold;\n  letter-spacing: 0.15em;\n  text-transform: uppercase;\n  margin-bottom: 1.5em;\n  padding-bottom: 0.5em;\n  border-bottom: 2px solid #dee2e6;\n}\n\n.toc-list {\n  list-style: none;\n  padding: 0;\n  margin: 0;\n}\n\n.toc-list li {\n  margin: 0;\n  padding: 0;\n  border-bottom: 1px solid #eee;\n}\n\n.toc-list li:last-child {\n  border-bottom: none;\n}\n\n.toc-list li a {\n  display: block;\n  padding: 0.8em 0.5em;\n  text-decoration: none;\n  color: inherit;\n  font-size: 1em;\n  transition: background-color 0.2s;\n}\n\n.toc-list li a:hover {\n  background-color: #f8f9fa;\n}\n\n/* Game UI Box */\npre.game-ui-box, .game-ui-box {\n  margin: 1.5em 0;\n  padding: 1em 1.5em;\n  font-family: "VT323", "Courier New", Courier, monospace;\n  font-size: 1.15em;\n  font-weight: bold;\n  white-space: pre-wrap;\n  line-height: 1.6;\n  background: none;\n  border: none;\n}'
    css_content = css_content.replace('{font_size}', str(font_size))
    css_content = css_content.replace('{line_height}', str(line_height))
    css_content = css_content.replace('{text_indent}', str(text_indent))
    with open(os.path.join(css_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)
    fonts_dir = os.path.join(oebps_dir, 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
    font_src = os.path.join(script_dir, 'VT323.woff2')
    if os.path.exists(font_src):
        shutil.copy2(font_src, os.path.join(fonts_dir, 'VT323.woff2'))
    manifest_items.append({'id': 'css', 'href': 'css/style.css', 'media-type': 'text/css'})
    if os.path.exists(os.path.join(fonts_dir, 'VT323.woff2')):
        manifest_items.append({'id': 'font-vt323', 'href': 'fonts/VT323.woff2', 'media-type': 'font/woff2'})
    manifest_items.append({'id': 'nav', 'href': 'nav.xhtml', 'media-type': 'application/xhtml+xml', 'properties': 'nav'})
    manifest_str = ''
    for item in manifest_items:
        props = f''' properties="{item['properties']}"''' if 'properties' in item else ''
        manifest_str += f'''    <item id="{item['id']}" href="{item['href']}" media-type="{item['media-type']}"{props}/>\n'''
    spine_str = ''
    for item in spine_items:
        itemref = item['id'] if isinstance(item, dict) else item
        if itemref == 'nav':
            spine_str += f'    <itemref idref="{itemref}" linear="no"/>\n'
        else:
            spine_str += f'    <itemref idref="{itemref}"/>\n'
    fxl_meta = ''
    if metadata.get('fixed_layout'):
        fxl_meta = '\n    <meta property="rendition:layout">pre-paginated</meta>\n    <meta property="rendition:orientation">auto</meta>\n    <meta property="rendition:spread">auto</meta>'
    opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n    <dc:title>{metadata.get('title', 'Untitled')}</dc:title>\n    <dc:creator>{metadata.get('author', 'Unknown Author')}</dc:creator>\n    <dc:language>{metadata.get('language', 'en')}</dc:language>\n    <dc:identifier id="bookid">urn:uuid:{uuid.uuid4()}</dc:identifier>\n    <meta property="dcterms:modified">{datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]}Z</meta>{fxl_meta}\n  </metadata>\n  <manifest>\n{manifest_str.rstrip()}\n  </manifest>\n  <spine>\n{spine_str.rstrip()}\n  </spine>\n</package>"""
    with open(os.path.join(oebps_dir, 'content.opf'), 'w', encoding='utf-8') as f:
        f.write(opf_content)
    nav_li_str = ''
    for i, item in enumerate(spine_items):
        itemref = item['id'] if isinstance(item, dict) else item
        if isinstance(item, dict) and item.get('exclude_from_toc'):
            continue
        title = item.get('title') if isinstance(item, dict) else f'Chapter {i + 1}'
        href = next((x['href'] for x in manifest_items if x['id'] == itemref), None)
        if href:
            nav_li_str += f'      <li><a href="{href}">{title}</a></li>\n'
    NON_READING_IDS = {'cover_page', 'nav', 'about_page', 'illustrations_page'}
    start_reading_href = ''
    for item in spine_items:
        itemref = item['id'] if isinstance(item, dict) else item
        if str(itemref) not in NON_READING_IDS and (not str(itemref).lower().startswith('cover')):
            href = next((x['href'] for x in manifest_items if x['id'] == itemref), '')
            if href:
                start_reading_href = href
                break
    if not start_reading_href and spine_items:
        first_ref = spine_items[0]['id'] if isinstance(spine_items[0], dict) else spine_items[0]
        start_reading_href = next((x['href'] for x in manifest_items if x['id'] == first_ref), '')
    landmarks_xml = ''
    if start_reading_href:
        landmarks_xml = f'\n  <nav epub:type="landmarks" hidden="hidden">\n    <h2>Guide</h2>\n    <ol>\n      <li><a epub:type="bodymatter" href="{start_reading_href}">Start of Story</a></li>\n    </ol>\n  </nav>'
    nav_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">\n<head>\n  <title>Table of Contents</title>\n  <link rel="stylesheet" type="text/css" href="css/style.css"/>\n</head>\n<body>\n  <nav epub:type="toc" id="toc" class="toc-page">\n    <h1 class="toc-title">Table of Contents</h1>\n    <ol class="toc-list">\n{nav_li_str.rstrip()}\n    </ol>\n  </nav>{landmarks_xml}\n</body>\n</html>'
    with open(os.path.join(oebps_dir, 'nav.xhtml'), 'w', encoding='utf-8') as f:
        f.write(nav_content)

def stage_6_zip_packaging(source_folder, output_path):
    """
    Creates the EPUB ZIP archive exactly as described in Part 4.
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(source_folder, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                if file == 'mimetype':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zf.write(file_path, arcname)

def stage_7_validation(epub_path):
    print(f'\n[Validation] Running EPUBCheck on {epub_path}...')
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        jar_path = os.path.join(base_dir, 'epubcheck.jar')
        result = subprocess.run(['java', '-jar', jar_path, epub_path], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print('Errors/Warnings:')
            print(result.stderr)
    except FileNotFoundError:
        print("Validation skipped: 'java' not found or 'epubcheck.jar' is missing.")

def universal_build_algorithm(args):
    """
    Scaffolds the project and coordinates all pipeline stages.
    """
    input_path = args.input
    output_path = args.output
    if not output_path:
        output_path = 'output.epub'
    print(f'Starting EPUB build for: {input_path}')
    temp_dir = tempfile.mkdtemp(prefix='epub_build_')
    try:
        input_type, raw_content = stage_1_input_analysis(input_path)
        print(f'Detected input type: {input_type}')
        structured_data = stage_2_structural_parsing(raw_content, input_type)
        manifest_items = []
        spine_items = []
        if input_type == 'images':
            print('Processing images...')
            img_manifest = stage_4_image_processing(input_path, temp_dir)
            manifest_items.extend(img_manifest)
            xhtml_dir = os.path.join(temp_dir, 'OEBPS', 'xhtml')
            os.makedirs(xhtml_dir, exist_ok=True)
            fxl_template = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n<head>\n  <title>Page {idx}</title>\n  <meta name="viewport" content="width={width}, height={height}"/>\n  <style type="text/css">\n    html, body {{\n      margin: 0;\n      padding: 0;\n      width: {width}px;\n      height: {height}px;\n      overflow: hidden;\n    }}\n    img {{\n      width: {width}px;\n      height: {height}px;\n      display: block;\n    }}\n  </style>\n</head>\n<body>\n  <img src="../images/{filename}" alt="Page {idx}"/>\n</body>\n</html>'
            for i, img_data in enumerate(img_manifest, 1):
                filename = f'page-{i:03d}.xhtml'
                filepath = os.path.join(xhtml_dir, filename)
                content = fxl_template.format(idx=i, width=img_data['width'], height=img_data['height'], filename=img_data['filename'])
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                ch_id = f'page{i:03d}'
                manifest_items.append({'id': ch_id, 'href': f'xhtml/{filename}', 'media-type': 'application/xhtml+xml', 'properties': 'rendition:layout-pre-paginated'})
                spine_items.append(ch_id)
        else:
            print('Generating XHTML...')
            man, spi = stage_3_xhtml_generation(structured_data, temp_dir, input_type)
            manifest_items.extend(man)
            spine_items.extend(spi)
        print('Assembling EPUB package...')
        metadata = {'title': args.title, 'author': args.author, 'language': args.language, 'fixed_layout': args.fixed_layout or input_type == 'images'}
        stage_5_package_assembly(metadata, manifest_items, spine_items, temp_dir)
        print(f'Packaging to {output_path}...')
        stage_6_zip_packaging(temp_dir, output_path)
        if args.validate:
            stage_7_validation(output_path)
        print('Build complete!')
    finally:
        shutil.rmtree(temp_dir)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Universal EPUB Builder based on Ultimate Guide.')
    parser.add_argument('input', help='Input file (.txt, .md, .docx) or folder of images.')
    parser.add_argument('--output', '-o', help='Output .epub file path.')
    parser.add_argument('--title', default='Untitled Ebook', help='Ebook title.')
    parser.add_argument('--author', default='Unknown Author', help='Ebook author.')
    parser.add_argument('--language', default='en', help='Language code (e.g. en).')
    parser.add_argument('--fixed-layout', action='store_true', help='Force fixed-layout EPUB.')
    parser.add_argument('--validate', action='store_true', help='Run EPUBCheck after building.')
    args = parser.parse_args()
    universal_build_algorithm(args)