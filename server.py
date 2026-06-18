import os
import threading
import re
import sys
import json
import shutil
import subprocess
import configparser
from pathlib import Path
from typing import Optional
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / 'static'
VENV_PYTHON = BASE_DIR / '.venv' / 'Scripts' / 'python.exe'
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
app = FastAPI(title='NarrativeOS EPUB Toolkit', version='2.0.0')
STATIC_DIR.mkdir(exist_ok=True)
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

file_save_lock = threading.Lock()


class ScrapeRequest(BaseModel):
    url: str
    novel: str
    volume: str
    filename: str
    html_content: str = None

class SaveMdRequest(BaseModel):
    path: str
    content: str

class BuildRequest(BaseModel):
    novel: str
    volume: str

class SettingsRequest(BaseModel):
    settings: dict

class CreateVolumeRequest(BaseModel):
    novel: str
    volume: str

class CreateNovelRequest(BaseModel):
    novel: str

class RenameRequest(BaseModel):
    old_path: str
    new_path: str

class DeleteRequest(BaseModel):
    path: str

class LogRequest(BaseModel):
    level: str
    message: str

def safe_path(rel: str) -> Path:
    """Resolve a relative path safely inside BASE_DIR."""
    p = (BASE_DIR / rel).resolve()
    if not str(p).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=403, detail='Path traversal denied')
    try:
        rel_parts = p.relative_to(BASE_DIR).parts
        if rel_parts:
            if rel_parts[0] in ['static', '.venv', '__pycache__', '.git', 'scratch']:
                raise HTTPException(status_code=403, detail='Access to system directories denied')
            if len(rel_parts) == 1 and p.name != 'main.md' and (p.suffix in ['.py', '.ini', '.log', '.bat']):
                raise HTTPException(status_code=403, detail='Access to core application files denied')
    except ValueError:
        pass
    return p
import datetime

def log_event(level: str, message: str):
    log_file = BASE_DIR / 'narrative_os.log'
    settings = read_settings()
    max_logs_str = settings.get('Settings', {}).get('max_logs', '1000')
    try:
        max_logs = int(max_logs_str)
    except ValueError:
        max_logs = 1000
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_entry = f'[{timestamp}] [{level.upper()}] {message}\n'
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(new_entry)
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) > max_logs + 100:
            lines = lines[-max_logs:]
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
    except:
        pass

def read_settings() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(str(BASE_DIR / 'settings.ini'), encoding='utf-8')
    out = {}
    for section in cfg.sections():
        out[section] = dict(cfg[section])
    return out

def write_settings(data: dict):
    cfg = configparser.ConfigParser()
    for section, kv in data.items():
        cfg[section] = kv
    with open(str(BASE_DIR / 'settings.ini'), 'w', encoding='utf-8') as f:
        cfg.write(f)

def list_novels() -> list:
    novels = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and (not item.name.startswith(('.', '_', 'static', 'scratch'))):
            skip = {'.venv', '__pycache__', 'Hasil extarat', 'scratch'}
            if item.name not in skip:
                novels.append(item.name)
    return sorted(novels)

def list_volumes(novel: str) -> list:
    novel_dir = safe_path(novel)
    if not novel_dir.is_dir():
        return []
    vols = []
    for item in novel_dir.iterdir():
        if item.is_dir():
            vols.append(item.name)
    return sorted(vols)

def list_md_files(novel: str, volume: str) -> list:
    vol_dir = safe_path(f'{novel}/{volume}')
    if not vol_dir.is_dir():
        return []
    files = [f.name for f in vol_dir.iterdir() if f.suffix.lower() == '.md']
    return sorted(files)

def list_images(novel: str, volume: str) -> list:
    vol_dir = safe_path(f'{novel}/{volume}')
    img_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
    results = []
    img_dir = vol_dir / 'images'
    if img_dir.is_dir():
        for f in img_dir.iterdir():
            if f.suffix.lower() in img_exts:
                results.append(f'images/{f.name}')
    for f in vol_dir.iterdir():
        if f.suffix.lower() in img_exts:
            results.append(f.name)
    return sorted(results)

@app.get('/')
def root():
    return FileResponse(str(STATIC_DIR / 'index.html'))

@app.get('/api/novels')
def get_novels():
    return {'novels': list_novels()}

@app.get('/api/novels/{novel}/volumes')
def get_volumes(novel: str):
    return {'volumes': list_volumes(novel)}

@app.get('/api/novels/{novel}/volumes/{volume}/files')
def get_files(novel: str, volume: str):
    return {'md_files': list_md_files(novel, volume), 'images': list_images(novel, volume)}

@app.post('/api/novels')
def create_novel(req: CreateNovelRequest):
    d = BASE_DIR / req.novel
    if d.exists():
        raise HTTPException(400, 'Novel folder already exists')
    d.mkdir()
    return {'ok': True, 'path': req.novel}

