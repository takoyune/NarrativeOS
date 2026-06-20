import { openInEditor, loadVolumesForSelect } from './library.js';
import { state } from '../core/state.js';
import { api, GET, POST, DEL } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from '../core/utils.js';


let batchUrls = []; 
export function initScraperPanel() {
  populateSelect('scraper-novel', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('scraper-novel').value = state.selectedNovel;
    scraperNovelChange();
  }
}
export async function scraperNovelChange() {
  await loadVolumesForSelect('scraper-novel', 'scraper-volume');
}
export function logScrape(msg, cls = '') {
  const log = document.getElementById('scrape-log');
  const line = document.createElement('span');
  if (cls) line.className = `log-${cls}`;
  line.innerHTML = msg + '\n';
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}
document.getElementById('btn-scrape-single').addEventListener('click', async () => {
  const url = document.getElementById('scraper-url').value.trim();
  const novel = document.getElementById('scraper-novel').value;
  const volume = document.getElementById('scraper-volume').value;
  const filename = document.getElementById('scraper-filename').value.trim() || 'chapter.md';
  if (!url || !novel || !volume) {
    toast('Fill in URL, novel, and volume', 'error'); return;
  }
  const btn = document.getElementById('btn-scrape-single');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Scraping…';
  logScrape(`→ Scraping: ${url}`, 'info');
  try {
    const res = await POST('/api/scrape', { url, novel, volume, filename });
    logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>Saved as "${res.filename}" (${res.chars} chars)`, 'ok');
    toast(`Scraped → ${res.filename}`, 'success');
    document.getElementById('scraper-url').value = '';
  } catch (e) {
    logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>Error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>Scrape Chapter';
  }
});
export function renderBatchList() {
  const container = document.getElementById('batch-url-list');
  container.innerHTML = '';
  batchUrls.forEach((item, i) => {
    const row = document.createElement('div');
    row.className = 'batch-url-item';
    row.innerHTML = `
      <input class="input" style="font-size:12px" value="${item.url}" placeholder="URL" data-idx="${i}" data-field="url">
      <input class="input" style="width:140px;font-size:12px" value="${item.filename}" placeholder="Chapter N.md" data-idx="${i}" data-field="filename">
      <button class="btn btn-danger btn-sm" data-rm="${i}">✕</button>
    `;
    row.querySelectorAll('input').forEach(inp => {
      inp.addEventListener('input', () => {
        batchUrls[parseInt(inp.dataset.idx)][inp.dataset.field] = inp.value;
      });
    });
    row.querySelector('[data-rm]').addEventListener('click', () => {
      batchUrls.splice(i, 1);
      renderBatchList();
    });
    container.appendChild(row);
  });
}
document.getElementById('btn-add-url').addEventListener('click', () => {
  batchUrls.push({ url: '', filename: `Chapter ${batchUrls.length + 1}.md` });
  renderBatchList();
});
document.getElementById('btn-scrape-batch').addEventListener('click', async () => {
  const novel = document.getElementById('scraper-novel').value;
  const volume = document.getElementById('scraper-volume').value;
  if (!novel || !volume) { toast('Select novel and volume', 'error'); return; }
  const valid = batchUrls.filter(u => u.url.trim());
  if (!valid.length) { toast('Add at least one URL', 'error'); return; }
  const btn = document.getElementById('btn-scrape-batch');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Scraping…';
  logScrape(`\n→ Batch scrape: ${valid.length} URLs`, 'info');
  try {
    const response = await fetch('/api/scrape/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': window.API_KEY || '' },
      body: JSON.stringify({ urls: valid, novel, volume })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || response.statusText);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep the last incomplete line
      
      for (const line of lines) {
        if (!line.trim()) continue;
        const r = JSON.parse(line);
        if (r.ok) logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>[${r.progress}] ${r.filename} (${r.chars} chars)`, 'ok');
        else      logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>[${r.progress}] ${r.filename}: ${r.error}`, 'err');
      }
    }
    toast(`Batch done: ${valid.length} chapters`, 'success');
  } catch (e) {
    logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>Batch error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Scrape All';
  }
});
document.getElementById('btn-parse-html').addEventListener('click', () => openModal('modal-html-paste'));
document.getElementById('btn-paste-cancel').addEventListener('click', () => closeModal('modal-html-paste'));
document.getElementById('btn-paste-confirm').addEventListener('click', () => {
  const html = document.getElementById('html-paste-input').value;
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const links = doc.querySelectorAll('a[href]');
  let count = 0;
  links.forEach(a => {
    const url = a.href;
    if (!url || url === '#') return;
    const text = a.textContent.trim();
    const filename = text ? text + '.md' : `Chapter ${batchUrls.length + 1}.md`;
    batchUrls.push({ url, filename });
    count++;
  });
  renderBatchList();
  closeModal('modal-html-paste');
  document.getElementById('html-paste-input').value = '';
  toast(`Extracted ${count} URLs`, 'success');
});
document.getElementById('btn-confirm-scrape-html').addEventListener('click', async () => {
  const htmlContent = document.getElementById('scrape-html-input').value.trim();
  if (!htmlContent) return toast('HTML is empty', 'error');
  const novel = document.getElementById('scraper-novel').value;
  const volume = document.getElementById('scraper-volume').value;
  const filename = document.getElementById('scraper-filename').value.trim();
  if (!novel || !volume || !filename) return toast('Missing novel/volume/filename', 'error');
  const btn = document.getElementById('btn-confirm-scrape-html');
  btn.disabled = true;
  btn.textContent = 'Scraping...';
  try {
    const res = await POST('/api/scrape', { url: "local-html", novel, volume, filename, html_content: htmlContent });
    logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>${res.filename} (${res.chars} chars)`, 'ok');
    toast(`Scraped: ${res.filename}`, 'success');
    closeModal('modal-scrape-html');
    document.getElementById('scrape-html-input').value = '';
    openInEditor(novel, volume, res.filename);
  } catch (e) {
    logScrape(`<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>HTML Scrape error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>Paste HTML';
  }
});
