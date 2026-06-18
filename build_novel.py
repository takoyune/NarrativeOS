import os
import re
import shutil
import tempfile
import markdown
import sys
import argparse
import urllib.request
import urllib.parse
import time
import configparser
import html
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
try:
    from PIL import Image
except ImportError:
    Image = None

def load_settings():
    """Load settings from settings.ini in the same directory as this script.
    Returns a dict with all settings, using defaults if file/keys are missing."""
    config = configparser.ConfigParser()
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.ini')
    if os.path.exists(settings_path):
        config.read(settings_path, encoding='utf-8')
    return {'image_format': config.get('image', 'format', fallback='webp').lower(), 'image_quality': config.getint('image', 'quality', fallback=90), 'max_size_mb': config.getfloat('image', 'max_size_mb', fallback=1.5), 'max_dimension': config.getint('image', 'max_dimension', fallback=2000), 'webp_method': config.getint('image', 'webp_method', fallback=4), 'language': config.get('output', 'language', fallback='id'), 'output_location': config.get('output', 'output_location', fallback='parent'), 'output_name_format': config.get('output', 'output_name_format', fallback='{folder_name}'), 'drop_cap': config.getboolean('styling', 'drop_cap', fallback=False), 'scene_break_symbol': config.get('styling', 'scene_break_symbol', fallback='❖ ❖ ❖'), 'font_size': config.getfloat('styling', 'font_size', fallback=1.0), 'line_height': config.getfloat('styling', 'line_height', fallback=1.8), 'text_indent': config.getfloat('styling', 'text_indent', fallback=1.5), 'auto_convert_images': config.getboolean('build', 'auto_convert_images', fallback=True), 'auto_compress': config.getboolean('build', 'auto_compress', fallback=True), 'download_online_images': config.getboolean('build', 'download_online_images', fallback=True), 'download_retries': config.getint('build', 'download_retries', fallback=3), 'download_timeout': config.getint('build', 'download_timeout', fallback=30)}
SETTINGS = load_settings()