@app.post('/api/volumes')
def create_volume(req: CreateVolumeRequest):
    vol_dir = safe_path(f'{req.novel}/{req.volume}')
    vol_dir.mkdir(parents=True, exist_ok=True)
    (vol_dir / 'images').mkdir(exist_ok=True)
    target_main = vol_dir / 'main.md'
    if not target_main.exists():
        novel_dir = safe_path(req.novel)
        existing_vols = []
        if novel_dir.exists():
            for item in novel_dir.iterdir():
                if item.is_dir() and item.name != req.volume:
                    if (item / 'main.md').exists():
                        existing_vols.append(item.name)
        if existing_vols:
            import re

            def sort_key(name):
                nums = re.findall('\\d+', name)
                return int(nums[-1]) if nums else 0
            existing_vols.sort(key=sort_key)
            prev_main = novel_dir / existing_vols[-1] / 'main.md'
            content = prev_main.read_text(encoding='utf-8')
            content = re.sub('Table of Content\\[[\\s\\S]*', 'Table of Content[\n]\n', content)
            content = re.sub('^Volume\\s*:\\s*\\[.*?\\]', 'Volume: []', content, flags=re.MULTILINE)
            target_main.write_text(content, encoding='utf-8')
        else:
            blank = BASE_DIR / 'main.md'
            if blank.exists():
                shutil.copy(str(blank), str(target_main))
            else:
                content = f'# Main\n\nTitle Japan: []\nTitle Indonesia: []\nTitle Inggris : []\nTitle Romanji: []\nVolume: []\nAuthor: []\nArtist: []\nGenres: []\nTranslator: []\nEPUB Compiler : [TakoYune]\nPrimary Title: [id]\n\nCover : []\n\nTable of Content[\n]\n'
                target_main.write_text(content, encoding='utf-8')
    return {'ok': True}

@app.delete('/api/delete')
def delete_item(req: DeleteRequest):
    p = safe_path(req.path)
    if not p.exists():
        raise HTTPException(404, 'Not found')
    if p.is_dir():
        shutil.rmtree(str(p))
    else:
        p.unlink()
    return {'ok': True}

@app.post('/api/rename')
def rename_item(req: RenameRequest):
    src = safe_path(req.old_path)
    dst = safe_path(req.new_path)
    if not src.exists():
        raise HTTPException(404, 'Source not found')
    src.rename(dst)
    return {'ok': True}

@app.get('/api/md')
def read_md(path: str):
    """Read any .md file. path is relative to BASE_DIR."""
    p = safe_path(path)
    if not p.exists():
        return {'content': ''}
    return {'content': p.read_text(encoding='utf-8')}

