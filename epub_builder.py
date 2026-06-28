import os
import sys
import uuid
import datetime
import shutil
import tempfile
import zipfile
import subprocess
import html


def xml_safe(text):
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def get_media_type(filename):
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    return {
        'webp': 'image/webp',
        'png':  'image/png',
        'jpg':  'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif':  'image/gif',
        'svg':  'image/svg+xml',
    }.get(ext, 'image/png')



def stage_5_package_assembly(metadata, manifest_items, spine_items, output_dir, settings=None):
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
    css_content = '/* Base page settings */\nbody {\n  font-family: "Palatino", "Palatino Linotype", "Book Antiqua", serif;\n  font-size: {font_size}em;\n  line-height: {line_height};\n  margin: 0;\n  padding: 0 5%;\n  color: #1a1a1a;\n  background-color: transparent;\n}\n\n/* Headings */\nh1 {\n  font-size: 1.8em;\n  font-weight: bold;\n  text-align: center;\n  margin-top: 2em;\n  margin-bottom: 1em;\n  page-break-before: always;\n}\n\nh2 {\n  font-size: 1.4em;\n  font-weight: bold;\n  text-align: center;\n  margin-top: 1.5em;\n  margin-bottom: 0.5em;\n}\n\nh3 {\n  font-size: 1.15em;\n  font-weight: bold;\n  margin-top: 1.2em;\n  margin-bottom: 0.3em;\n}\n\n/* Body paragraphs */\np {\n  margin: 0 0 0.5em 0;\n  padding: 0;\n  text-indent: {text_indent}em;\n  text-align: justify;\n}\n\nh1 + p, h2 + p, h3 + p, .full-page-image + p, .no-indent {\n  text-indent: 0;\n}\n\n/* Full-page illustration pages (each image gets its own spine xhtml file) */\n/* IMPORTANT: Do NOT use height:100vh or display:flex here.\n   Those are unreliable on Kobo/Kindle/Moon+ and cause the "ghost image" bug\n   where the image renders blank until the user slowly swipes. */\nbody.image-page {\n  margin: 0;\n  padding: 0;\n  text-align: center;\n}\n\n.full-page-image {\n  margin: 0;\n  padding: 0;\n  text-align: center;\n  page-break-before: always;\n  page-break-after: always;\n  /* epub:spread-page for two-page spread support */\n  -epub-page-break-before: always;\n  -epub-page-break-after: always;\n}\n\n.full-page-image img {\n  /* width: 100% fills the reader column; height: auto preserves aspect ratio.\n     This is the most universally supported approach across all EPUB readers. */\n  width: 100%;\n  height: auto;\n  max-width: 100%;\n  display: block;\n  margin: 0 auto;\n}\n\n/* UI / Visual Stats Elements */\ntable {\n  width: 100%;\n  border-collapse: collapse;\n  margin: 1.5em 0;\n  background-color: #f8f9fa;\n  border: 1px solid #dee2e6;\n  border-radius: 4px;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n  font-size: 0.9em;\n}\n\nth, td {\n  padding: 0.75em;\n  border-bottom: 1px solid #dee2e6;\n  text-align: left;\n}\n\nth {\n  background-color: #e9ecef;\n  font-weight: bold;\n}\n\nblockquote {\n  margin: 1.5em 0;\n  padding: 1.2em 1.5em;\n  background-color: #2b2b36;\n  border: 2px solid #d4af37;\n  color: #f8f9fa;\n  font-family: "Courier New", Courier, monospace;\n  border-radius: 8px;\n  box-shadow: 0 4px 8px rgba(0,0,0,0.3);\n  white-space: pre-wrap;\n}\n\nblockquote p {\n  margin: 0 0 0.5em 0;\n  text-indent: 0;\n  text-align: left;\n  color: #f8f9fa;\n}\n\n/* Markdown Tricks */\n.dropcap {\n  float: left;\n  font-size: 3.2em;\n  line-height: 0.8;\n  margin-right: 0.1em;\n  margin-top: 0.1em;\n  margin-bottom: -0.1em;\n  font-weight: bold;\n  font-family: Georgia, "Times New Roman", serif;\n  color: #2c3e50;\n}\n\n.scene-break {\n  text-align: center;\n  margin: 2em 0;\n  font-size: 1.5em;\n  letter-spacing: 0.5em;\n  color: #888;\n}\n\n.thought {\n  font-style: italic;\n}\n\n/* Thought Box styling */\n.thought-box {\n  margin: 1em 0;\n  font-style: italic;\n}\n\n.thought-inline {\n  font-style: italic;\n}\n\n/* About / Info Page styling */\n.info-page {\n  text-align: center;\n  padding: 5% 4%;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n}\n\n.info-page h1 {\n  font-size: 1.4em;\n  font-weight: 700;\n  text-align: center;\n  margin-top: 0.5em;\n  margin-bottom: 0.3em;\n  letter-spacing: 0.12em;\n  text-transform: uppercase;\n  border: none;\n  padding-bottom: 0;\n}\n\n.info-divider {\n  width: 50px;\n  height: 2px;\n  background-color: currentColor;\n  opacity: 0.5;\n  border: none;\n  border-radius: 2px;\n  margin: 0.8em auto 2em auto;\n}\n\n.info-container {\n  display: block;\n  text-align: center;\n  max-width: 90%;\n  margin: 0 auto;\n}\n\n.info-item {\n  margin: 1em auto;\n  padding: 0.5em 0;\n  border-bottom: 1px solid currentColor;\n  opacity: 0.9;\n  text-align: center;\n}\n\n.info-item:last-child {\n  border-bottom: none;\n}\n\n.info-item-title {\n  padding: 0.8em 1em;\n  border: 1px solid currentColor;\n  border-radius: 8px;\n  margin-bottom: 1.5em;\n  opacity: 1;\n}\n\n.info-label {\n  display: block;\n  font-size: 0.7em;\n  font-weight: 600;\n  text-transform: uppercase;\n  letter-spacing: 0.15em;\n  margin-bottom: 0.4em;\n  opacity: 0.7;\n}\n\n.info-value {\n  display: block;\n  font-size: 1.1em;\n  line-height: 1.4;\n  font-weight: 500;\n}\n\n/* TakoYune Watermark */\n.info-watermark {\n  margin-top: 3em;\n  text-align: center;\n  opacity: 0.18;\n}\n\n.watermark-link {\n  font-size: 0.65em;\n  font-weight: 600;\n  letter-spacing: 0.25em;\n  text-transform: uppercase;\n  text-decoration: none;\n  color: inherit;\n  border-bottom: 1px solid currentColor;\n  padding-bottom: 1px;\n}\n\n.watermark-link:hover {\n  opacity: 0.5;\n}\n\n\n.toc-page {\n  padding: 1em 5%;\n  font-family: "Inter", "Roboto", "Segoe UI", sans-serif;\n}\n\n.toc-title {\n  text-align: center;\n  font-size: 1.6em;\n  font-weight: bold;\n  letter-spacing: 0.15em;\n  text-transform: uppercase;\n  margin-bottom: 1.5em;\n  padding-bottom: 0.5em;\n  border-bottom: 2px solid #dee2e6;\n}\n\n.toc-list {\n  list-style: none;\n  padding: 0;\n  margin: 0;\n}\n\n.toc-list li {\n  margin: 0;\n  padding: 0;\n  border-bottom: 1px solid #eee;\n}\n\n.toc-list li:last-child {\n  border-bottom: none;\n}\n\n.toc-list li a {\n  display: block;\n  padding: 0.8em 0.5em;\n  text-decoration: none;\n  color: inherit;\n  font-size: 1em;\n  transition: background-color 0.2s;\n}\n\n.toc-list li a:hover {\n  background-color: #f8f9fa;\n}\n\n/* Game UI Box */\npre.game-ui-box, .game-ui-box {\n  margin: 1.5em 0;\n  padding: 1em 1.5em;\n  font-family: "VT323", "Courier New", Courier, monospace;\n  font-size: 1.15em;\n  font-weight: bold;\n  white-space: pre-wrap;\n  line-height: 1.6;\n  background: none;\n  border: none;\n}'
    css_content += (
        '\n\n/* 3.1 Kobo / WebKit compatibility */'
        '\nbody {'
        '\n  -webkit-text-size-adjust: 100%;'
        '\n}'
        '\n.image-wrapper {'
        '\n  text-align: center;'
        '\n}'
        '\n.image-wrapper img {'
        '\n  max-width: 100%;'
        '\n  height: auto;'
        '\n}'
        '\n\n/* 3.3 Dark mode */'
        '\n@media (prefers-color-scheme: dark) {'
        '\n  body, p, span, div, li, td, th {'
        '\n    color: #ddd8cc !important;'
        '\n    background-color: #1c1c1e !important;'
        '\n  }'
        '\n  h1, h2, h3, h4, h5, h6 {'
        '\n    color: #e8e2d5 !important;'
        '\n  }'
        '\n  blockquote {'
        '\n    background-color: #252530 !important;'
        '\n    border-color: #b8962e !important;'
        '\n    color: #ddd8cc !important;'
        '\n  }'
        '\n  blockquote p, blockquote span {'
        '\n    color: #ddd8cc !important;'
        '\n    background-color: transparent !important;'
        '\n  }'
        '\n  table {'
        '\n    background-color: #252530 !important;'
        '\n    border-color: #444 !important;'
        '\n  }'
        '\n  th {'
        '\n    background-color: #333340 !important;'
        '\n  }'
        '\n  th, td {'
        '\n    border-color: #444 !important;'
        '\n  }'
        '\n}'

    )
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
        elif itemref == 'cover_page':
            spine_str += f'    <itemref idref="{itemref}" linear="no"/>\n'
        else:
            spine_str += f'    <itemref idref="{itemref}"/>\n'
    fxl_meta = ''
    if metadata.get('fixed_layout'):
        fxl_meta = '\n    <meta property="rendition:layout">pre-paginated</meta>\n    <meta property="rendition:orientation">auto</meta>\n    <meta property="rendition:spread">auto</meta>'
    
    safe_title = xml_safe(metadata.get('title', 'Untitled'))
    safe_author = xml_safe(metadata.get('author', 'Unknown Author'))
    safe_lang = xml_safe(metadata.get('language', 'en'))

    cover_img_id = next((item['id'] for item in manifest_items if item.get('properties') == 'cover-image'), '')
    cover_meta = f'\n    <meta name="cover" content="{cover_img_id}"/>' if cover_img_id else ''

    opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{safe_title}</dc:title>
    <dc:creator>{safe_author}</dc:creator>
    <dc:language>{safe_lang}</dc:language>
    <dc:identifier id="bookid">urn:uuid:{uuid.uuid4()}</dc:identifier>
    <meta property="dcterms:modified">{datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]}Z</meta>{fxl_meta}{cover_meta}
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
    nav_li_str = ''
    for i, item in enumerate(spine_items):
        itemref = item['id'] if isinstance(item, dict) else item
        if isinstance(item, dict) and item.get('exclude_from_toc'):
            continue
        title = item.get('title') if isinstance(item, dict) else f'Chapter {i + 1}'
        href = next((x['href'] for x in manifest_items if x['id'] == itemref), None)
        if href:
            nav_li_str += f'      <li><a href="{href}">{xml_safe(title)}</a></li>\n'
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
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(source_folder, 'mimetype'), 'mimetype',
                 compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(source_folder):
            dirs.sort()
            files.sort()
            for file in files:
                if file == 'mimetype':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zf.write(file_path, arcname)


def stage_7_validation(epub_path):
    print(f'\n[Validation] Running EPUBCheck on {epub_path}...')

    try:
        import epubcheck as _epubcheck
        result = _epubcheck.validate(epub_path)
        if result.valid:
            print('  EPUBCheck: VALID ✓')
        else:
            print(f'  EPUBCheck: {len(result.messages)} issue(s):')
            for msg in result.messages:
                print(f'    [{msg.level}] {msg}')
        return
    except ImportError:
        pass
    except Exception as e:
        print(f'  epubcheck package error: {e}')

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        jar_path = os.path.join(base_dir, 'epubcheck.jar')
        result = subprocess.run(
            ['java', '-jar', jar_path, epub_path],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print('Errors/Warnings:')
            print(result.stderr)
    except FileNotFoundError:
        print("  Validation skipped: install 'epubcheck' (pip install epubcheck) or ensure java + epubcheck.jar are available.")
