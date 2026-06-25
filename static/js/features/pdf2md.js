import { loadLibrary } from './library.js';
import { GET } from '../core/api.js';

export function initPdf2mdPanel() {
  document.getElementById('pdf2md-novel').addEventListener('change', pdf2mdNovelChange);
  document.getElementById('btn-convert-pdf').addEventListener('click', convertPdf);

  const dropzone = document.getElementById('pdf2md-dropzone');
  const fileInput = document.getElementById('pdf2md-file');
  const dzText = document.getElementById('pdf2md-dz-text');

  dropzone.addEventListener('click', (e) => {
    if (e.target !== fileInput) {
      fileInput.click();
    }
  });
  dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      dzText.innerHTML = `<span style="color:var(--accent);font-weight:600;">Selected: ${e.dataTransfer.files[0].name}</span>`;
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      dzText.innerHTML = `<span style="color:var(--accent);font-weight:600;">Selected: ${fileInput.files[0].name}</span>`;
    }
  });
}

function log(msg, type = 'info') {
  const el = document.getElementById('pdf2md-log');
  
  let icon = '';
  if (type === 'error') {
    icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" style="flex-shrink:0;margin-right:6px;"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
  } else if (type === 'wait') {
    icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-right:6px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>';
  } else if (type === 'success') {
    icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" style="flex-shrink:0;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
  } else if (type === 'refresh') {
    icon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-right:6px;"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>';
  } else {
    icon = '<span style="display:inline-block;width:20px;flex-shrink:0;"></span>';
  }

  if (el.textContent.includes('Processing output will appear here...')) {
    el.innerHTML = '';
  }

  const line = document.createElement('div');
  line.style.display = 'flex';
  line.style.alignItems = 'flex-start';
  line.style.marginBottom = '4px';
  line.innerHTML = `${icon}<span style="white-space:pre-wrap;word-break:break-word;">${msg}</span>`;
  
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

export async function pdf2mdNovelChange() {
  const nv = document.getElementById('pdf2md-novel').value;
  const volSelect = document.getElementById('pdf2md-volume');
  volSelect.innerHTML = '';
  if (!nv) return;
  try {
    const res = await GET(`/api/novels/${encodeURIComponent(nv)}/volumes`);
    res.volumes.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v;
      volSelect.appendChild(opt);
    });
  } catch (e) {
    console.error(e);
  }
}

export async function convertPdf() {
  const novel = document.getElementById('pdf2md-novel').value;
  const volume = document.getElementById('pdf2md-volume').value;
  const fileInput = document.getElementById('pdf2md-file');
  const file = fileInput.files[0];

  if (!novel || !volume) {
    log('Error: Please select a novel and volume.', 'error');
    return;
  }
  if (!file) {
    log('Error: Please select a PDF file.', 'error');
    return;
  }

  log(`Starting conversion for ${file.name}...`, 'wait');
  log(`Target: ${novel} / ${volume}`, 'info');
  
  const formData = new FormData();
  formData.append('novel', novel);
  formData.append('volume', volume);
  formData.append('file', file);

  try {
    document.getElementById('btn-convert-pdf').disabled = true;
    
    const res = await fetch('/api/pdf2md', {
      method: 'POST',
      headers: { 'X-API-Key': window.API_KEY || '' },
      body: formData
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    
    const data = await res.json();
    log(`Success: ${data.message}`, 'success');
    log('Refreshing library...', 'refresh');
    await loadLibrary();
  } catch (e) {
    log(`Error: ${e.message}`, 'error');
  } finally {
    document.getElementById('btn-convert-pdf').disabled = false;
  }
}
