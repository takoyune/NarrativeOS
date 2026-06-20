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
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Path as FastAPIPath
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from utils import pin_dns, get_safe_ip_and_host, BLANK_MAIN_MD_TEMPLATE, log_event
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / 'static'
VENV_PYTHON = BASE_DIR / '.venv' / ('Scripts' if os.name == 'nt' else 'bin') / ('python.exe' if os.name == 'nt' else 'python')
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
app = FastAPI(title='NarrativeOS EPUB Toolkit', version='2.0.0')

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["X-API-Key", "Content-Type", "Accept"],
    max_age=3600,
)
STATIC_DIR.mkdir(exist_ok=True)
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

from fastapi import Request, Response
from fastapi.responses import HTMLResponse
import secrets

APP_TOKEN = secrets.token_hex(16)
log_event("info", f"[Security] Generated dynamic API token for this session.")
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # API Authentication
    if request.url.path.startswith("/api/"):
        token = request.headers.get("X-API-Key") or request.query_params.get("token")
        if token != APP_TOKEN:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
            
    response: Response = await call_next(request)
    
    # Secure Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: blob: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; connect-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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
    if '..' in rel or (os.name == 'nt' and ':' in rel):
        raise HTTPException(status_code=403, detail='Invalid path characters')
        
    try:
        p = (BASE_DIR / rel).resolve(strict=False)
    except Exception:
        raise HTTPException(status_code=400, detail='Path resolution failed')
        
    # Strict bounds checking using pathlib.Path.is_relative_to (Python 3.9+)
    # Fallback to absolute string comparison if needed
    p_str = str(p)
    base_str = str(BASE_DIR)
    if not p_str.startswith(base_str) or (len(p_str) > len(base_str) and p_str[len(base_str)] not in ['\\', '/']):
        raise HTTPException(status_code=403, detail='Path traversal denied')
        
    try:
        rel_parts = p.relative_to(BASE_DIR).parts
        if rel_parts:
            # Block access to system and hidden directories
            if rel_parts[0] in ['static', '.venv', '__pycache__', '.git', 'scratch', '.agent', '.agents'] or rel_parts[0].startswith('.'):
                raise HTTPException(status_code=403, detail='Access to system directories denied')
            # Block executable and critical file access at the root level
            if len(rel_parts) == 1 and p.suffix.lower() in ['.py', '.ini', '.log', '.bat', '.sh', '.exe', '.dll', '.json']:
                raise HTTPException(status_code=403, detail='Access to core application files denied')
    except ValueError:
        pass
    return p

def _sort_key_volumes(name: str) -> int:
    nums = re.findall(r'\d+', name)
    return int(nums[-1]) if nums else 0


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
    with file_save_lock:
        with open(str(BASE_DIR / 'settings.ini'), 'w', encoding='utf-8') as f:
            cfg.write(f)

def list_novels() -> list:
    novels = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and (not item.name.startswith(('.', '_', 'static', 'scratch'))):
            skip = {'.venv', '__pycache__', 'scratch'}
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
    html_content = (STATIC_DIR / 'index.html').read_text(encoding='utf-8')
    injection = f'<script>window.API_KEY = "{APP_TOKEN}";</script>'
    html_content = html_content.replace('<head>', f'<head>\n  {injection}')
    return HTMLResponse(content=html_content)

@app.get('/api/novels')
def get_novels():
    return {'novels': list_novels()}

@app.get('/api/novels/{novel}/volumes')
def get_volumes(novel: str = FastAPIPath(..., pattern=r'^[^/\\]+$')):
    return {'volumes': list_volumes(novel)}

@app.get('/api/novels/{novel}/volumes/{volume}/files')
def get_files(novel: str = FastAPIPath(..., pattern=r'^[^/\\]+$'), volume: str = FastAPIPath(..., pattern=r'^[^/\\]+$')):
    return {'md_files': list_md_files(novel, volume), 'images': list_images(novel, volume)}

@app.post('/api/novels')
def create_novel(req: CreateNovelRequest):
    d = safe_path(req.novel)
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
            existing_vols.sort(key=_sort_key_volumes)
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
                target_main.write_text(BLANK_MAIN_MD_TEMPLATE, encoding='utf-8')
    return {'ok': True}