@app.post('/api/md')
def save_md(req: SaveMdRequest):
    p = safe_path(req.path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with file_save_lock:
        p.write_text(req.content, encoding='utf-8')
    return {'ok': True}

@app.post('/api/md/new')
def new_md_file(path: str=Form(...)):
    p = safe_path(path)
    if p.exists():
        raise HTTPException(400, 'File already exists')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('', encoding='utf-8')
    return {'ok': True}

@app.post('/api/images/upload')
async def upload_image(file: UploadFile=File(...), novel: str=Form(...), volume: str=Form(...)):
    vol_dir = safe_path(f'{novel}/{volume}')
    img_dir = vol_dir / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub('[^\\w\\-.]', '_', file.filename)
    dest = img_dir / safe_name
    with open(str(dest), 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {'ok': True, 'filename': safe_name, 'path': f'{novel}/{volume}/images/{safe_name}'}

@app.get('/api/images/serve')
def serve_image(path: str):
    """Serve an image file by relative path."""
    p = safe_path(path)
    if not p.exists():
        raise HTTPException(404, 'Image not found')
    return FileResponse(str(p))

@app.post('/api/scrape')
def scrape_url(req: ScrapeRequest):
    """Scrape a web URL and save as .md in the target volume folder."""
    import requests as req_lib
    from bs4 import BeautifulSoup
    import markdownify
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    try:
        if req.html_content:
            soup = BeautifulSoup(req.html_content, 'html.parser')
        else:
            response = req_lib.get(req.url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', class_='entry-content')
        if not content:
            content = soup.find('article')
        if not content:
            content = soup.body
        for tag in content(['script', 'style', 'nav', 'footer', 'iframe']):
            tag.decompose()
        for div in content.find_all('div', class_=['sharedaddy', 'jp-relatedposts']):
            div.decompose()
        import base64
        for canvas in content.find_all('canvas', class_='kdt-img-canvas'):
            data_kdt = canvas.get('data-kdt')
            if data_kdt:
                try:
                    decoded_url = base64.b64decode(data_kdt).decode('utf-8')[::-1]
                    new_img = soup.new_tag('img', src=decoded_url, alt='Illustration')
                    canvas.replace_with(new_img)
                except Exception:
                    pass
        for img in content.find_all('img'):
            src = img.get('src') or ''
            if not src or src.startswith('data:image'):
                real_src = img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                if real_src:
                    img['src'] = real_src
        html_str = str(content)
        md_text = markdownify.markdownify(html_str, heading_style='ATX')
        md_text = re.sub('\\n{3,}', '\n\n', md_text).strip()
        fname = req.filename if req.filename.endswith('.md') else req.filename + '.md'
        fname = re.sub('[\\\\/*?:"<>|]', '_', fname)
        out_path = safe_path(f'{req.novel}/{req.volume}/{fname}')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_text, encoding='utf-8')
        return {'ok': True, 'filename': fname, 'chars': len(md_text)}
    except Exception as e:
        raise HTTPException(500, f'Scrape error: {e}')

@app.post('/api/build')
def build_epub(req: BuildRequest):
    """Run build_novel.py for a specific volume folder."""
    vol_dir = safe_path(f'{req.novel}/{req.volume}')
    if not vol_dir.is_dir():
        raise HTTPException(404, 'Volume folder not found')
    build_script = str(BASE_DIR / 'build_novel.py')
    cmd = [PYTHON, build_script, str(vol_dir)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300, cwd=str(BASE_DIR))
        stdout = result.stdout or ''
        stderr = result.stderr or ''
        success = result.returncode == 0
        epub_path = None
        for line in stdout.splitlines():
            if line.strip().endswith('.epub'):
                epub_path = line.strip()
        return {'ok': success, 'stdout': stdout, 'stderr': stderr, 'epub_path': epub_path, 'returncode': result.returncode}
    except subprocess.TimeoutExpired:
        raise HTTPException(504, 'Build timed out after 300 seconds')
    except Exception as e:
        raise HTTPException(500, f'Build error: {e}')

@app.get('/api/settings')
def get_settings():
    return read_settings()

@app.post('/api/settings')
def post_settings(req: SettingsRequest):
    write_settings(req.settings)
    return {'ok': True}

@app.post('/api/logs')
def post_log(req: LogRequest):
    log_event(req.level, req.message)
    return {'ok': True}

@app.get('/api/logs')
def get_logs():
    log_file = BASE_DIR / 'narrative_os.log'
    if not log_file.exists():
        return {'logs': 'No logs yet.'}
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return {'logs': f.read()}
    except Exception as e:
        return {'logs': f'Error reading logs: {e}'}

@app.get('/api/mainmd')
def get_mainmd(novel: str, volume: str):
    p = safe_path(f'{novel}/{volume}/main.md')
    if p.exists():
        return {'content': p.read_text(encoding='utf-8')}
    novel_dir = safe_path(novel)
    existing_vols = []
    if novel_dir.exists():
        for item in novel_dir.iterdir():
            if item.is_dir() and item.name != volume:
                if (item / 'main.md').exists():
                    existing_vols.append(item.name)
    if existing_vols:
        import re

        def sort_key(name):
            nums = re.findall('\\d+', name)
            return int(nums[-1]) if nums else 0
        existing_vols.sort(key=sort_key)
        prev_main = novel_dir / existing_vols[-1] / 'main.md'
        content = prev_main.read_text(encoding='utf-8')
        content = re.sub('Table of Content\\[[\\s\\S]*', 'Table of Content[\n]\n', content)
        content = re.sub('^Volume\\s*:\\s*\\[.*?\\]', 'Volume: []', content, flags=re.MULTILINE)
        return {'content': content}
    blank = BASE_DIR / 'main.md'
    if blank.exists():
        return {'content': blank.read_text(encoding='utf-8')}
    content = f'# Main\n\nTitle Japan: []\nTitle Indonesia: []\nTitle Inggris : []\nTitle Romanji: []\nVolume: []\nAuthor: []\nArtist: []\nGenres: []\nTranslator: []\nEPUB Compiler : [TakoYune]\nPrimary Title: [id]\n\nCover : []\n\nTable of Content[\n]\n'
    return {'content': content}

@app.post('/api/mainmd')
def save_mainmd(req: SaveMdRequest):
    p = safe_path(req.path)
    with file_save_lock:
        p.write_text(req.content, encoding='utf-8')
    return {'ok': True}

class BatchScrapeRequest(BaseModel):
    urls: list
    novel: str
    volume: str

@app.post('/api/scrape/batch')
def batch_scrape(req: BatchScrapeRequest):
    results = []
    for item in req.urls:
        single = ScrapeRequest(url=item.get('url', ''), novel=req.novel, volume=req.volume, filename=item.get('filename', 'chapter.md'))
        try:
            r = scrape_url(single)
            results.append({'filename': single.filename, 'ok': True, 'chars': r.get('chars', 0)})
        except Exception as e:
            results.append({'filename': single.filename, 'ok': False, 'error': str(e)})
    return {'results': results}