def compress_image(filepath, max_mb=None):
    """Compress image and convert to the target format from settings.
    Returns the final filepath — will differ from input if converted."""
    if Image is None:
        return filepath
    if max_mb is None:
        max_mb = SETTINGS['max_size_mb']
    max_bytes = max_mb * 1024 * 1024
    target_format = SETTINGS['image_format']
    target_quality = SETTINGS['image_quality']
    max_dim = SETTINGS['max_dimension']
    webp_method = SETTINGS['webp_method']
    fmt_map = {'webp': ('webp', 'WEBP'), 'jpeg': ('jpg', 'JPEG'), 'jpg': ('jpg', 'JPEG'), 'png': ('png', 'PNG')}
    target_ext, pil_format = fmt_map.get(target_format, ('webp', 'WEBP'))
    try:
        with Image.open(filepath) as img:
            img = img.copy()
        if img.width > max_dim or img.height > max_dim:
            ratio = min(max_dim / img.width, max_dim / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        target_path = os.path.splitext(filepath)[0] + f'.{target_ext}'
        temp_path = filepath + f'.tmp.{target_ext}'
        is_already_target = filepath.lower().endswith(f'.{target_ext}')
        is_already_small = os.path.getsize(filepath) <= max_bytes
        if is_already_target and is_already_small:
            return filepath
        if pil_format in ('WEBP',) and img.mode in ('RGBA', 'LA', 'P'):
            img_save = img.convert('RGBA')
        elif pil_format in ('JPEG',):
            img_save = img.convert('RGB')
        else:
            img_save = img.convert('RGBA') if img.mode in ('RGBA', 'LA', 'P') else img.convert('RGB')
        save_kwargs = {'format': pil_format}
        if pil_format == 'WEBP':
            save_kwargs['method'] = webp_method
        if pil_format in ('WEBP', 'JPEG'):
            save_kwargs['quality'] = target_quality
        if pil_format in ('JPEG', 'PNG'):
            save_kwargs['optimize'] = True
        quality_steps = [target_quality, 85, 75, 65, 55, 40, 30]
        seen = set()
        quality_steps = [q for q in quality_steps if not (q in seen or seen.add(q))]
        for quality in quality_steps:
            if pil_format in ('WEBP', 'JPEG'):
                save_kwargs['quality'] = quality
            img_save.save(temp_path, **save_kwargs)
            if os.path.getsize(temp_path) <= max_bytes:
                if is_already_target:
                    os.replace(temp_path, filepath)
                    print(f'  → Compressed {target_format.upper()} to {os.path.getsize(filepath) / 1024 / 1024:.2f} MB at quality={quality}')
                    return filepath
                else:
                    os.replace(temp_path, target_path)
                    os.remove(filepath)
                    print(f'  → Converted {os.path.basename(filepath)} → {target_format.upper()} at quality={quality}: {os.path.basename(target_path)}')
                    return target_path
        if pil_format in ('WEBP', 'JPEG'):
            save_kwargs['quality'] = 20
        img_save.save(temp_path, **save_kwargs)
        if is_already_target:
            os.replace(temp_path, filepath)
            print(f'  → Compressed {target_format.upper()} (quality=20, forced): {os.path.basename(filepath)}')
            return filepath
        else:
            os.replace(temp_path, target_path)
            os.remove(filepath)
            print(f'  → Converted {os.path.basename(filepath)} → {target_format.upper()} (quality=20, forced): {os.path.basename(target_path)}')
            return target_path
    except Exception as e:
        print(f'Error compressing {filepath}: {e}')
        if os.path.exists(filepath + f'.tmp.{target_ext}'):
            os.remove(filepath + f'.tmp.{target_ext}')
        return filepath

def update_md_image_references(base_dir, old_name, new_name):
    """Scan all .md files in base_dir and replace old_name with new_name in image references.
    Called after a PNG→JPEG conversion to keep .md files in sync."""
    pattern = re.compile('(?<![\\w\\-])' + re.escape(old_name) + '(?![\\w\\-])', re.IGNORECASE)
    for fname in os.listdir(base_dir):
        if fname.lower().endswith('.md'):
            fpath = os.path.join(base_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    text = f.read()
                new_text = pattern.sub(new_name, text)
                if new_text != text:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    print(f'  → Updated reference in {fname}: {old_name} → {new_name}')
            except Exception as e:
                print(f'  Warning: Could not update references in {fname}: {e}')

def download_url(url, dest_path, retries=None, timeout=None):
    """Download a URL to dest_path with retry logic. Returns True on success."""
    if retries is None:
        retries = SETTINGS['download_retries']
    if timeout is None:
        timeout = SETTINGS['download_timeout']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if 'cdn.asdasdhg.com' in url:
        headers['Referer'] = 'https://kdtnovels.net/'
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response, open(dest_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            return True
        except Exception as e:
            if attempt < retries:
                print(f'  Attempt {attempt} failed: {e}. Retrying in 2s...')
                time.sleep(2)
            else:
                print(f'  Download failed after {retries} attempts: {e}')
    return False

def auto_compress_folder(base_dir):
    target_fmt = SETTINGS['image_format'].upper()
    print(f'Checking and converting images to {target_fmt} automatically...')
    target_ext = {'webp': '.webp', 'jpeg': '.jpg', 'jpg': '.jpg', 'png': '.png'}.get(SETTINGS['image_format'], '.webp')
    for folder_name in ['images', 'Ilustrasi', 'Ilustarasi']:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.exists(folder_path):
            for file in list(os.listdir(folder_path)):
                file_ext = os.path.splitext(file)[1].lower()
                is_image = file_ext in ('.png', '.jpg', '.jpeg', '.webp')
                is_target_format = file_ext == target_ext
                if is_image and (not is_target_format) and SETTINGS['auto_convert_images']:
                    filepath = os.path.join(folder_path, file)
                    print(f'Converting to {target_fmt}: {file}...')
                    new_path = compress_image(filepath)
                    if new_path != filepath:
                        update_md_image_references(base_dir, os.path.basename(filepath), os.path.basename(new_path))
                elif is_target_format and SETTINGS['auto_compress']:
                    filepath = os.path.join(folder_path, file)
                    if os.path.getsize(filepath) > SETTINGS['max_size_mb'] * 1024 * 1024:
                        print(f'Compressing large {target_fmt}: {file}...')
                        compress_image(filepath)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import epub_builder

def process_markdown_tricks(md_text):
    scene_break_symbol = html.escape(SETTINGS['scene_break_symbol'])
    md_text = re.sub('^\\s*(\\*\\*\\*|---)\\s*$', f'\n<div class="scene-break">{scene_break_symbol}</div>\n', md_text, flags=re.MULTILINE)
    md_text = re.sub('^\\s*\\(thought\\)\\s*\\[?(.*?)\\]?\\s*$', lambda m: f'<div class="thought-box">{html.escape(m.group(1))}</div>', md_text, flags=re.IGNORECASE | re.MULTILINE)
    md_text = re.sub('\\(thought\\)\\s*\\[(.*?)\\]', lambda m: f'<span class="thought-inline">{html.escape(m.group(1))}</span>', md_text, flags=re.IGNORECASE)
    md_text = re.sub('\\[stats\\](.*?)\\[/stats\\]', lambda m: f'\n<blockquote>\n{html.escape(m.group(1))}\n</blockquote>\n', md_text, flags=re.DOTALL | re.IGNORECASE)
    md_text = re.sub('\\[UI\\](.*?)\\[/UI\\]', lambda m: f'\n<pre class="game-ui-box">{html.escape(m.group(1))}</pre>\n', md_text, flags=re.DOTALL | re.IGNORECASE)
    md_text = re.sub('^\\s*(([■🍖▼▲◆○●❖])(\\s*\\2)*)\\s*$', f'<div class="scene-break">\\1</div>', md_text, flags=re.MULTILINE)
    return md_text

def add_dropcap(html):
    match = re.search('<p>([A-Za-z])(.*?</p>)', html, flags=re.DOTALL)
    if match:
        first_letter = match.group(1)
        rest = match.group(2)
        html = html[:match.start()] + f'<p><span class="dropcap">{first_letter}</span>{rest}' + html[match.end():]
    return html

def remove_first_p_indent(html):
    match = re.search('<p\\b([^>]*)>', html)
    if match:
        attrs = match.group(1)
        if 'class=' in attrs:
            new_attrs = re.sub('class=["\\\'](.*?)["\\\']', 'class="\\1 no-indent"', attrs)
        else:
            new_attrs = attrs + ' class="no-indent"'
        html = html[:match.start()] + f'<p{new_attrs}>' + html[match.end():]
    return html

def download_online_images(base_dir, md_text):
    pattern = re.compile('!\\[(.*?)\\]\\((https?://[^\\s\\)]+)[^\\)]*\\)', re.IGNORECASE)
    images_dir = os.path.join(base_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    def replacer(match):
        url = match.group(2)
        parsed = urllib.parse.urlparse(url)
        clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = 'downloaded_img.jpg'
        filename = re.sub('[^\\w.\\-]', '_', filename)
        local_path = os.path.join(images_dir, filename)
        if not os.path.exists(local_path):
            print(f'Downloading {clean_url}...')
            if not download_url(clean_url, local_path):
                return ''
        target_ext = {'webp': '.webp', 'jpeg': '.jpg', 'jpg': '.jpg', 'png': '.png'}.get(SETTINGS['image_format'], '.webp')
        if os.path.exists(local_path) and (not local_path.lower().endswith(target_ext)):
            new_path = compress_image(local_path)
            if new_path != local_path:
                filename = os.path.basename(new_path)
                local_path = new_path
        return f'(image) [images/{filename}]'
    return pattern.sub(replacer, md_text)

def build_novel(args=None):
    parser = argparse.ArgumentParser(description='Novel EPUB Builder')
    parser.add_argument('folder', nargs='?', default='d:\\code iwan\\EPUB\\Teori Guru Jenius Berengsek tentang Cara Membesarkan Putri Bangsawan yang Jatuh ke Jalan Kegelapan', help='Path to the novel folder')
    parsed_args = parser.parse_args(args)
    base_dir = parsed_args.folder
    if not os.path.exists(base_dir):
        print(f'Error: Folder not found: {base_dir}')
        return
    auto_compress_folder(base_dir)
    main_md_path = os.path.join(base_dir, 'main.md')
    if not os.path.exists(main_md_path):
        print(f'Error: main.md not found in {base_dir}')
        return
    with open(main_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    title_indo = re.search('Title Indonesia\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    title_en = re.search('Title Inggris\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    title_romaji = re.search('Title Romanji\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    title_japan = re.search('Title Japan\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    author_match = re.search('Author\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    cover_match = re.search('Cover\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    primary_override = re.search('Primary Title\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    primary_lang = primary_override.group(1).strip().lower() if primary_override else None
    title_map = {'id': title_indo, 'en': title_en, 'romaji': title_romaji, 'jp': title_japan}
    label_map = {'id': 'Title Indonesia', 'en': 'Title Inggris', 'romaji': 'Title Romanji', 'jp': 'Title Japan'}
    primary_title_label = ''
    if primary_lang and primary_lang in title_map and title_map[primary_lang]:
        title = title_map[primary_lang].group(1).strip()
        primary_title_label = label_map[primary_lang]
    elif title_indo and title_indo.group(1).strip():
        title = title_indo.group(1).strip()
        primary_title_label = 'Title Indonesia'
    elif title_en and title_en.group(1).strip():
        title = title_en.group(1).strip()
        primary_title_label = 'Title Inggris'
    elif title_romaji and title_romaji.group(1).strip():
        title = title_romaji.group(1).strip()
        primary_title_label = 'Title Romanji'
    elif title_japan and title_japan.group(1).strip():
        title = title_japan.group(1).strip()
        primary_title_label = 'Title Japan'
    else:
        title = os.path.basename(base_dir)
        primary_title_label = 'Title'
    volume_match = re.search('Volume\\s*:\\s*\\[(.*?)\\]', content, flags=re.IGNORECASE)
    if volume_match and volume_match.group(1).strip():
        vol_str = volume_match.group(1).strip()
        if not vol_str.lower().startswith('volume'):
            title += f' Volume {vol_str}'
        else:
            title += f' {vol_str}'
    author = author_match.group(1).strip() if author_match else 'Unknown Author'
    cover_rel_path = cover_match.group(1).strip() if cover_match else None
    metadata_section = content.split('Table of Content')[0]
    metadata_pairs = re.findall('^([^:\\n]+?)\\s*:\\s*\\[(.*?)\\]', metadata_section, flags=re.MULTILINE)
    has_about = re.search('\\[About\\]', content, flags=re.IGNORECASE) is not None
    about_body_html = ''
    if has_about:
        about_body_elements = []
        about_body_elements.append('<div class="info-page">')
        about_body_elements.append('  <h1>About This Ebook</h1>')
        about_body_elements.append('  <hr class="info-divider"/>')
        about_body_elements.append('  <div class="info-container">')
        about_body_elements.append('    <div class="info-item info-item-title">')
        about_body_elements.append(f'      <span class="info-label">{primary_title_label}</span>')
        about_body_elements.append(f'      <span class="info-value"><strong>{title}</strong></span>')
        about_body_elements.append('    </div>')
        for key, val in metadata_pairs:
            key_strip = key.strip()
            val_strip = val.strip()
            if key_strip.lower() in ['cover', primary_title_label.lower()]:
                continue
            about_body_elements.append('    <div class="info-item">')
            about_body_elements.append(f'      <span class="info-label">{key_strip}</span>')
            about_body_elements.append(f'      <span class="info-value">{val_strip}</span>')
            about_body_elements.append('    </div>')
        about_body_elements.append('  </div>')
        about_body_elements.append('  <div class="info-watermark">')
        about_body_elements.append('    <a href="https://github.com/takoyune" class="watermark-link">TakoYune</a>')
        about_body_elements.append('  </div>')
        about_body_elements.append('</div>')
        about_body_html = '\n'.join(about_body_elements)
    temp_dir = tempfile.mkdtemp(prefix='epub_novel_')
    try:
        manifest_items = []
        spine_items = []
        oebps_dir = os.path.join(temp_dir, 'OEBPS')
        xhtml_dir = os.path.join(oebps_dir, 'xhtml')
        images_dir = os.path.join(oebps_dir, 'images')
        os.makedirs(xhtml_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        def add_image_to_manifest(filename, src_path, is_cover=False):
            """Add image to manifest, converting to WebP if needed.
            Returns the actual filename used (may be .webp) on success, or empty string on failure."""
            if not os.path.exists(src_path):
                print(f'Warning: Image not found at {src_path}')
                return ''
            ext = filename.lower().split('.')[-1]
            if ext in ('png', 'jpg', 'jpeg') and Image is not None:
                webp_filename = os.path.splitext(filename)[0] + '.webp'
                dest_path = os.path.join(images_dir, webp_filename)
                if not os.path.exists(dest_path):
                    try:
                        with Image.open(src_path) as img:
                            img_copy = img.copy()
                        if img_copy.mode in ('RGBA', 'LA', 'P'):
                            img_save = img_copy.convert('RGBA')
                        else:
                            img_save = img_copy.convert('RGB')
                        img_save.save(dest_path, format='WEBP', quality=90, method=4)
                    except Exception as e:
                        print(f'  Warning: WebP conversion failed for {filename}, using original: {e}')
                        dest_path = os.path.join(images_dir, filename)
                        if not os.path.exists(dest_path):
                            shutil.copy2(src_path, dest_path)
                        webp_filename = filename
                filename = webp_filename
            else:
                dest_path = os.path.join(images_dir, filename)
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
            img_id = 'cover-img' if is_cover else f'img-{filename}'
            img_id = re.sub('[^a-zA-Z0-9_.-]', '_', img_id)
            if img_id and img_id[0].isdigit():
                img_id = 'i_' + img_id
            if any((item['id'] == img_id for item in manifest_items)):
                return filename
            media_type = 'image/webp'
            if not filename.lower().endswith('.webp'):
                ext = filename.lower().split('.')[-1]
                media_type = f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
            manifest_item = {'id': img_id, 'href': f'images/{filename}', 'media-type': media_type}
            if is_cover:
                manifest_item['properties'] = 'cover-image'
            manifest_items.append(manifest_item)
            return filename
        xhtml_template = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n<head>\n  <title>{title}</title>\n  <link rel="stylesheet" type="text/css" href="../css/style.css"/>\n</head>\n<body>\n{body}\n</body>\n</html>'
        if cover_rel_path:
            if cover_rel_path.lower().startswith(('http://', 'https://')):
                src_images_dir = os.path.join(base_dir, 'images')
                os.makedirs(src_images_dir, exist_ok=True)
                parsed = urllib.parse.urlparse(cover_rel_path)
                clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
                cover_filename = os.path.basename(parsed.path) or 'cover.jpg'
                cover_src = os.path.join(src_images_dir, cover_filename)
                if not os.path.exists(cover_src):
                    print(f'Downloading cover from {clean_url}...')
                    download_url(clean_url, cover_src)
                if os.path.exists(cover_src):
                    new_cover_src = compress_image(cover_src)
                    if new_cover_src != cover_src:
                        cover_src = new_cover_src
                        cover_filename = os.path.basename(cover_src)
            else:
                cover_src = os.path.join(base_dir, cover_rel_path)
                if not os.path.exists(cover_src):
                    for folder in ['images', 'Ilustrasi', 'Ilustarasi']:
                        for target in ['images', 'Ilustrasi', 'Ilustarasi']:
                            if folder in cover_src:
                                candidate = cover_src.replace(folder, target)
                                if os.path.exists(candidate):
                                    cover_src = candidate
                                    break
            add_image_to_manifest(os.path.basename(cover_src), cover_src, is_cover=True)
        chapter_idx = 1
        inline_img_pattern = re.compile('\\(image\\)\\s*\\[(?:.*?[\\/\\\\])?([^\\/\\]\\\\ ]+\\.(?:webp|jpg|jpeg|png))\\]', re.IGNORECASE)
        toc_start_idx = content.lower().find('table of content')
        if toc_start_idx == -1:
            print('Error: Table of Content block not found in main.md')
            return
        toc_part = content[toc_start_idx:]
        start_bracket = toc_part.find('[')
        end_bracket = toc_part.rfind(']')
        if start_bracket == -1 or end_bracket == -1:
            print('Error: Table of Content block not found or malformed')
            return
        toc_block = toc_part[start_bracket+1:end_bracket]
        raw_toc_items = []
        for line in toc_block.split('\n'):
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                raw_toc_items.append(line[1:-1])
        toc_items = [item.strip() for item in raw_toc_items if item.strip()]
        for item in toc_items:
            cover_match = re.match('^Cover\\s*\\((.*?)\\)$', item, flags=re.IGNORECASE)
            if cover_match:
                c_path = cover_match.group(1).strip()
                if c_path.lower().startswith(('http://', 'https://')):
                    src_images_dir = os.path.join(base_dir, 'images')
                    os.makedirs(src_images_dir, exist_ok=True)
                    parsed = urllib.parse.urlparse(c_path)
                    clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
                    cover_filename = os.path.basename(parsed.path) or 'cover.jpg'
                    c_src = os.path.join(src_images_dir, cover_filename)
                    if not os.path.exists(c_src):
                        print(f'Downloading cover from {clean_url}...')
                        download_url(clean_url, c_src)
                    if os.path.exists(c_src):
                        new_c_src = compress_image(c_src)
                        if new_c_src != c_src:
                            c_src = new_c_src
                            cover_filename = os.path.basename(c_src)
                    c_filename = cover_filename
                else:
                    c_src = os.path.join(base_dir, c_path)
                    c_filename = os.path.basename(c_src)
                    if not os.path.exists(c_src):
                        c_src = os.path.join(base_dir, 'images', c_filename)
                    if not os.path.exists(c_src):
                        c_src = os.path.join(base_dir, 'Ilustrasi', c_filename)
                    if not os.path.exists(c_src):
                        c_src = os.path.join(base_dir, 'Ilustarasi', c_filename)
                actual_c_filename = add_image_to_manifest(c_filename, c_src)
                if actual_c_filename:
                    cover_html = f'<div class="full-page-image"><img src="../images/{actual_c_filename}" alt="Cover" /></div>\n'
                    xhtml_content = xhtml_template.format(title='Cover', body=cover_html)
                    out_filename = 'cover.xhtml'
                    out_path = os.path.join(xhtml_dir, out_filename)
                    with open(out_path, 'w', encoding='utf-8') as out_f:
                        out_f.write(xhtml_content)
                    manifest_items.append({'id': 'cover_page', 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                    spine_items.append({'id': 'cover_page', 'title': 'Cover'})
                continue
            illus_match = re.match('^(?:Ilustra(?:s|a)i|images)(?:\\(folder\\))?\\((.*?)\\)$', item, flags=re.IGNORECASE)
            if illus_match:
                folder_images = [os.path.basename(img.strip()) for img in illus_match.group(1).split(',') if img.strip()]
                illus_html_list = []
                for img_name in folder_images:
                    img_src = os.path.join(base_dir, 'images', img_name)
                    if not os.path.exists(img_src):
                        img_src = os.path.join(base_dir, 'Ilustrasi', img_name)
                    if not os.path.exists(img_src):
                        img_src = os.path.join(base_dir, 'Ilustarasi', img_name)
                    actual_img_name = add_image_to_manifest(img_name, img_src)
                    if actual_img_name:
                        illus_html_list.append(f'<div class="full-page-image"><img src="../images/{actual_img_name}" alt="Illustration" /></div>')
                if illus_html_list:
                    illus_body = '\n'.join(illus_html_list)
                    xhtml_content = xhtml_template.format(title='Ilustrasi', body=illus_body)
                    out_filename = 'illustrations.xhtml'
                    out_path = os.path.join(xhtml_dir, out_filename)
                    with open(out_path, 'w', encoding='utf-8') as out_f:
                        out_f.write(xhtml_content)
                    illus_id = 'illustrations_page'
                    manifest_items.append({'id': illus_id, 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                    spine_items.append({'id': illus_id, 'title': 'Ilustrasi'})
                continue
            if item.lower() == 'table of contents':
                spine_items.append({'id': 'nav', 'title': 'Table of Contents'})
                continue
            if item.lower() == 'about':
                if has_about:
                    about_html = xhtml_template.format(title='About', body=about_body_html)
                    out_filename = 'about.xhtml'
                    out_path = os.path.join(xhtml_dir, out_filename)
                    with open(out_path, 'w', encoding='utf-8') as out_f:
                        out_f.write(about_html)
                    manifest_items.append({'id': 'about_page', 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                    spine_items.append({'id': 'about_page', 'title': 'About'})
                continue
            chapter_match = re.match('^(.*?\\.md)\\s*\\(file\\)$', item, flags=re.IGNORECASE)
            if chapter_match:
                filename = chapter_match.group(1).strip()
                filename = filename.replace('Boonus Chapter.md', 'Bonus Chapter.md')
                file_path = os.path.join(base_dir, filename)
                if not os.path.exists(file_path):
                    for df in os.listdir(base_dir):
                        if df.lower() == filename.lower():
                            file_path = os.path.join(base_dir, df)
                            break
                if os.path.exists(file_path):
                    print(f'Processing: {filename}')
                    with open(file_path, 'r', encoding='utf-8') as cf:
                        md_text = cf.read()
                    new_md_text = download_online_images(base_dir, md_text)
                    if new_md_text != md_text:
                        print(f'Updating {filename} with local image references...')
                        with open(file_path, 'w', encoding='utf-8') as cf:
                            cf.write(new_md_text)
                        md_text = new_md_text
                    ch_title = filename.replace('.md', '').replace('.MD', '')
                    first_heading = re.search('^#\\s+(.*)', md_text, flags=re.MULTILINE)
                    if first_heading:
                        ch_title = first_heading.group(1).strip()
                    else:
                        for line in md_text.split('\n'):
                            line_stripped = line.strip()
                            if line_stripped and (not line_stripped.startswith('(image)')) and (not line_stripped.startswith('![')):
                                ch_title = line_stripped
                                break
                    matches = list(inline_img_pattern.finditer(md_text))
                    segments = []
                    last_pos = 0
                    for match in matches:
                        start, end = match.span()
                        text_segment = md_text[last_pos:start]
                        segments.append(('text', text_segment))
                        img_filename = match.group(1)
                        segments.append(('image', img_filename))
                        last_pos = end
                    text_segment = md_text[last_pos:]
                    segments.append(('text', text_segment))
                    filtered_segments = []
                    for seg_type, val in segments:
                        if seg_type == 'text':
                            if val.strip():
                                filtered_segments.append((seg_type, val))
                        else:
                            filtered_segments.append((seg_type, val))
                    if not filtered_segments:
                        continue
                    has_text = any((seg_type == 'text' for seg_type, _ in filtered_segments))
                    if not has_text:
                        illus_html_list = []
                        for seg_type, val in filtered_segments:
                            if seg_type == 'image':
                                img_filename = val
                                src = os.path.join(base_dir, 'images', img_filename)
                                if not os.path.exists(src):
                                    src = os.path.join(base_dir, 'Ilustrasi', img_filename)
                                if not os.path.exists(src):
                                    src = os.path.join(base_dir, 'Ilustarasi', img_filename)
                                actual_img = add_image_to_manifest(img_filename, src)
                                if actual_img:
                                    illus_html_list.append(f'<div class="full-page-image"><img src="../images/{actual_img}" alt="Illustration" /></div>')
                        if illus_html_list:
                            illus_body = '\n'.join(illus_html_list)
                            xhtml_content = xhtml_template.format(title=ch_title, body=illus_body)
                            out_filename = f'chapter-{chapter_idx:02d}-01.xhtml'
                            out_path = os.path.join(xhtml_dir, out_filename)
                            with open(out_path, 'w', encoding='utf-8') as out_f:
                                out_f.write(xhtml_content)
                            ch_id = f'ch{chapter_idx:02d}_01'
                            manifest_items.append({'id': ch_id, 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                            spine_items.append({'id': ch_id, 'title': ch_title})
                            chapter_idx += 1
                        continue
                    part_idx = 1
                    first_text_segment_done = False
                    for seg_type, val in filtered_segments:
                        if seg_type == 'text':
                            segment_text = process_markdown_tricks(val)
                            segment_html = markdown.markdown(segment_text, extensions=['tables', 'fenced_code'])
                            if not first_text_segment_done:
                                first_text_segment_done = True
                                if SETTINGS['drop_cap']:
                                    segment_html = add_dropcap(segment_html)
                            else:
                                segment_html = remove_first_p_indent(segment_html)
                            xhtml_content = xhtml_template.format(title=ch_title, body=segment_html)
                            out_filename = f'chapter-{chapter_idx:02d}-{part_idx:02d}.xhtml'
                            out_path = os.path.join(xhtml_dir, out_filename)
                            with open(out_path, 'w', encoding='utf-8') as out_f:
                                out_f.write(xhtml_content)
                            ch_id = f'ch{chapter_idx:02d}_{part_idx:02d}'
                            manifest_items.append({'id': ch_id, 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                            is_first_part = part_idx == 1
                            spine_item = {'id': ch_id, 'title': ch_title}
                            if not is_first_part:
                                spine_item['exclude_from_toc'] = True
                            spine_items.append(spine_item)
                            part_idx += 1
                        elif seg_type == 'image':
                            img_filename = val
                            src = os.path.join(base_dir, 'images', img_filename)
                            if not os.path.exists(src):
                                src = os.path.join(base_dir, 'Ilustrasi', img_filename)
                            if not os.path.exists(src):
                                src = os.path.join(base_dir, 'Ilustarasi', img_filename)
                            actual_img = add_image_to_manifest(img_filename, src)
                            if actual_img:
                                is_first_part = part_idx == 1
                                illus_html = f'<div class="full-page-image"><img src="../images/{actual_img}" alt="Illustration" /></div>\n'
                                xhtml_content = xhtml_template.format(title=ch_title if is_first_part else 'Ilustrasi', body=illus_html)
                                out_filename = f'chapter-{chapter_idx:02d}-{part_idx:02d}.xhtml'
                                out_path = os.path.join(xhtml_dir, out_filename)
                                with open(out_path, 'w', encoding='utf-8') as out_f:
                                    out_f.write(xhtml_content)
                                ch_id = f'ch{chapter_idx:02d}_{part_idx:02d}'
                                manifest_items.append({'id': ch_id, 'href': f'xhtml/{out_filename}', 'media-type': 'application/xhtml+xml'})
                                spine_item = {'id': ch_id, 'title': ch_title if is_first_part else 'Ilustrasi'}
                                if not is_first_part:
                                    spine_item['exclude_from_toc'] = True
                                spine_items.append(spine_item)
                                part_idx += 1
                    chapter_idx += 1
                else:
                    print(f'Warning: Chapter file not found: {filename}')
                continue
            else:
                print(f"Warning: Unrecognized TOC item: '{item}'")
        metadata = {'title': title, 'author': author, 'language': SETTINGS['language'], 'fixed_layout': False}
        epub_builder.stage_5_package_assembly(metadata, manifest_items, spine_items, temp_dir, settings=SETTINGS)
        novel_folder_name = os.path.basename(base_dir)
        try:
            vol_match = re.search('Volume\\s*(\\d+)', novel_folder_name, flags=re.IGNORECASE)
            volume_num = vol_match.group(1) if vol_match else ''
        except:
            volume_num = ''
        epub_name = SETTINGS['output_name_format'].format(title=title, volume=volume_num, folder_name=novel_folder_name)
        safe_name = ''.join([c for c in epub_name if c.isalpha() or c.isdigit() or c in ' -_']).strip()
        safe_name = safe_name.replace(' ', '_')
        if SETTINGS['output_location'].lower() == 'same':
            output_dir = base_dir
        else:
            output_dir = os.path.dirname(base_dir)
        output_epub = os.path.join(output_dir, f'{safe_name}.epub')
        print(f'Packaging to {output_epub}...')
        epub_builder.stage_6_zip_packaging(temp_dir, output_epub)
        epub_size_mb = os.path.getsize(output_epub) / 1024 / 1024
        ch_count = sum((1 for s in spine_items if isinstance(s, dict) and s.get('id', '').endswith('_01') and s.get('id', '').startswith('ch')))
        img_count = sum((1 for m in manifest_items if m.get('media-type', '').startswith('image/')))
        print(f'\n✅ Done! {title}')
        print(f'   📚 {ch_count} chapter(s)  |  🖼  {img_count} image(s)  |  📦 {epub_size_mb:.1f} MB')
        print(f'   📄 {output_epub}\n')
    finally:
        shutil.rmtree(temp_dir)
if __name__ == '__main__':
    build_novel()