@app.delete('/api/delete')
def delete_item(req: DeleteRequest):
    p = safe_path(req.path)
    if not p.exists():
        raise HTTPException(404, 'Not found')
        
    try:
        rel_parts = p.relative_to(BASE_DIR).parts
        if not rel_parts or rel_parts[0] not in list_novels():
            raise HTTPException(403, 'Can only delete items inside a novel directory')
    except ValueError:
        raise HTTPException(403, 'Invalid path')

    if p.is_dir():
        shutil.rmtree(str(p))
    else:
        p.unlink()
    log_event("info", f"SECURITY AUDIT: File/Directory deleted -> {p}")
    return {'ok': True}

@app.post('/api/rename')
def rename_item(req: RenameRequest):
    src = safe_path(req.old_path)
    dst = safe_path(req.new_path)
    
    try:
        src_parts = src.relative_to(BASE_DIR).parts
        if not src_parts or src_parts[0] not in list_novels():
            raise HTTPException(403, 'Can only rename items inside a novel directory')
        dst_parts = dst.relative_to(BASE_DIR).parts
        if not dst_parts or dst_parts[0] not in list_novels():
            raise HTTPException(403, 'Can only rename items into a novel directory')
    except ValueError:
        raise HTTPException(403, 'Invalid path')
        
    if not src.exists():
        raise HTTPException(404, 'Source not found')
    src.rename(dst)
    log_event("info", f"SECURITY AUDIT: File/Directory renamed -> {src} to {dst}")
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
    if p.suffix.lower() != '.md':
        raise HTTPException(403, 'Only .md files allowed')
    rel_parts = p.relative_to(BASE_DIR).parts
    if not rel_parts or rel_parts[0] not in list_novels():
        raise HTTPException(403, 'Must be inside a novel directory')
    p.parent.mkdir(parents=True, exist_ok=True)
    with file_save_lock:
        p.write_text(req.content, encoding='utf-8')
    print(f"SECURITY AUDIT: File written -> {p}")
    return {'ok': True}

@app.post('/api/md/new')
def new_md_file(path: str=Form(...)):
    p = safe_path(path)
    if p.suffix.lower() != '.md':
        raise HTTPException(403, 'Only .md files allowed')
    rel_parts = p.relative_to(BASE_DIR).parts
    if not rel_parts or rel_parts[0] not in list_novels():
        raise HTTPException(403, 'Must be inside a novel directory')
    if p.exists():
        raise HTTPException(400, 'File already exists')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('', encoding='utf-8')
    print(f"SECURITY AUDIT: New file created -> {p}")
    return {'ok': True}

@app.post('/api/images/upload')
async def upload_image(file: UploadFile=File(...), novel: str=Form(...), volume: str=Form(...)):
    if novel not in list_novels():
        raise HTTPException(403, 'Must upload into an existing novel')
        
    file.file.seek(0, 2)
    if file.file.tell() > 10 * 1024 * 1024:
        raise HTTPException(413, 'File too large (max 10MB)')
        
    file.file.seek(0)
    magic = file.file.read(12)
    is_image = False
    if magic.startswith(b'\\xff\\xd8\\xff'): is_image = True
    elif magic.startswith(b'\\x89PNG\\r\\n\\x1a\\n'): is_image = True
    elif magic.startswith(b'GIF8'): is_image = True
    elif magic.startswith(b'RIFF') and magic[8:12] == b'WEBP': is_image = True
    if not is_image:
        raise HTTPException(403, 'Invalid image file content')
    file.file.seek(0)
    
    vol_dir = safe_path(f'{novel}/{volume}')
    img_dir = vol_dir / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)
    base = Path(file.filename).stem
    ext = Path(file.filename).suffix.lower()
    safe_base = re.sub('[^\\w\\-]', '_', base)
    safe_name = f"{safe_base}{ext}"
    if Path(safe_name).suffix.lower() not in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
        raise HTTPException(403, 'Only image files allowed')
    dest = img_dir / safe_name
    with open(str(dest), 'wb') as f:
        shutil.copyfileobj(file.file, f)
    log_event("info", f"SECURITY AUDIT: Image uploaded -> {dest}")
    return {'ok': True, 'filename': safe_name, 'path': f'{novel}/{volume}/images/{safe_name}'}

@app.get('/api/images/serve')
def serve_image(path: str):
    """Serve an image file by relative path."""
    p = safe_path(path)
    if not p.exists():
        raise HTTPException(404, 'Image not found')
    return FileResponse(str(p))

@app.get('/api/epub/serve')
def serve_epub(path: str):
    """Serve an EPUB file by relative path."""
    p = safe_path(path)
    if not p.exists() or p.suffix.lower() != '.epub':
        raise HTTPException(404, 'EPUB not found')
    return FileResponse(str(p), media_type='application/epub+zip')

@app.post('/api/scrape')
def scrape_url(req: ScrapeRequest):
    """Scrape a web URL and save as .md in the target volume folder."""
    ip_str, host = get_safe_ip_and_host(req.url)
    if not ip_str:
        raise HTTPException(status_code=403, detail="SSRF protection: URL resolves to internal IP")
        
    from scrapling.fetchers import StealthyFetcher
    from bs4 import BeautifulSoup
    import markdownify
    try:
        if req.html_content:
            soup = BeautifulSoup(req.html_content, 'html.parser')
        else:
            with pin_dns(host, ip_str):
                # StealthyFetcher bypasses Cloudflare automatically
                page = StealthyFetcher.fetch(req.url, headless=True)
            soup = BeautifulSoup(page.body, 'html.parser')
            
        # Try to find the main content container robustly
        possible_classes = [
            'entry-content', 'post-content', 'chapter-content', 'read-container', 
            'bs-card-box', 'text-left', 'chapter-body', 'novel-content', 'content-area'
        ]
        content = None
        for cls in possible_classes:
            elements = soup.find_all(class_=cls)
            if elements:
                best_el = max(elements, key=lambda e: len(e.get_text(strip=True)))
                if len(best_el.get_text(strip=True)) > 200:
                    content = best_el
                    break
                    
        if not content:
            content = soup.find('article')
        if not content:
            content = soup.find('main')
        if not content:
            content = soup.body
        if not content:
            raise ValueError("Could not find any readable content on the page.")
            
        for tag in content.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
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
        fname = re.sub('[\\\\/*?:"<>|]', '_', fname).replace('..', '')
        out_path = safe_path(f'{req.novel}/{req.volume}/{fname}')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_text, encoding='utf-8')
        return {'ok': True, 'filename': fname, 'chars': len(md_text)}
    except Exception as e:
        print(f"Scrape error: {e}")
        raise HTTPException(500, 'An internal error occurred while scraping.')

build_lock = threading.Lock()

@app.post('/api/build')
def build_epub(req: BuildRequest):
    """Run build_novel.py for a specific volume folder."""
    if not build_lock.acquire(blocking=False):
        raise HTTPException(429, 'A build is already in progress, please wait.')
    try:
        vol_dir = safe_path(f'{req.novel}/{req.volume}')
        if not vol_dir.is_dir():
            raise HTTPException(404, 'Volume folder not found')
        build_script = str(BASE_DIR / 'build_novel.py')
        cmd = [PYTHON, build_script, str(vol_dir)]
        
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
        log_event("error", f"Build error: {e}")
        raise HTTPException(500, 'An internal error occurred while building.')
    finally:
        build_lock.release()

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
        existing_vols.sort(key=_sort_key_volumes)
        prev_main = novel_dir / existing_vols[-1] / 'main.md'
        content = prev_main.read_text(encoding='utf-8')
        content = re.sub('Table of Content\\[[\\s\\S]*', 'Table of Content[\n]\n', content)
        content = re.sub('^Volume\\s*:\\s*\\[.*?\\]', 'Volume: []', content, flags=re.MULTILINE)
        return {'content': content}
    blank = BASE_DIR / 'main.md'
    if blank.exists():
        return {'content': blank.read_text(encoding='utf-8')}
    return {'content': BLANK_MAIN_MD_TEMPLATE}

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
    if len(req.urls) > 30:
        raise HTTPException(429, 'Too many URLs to scrape at once (max 30)')
    def generator():
        for i, item in enumerate(req.urls, 1):
            single = ScrapeRequest(url=item.get('url', ''), novel=req.novel, volume=req.volume, filename=item.get('filename', 'chapter.md'))
            try:
                r = scrape_url(single)
                res = {'filename': single.filename, 'ok': True, 'chars': r.get('chars', 0), 'progress': f'{i}/{len(req.urls)}'}
            except Exception as e:
                res = {'filename': single.filename, 'ok': False, 'error': str(e), 'progress': f'{i}/{len(req.urls)}'}
            yield json.dumps(res) + '\n'
            
    return StreamingResponse(generator(), media_type="application/x-ndjson")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8765, reload=False)