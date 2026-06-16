/* ═══════════════════════════════════════════════════════════════
   NarrativeOS EPUB Toolkit — app.js
   Full application logic for the local web interface.
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── Global state ─────────────────────────────────────────────────
const state = {
  novels: [],
  selectedNovel: null,
  selectedVolume: null,
  currentMdPath: null,
  mdDirty: false,
  currentPanel: 'overview',
  images: [],
};

// ── API helpers ───────────────────────────────────────────────────
async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

const GET  = (url)        => api('GET', url);
const POST = (url, body)  => api('POST', url, body);
const DEL  = (url, body)  => api('DELETE', url, body);

async function sendLog(level, message) {
  try {
    await fetch('/api/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level, message })
    });
  } catch(e) {}
}

// ── Toast notifications ───────────────────────────────────────────
function toast(msg, type = 'info', duration = 3500) {
  if (type === 'error' || type === 'success') {
    sendLog(type, msg);
  }
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => {
    el.classList.add('hiding');
    setTimeout(() => el.remove(), 350);
  }, duration);
}

// ── Panel navigation ──────────────────────────────────────────────
function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`panel-${name}`)?.classList.add('active');
  document.getElementById(`nav-${name}`)?.classList.add('active');
  state.currentPanel = name;

  // Panel-specific init
  if (name === 'scraper')  initScraperPanel();
  if (name === 'editor')   initEditorPanel();
  if (name === 'images')   initImagesPanel();
  if (name === 'metadata') initMetaPanel();
  if (name === 'builder')  initBuilderPanel();
  if (name === 'settings') initSettingsPanel();
}

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => showPanel(item.dataset.panel));
});

// ── Modal helpers ─────────────────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  openModal('modal-lightbox');
}

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});

// ══════════════════════════════════════════════════════════════════
// LIBRARY  — Load novels and build sidebar tree
// ══════════════════════════════════════════════════════════════════
async function loadLibrary() {
  try {
    const data = await GET('/api/novels');
    state.novels = data.novels || [];
    renderLibraryTree();
    updateStats();
    populateAllSelects();
  } catch (e) {
    toast('Failed to load library: ' + e.message, 'error');
  }
}

function renderLibraryTree() {
  const tree = document.getElementById('library-tree');
  if (!state.novels.length) {
    tree.innerHTML = '<div class="text-muted text-sm" style="padding:8px">No novels found</div>';
    return;
  }

  tree.innerHTML = '';
  state.novels.forEach(novel => {
    const novelEl = document.createElement('div');
    novelEl.innerHTML = `
      <div class="tree-item" data-novel="${novel}" id="tree-novel-${CSS.escape(novel)}">
        <span class="ti">📚</span>
        <span class="label">${novel}</span>
      </div>
      <div class="tree-children hidden" id="tree-children-${CSS.escape(novel)}"></div>
    `;
    tree.appendChild(novelEl);

    novelEl.querySelector('.tree-item').addEventListener('click', async () => {
      const childrenEl = document.getElementById(`tree-children-${CSS.escape(novel)}`);
      if (childrenEl.classList.contains('hidden')) {
        childrenEl.classList.remove('hidden');
        await loadVolumesInTree(novel, childrenEl);
      } else {
        childrenEl.classList.add('hidden');
      }
    });
  });
}

async function loadVolumesInTree(novel, container) {
  container.innerHTML = '<div class="tree-item text-muted text-sm"><span class="ti">⋯</span>Loading…</div>';
  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes`);
    container.innerHTML = '';
    (data.volumes || []).forEach(vol => {
      const el = document.createElement('div');
      el.className = 'tree-item';
      el.dataset.novel = novel;
      el.dataset.volume = vol;
      el.innerHTML = `<span class="ti">📖</span><span class="label">${vol}</span>`;
      el.addEventListener('click', () => selectVolume(novel, vol));
      container.appendChild(el);
    });
    if (!data.volumes?.length) {
      container.innerHTML = '<div class="tree-item text-muted text-sm" style="padding-left:8px"><span class="ti">📭</span> No volumes</div>';
    }
  } catch (e) {
    container.innerHTML = `<div class="tree-item" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

async function updateStats() {
  document.getElementById('stat-novels').textContent = state.novels.length;
  let totalVols = 0, totalFiles = 0, totalImgs = 0;
  for (const novel of state.novels.slice(0, 10)) {
    try {
      const vdata = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes`);
      const vols = vdata.volumes || [];
      totalVols += vols.length;
      for (const vol of vols.slice(0, 5)) {
        try {
          const fdata = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(vol)}/files`);
          totalFiles += (fdata.md_files || []).length;
          totalImgs += (fdata.images || []).length;
        } catch {}
      }
    } catch {}
  }
  document.getElementById('stat-volumes').textContent = totalVols;
  document.getElementById('stat-files').textContent = totalFiles;
  document.getElementById('stat-images').textContent = totalImgs;
}

async function selectVolume(novel, volume) {
  state.selectedNovel = novel;
  state.selectedVolume = volume;

  // Highlight in tree
  document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
  document.querySelectorAll(`[data-novel="${novel}"][data-volume="${volume}"]`).forEach(el => el.classList.add('selected'));

  // Update breadcrumb
  document.getElementById('breadcrumb').innerHTML =
    `<span>${novel}</span> / <span>${volume}</span>`;

  // Show volume info on overview
  showVolumeInfo(novel, volume);

  // Sync all selects
  syncSelectsTo(novel, volume);
}

async function showVolumeInfo(novel, volume) {
  document.getElementById('no-selection').classList.add('hidden');
  const infoEl = document.getElementById('volume-info');
  infoEl.classList.remove('hidden');
  document.getElementById('vi-title').textContent = volume;

  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
    const files = data.md_files || [];
    const fileListEl = document.getElementById('vi-files');
    fileListEl.innerHTML = '';
    files.forEach(f => {
      const row = document.createElement('div');
      row.className = 'file-row';
      row.innerHTML = `
        <span class="fr-icon">${f === 'main.md' ? '📋' : '📝'}</span>
        <span class="fr-name">${f}</span>
        <div class="fr-actions">
          <button class="btn btn-ghost btn-sm" title="Open in editor" onclick="openInEditor('${novel}','${volume}','${f}')">✏️</button>
        </div>
      `;
      row.addEventListener('click', () => openInEditor(novel, volume, f));
      fileListEl.appendChild(row);
    });
    if (!files.length) {
      fileListEl.innerHTML = '<div class="text-muted text-sm" style="padding:8px">No markdown files yet</div>';
    }
  } catch (e) {
    toast('Error loading files: ' + e.message, 'error');
  }
}

// [Bug 3 fix] Refactor to use async/await instead of a fragile setTimeout
async function openInEditor(novel, volume, filename) {
  state.selectedNovel = novel;
  state.selectedVolume = volume;
  
  showPanel('editor');
  syncSelectsTo(novel, volume);
  
  await editorVolumeChange();
  setSelectValue('editor-file-select', filename);
  await editorFileChange();
}

// ══════════════════════════════════════════════════════════════════
// SELECT HELPERS — keep all dropdowns in sync
// ══════════════════════════════════════════════════════════════════
function populateSelect(selectId, items, emptyLabel = '—') {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  const prev = sel.value;
  
  // 1. Populate native select (hidden)
  sel.innerHTML = `<option value="">— ${emptyLabel} —</option>` +
    items.map(i => `<option value="${i.replace(/"/g, '&quot;')}">${i}</option>`).join('');
  if (items.includes(prev)) sel.value = prev;

  // 2. Hide native select
  sel.style.display = 'none';

  // 3. Remove existing wrapper if any
  let wrapper = sel.nextElementSibling;
  if (wrapper && wrapper.classList.contains('custom-select-wrapper')) {
    wrapper.remove();
  }

  // 4. Build Custom UI
  wrapper = document.createElement('div');
  wrapper.className = 'custom-select-wrapper';
  
  const input = document.createElement('input');
  input.className = 'custom-select-input';
  input.type = 'text';
  input.placeholder = `— ${emptyLabel} —`;
  input.value = sel.value || ''; 

  const arrow = document.createElement('div');
  arrow.className = 'custom-select-arrow';
  arrow.innerHTML = '▼';

  const dropdown = document.createElement('div');
  dropdown.className = 'custom-select-dropdown';

  const allOptions = [{ value: '', label: `— ${emptyLabel} —` }, ...items.map(i => ({ value: i, label: i }))];

  const renderDropdown = (filter = '') => {
    dropdown.innerHTML = '';
    const term = filter.toLowerCase();
    const filtered = allOptions.filter(o => o.label.toLowerCase().includes(term));
    
    if (filtered.length === 0) {
      dropdown.innerHTML = '<div class="custom-select-option text-muted" style="pointer-events:none">No matches</div>';
      return;
    }
    
    filtered.forEach(o => {
      const optEl = document.createElement('div');
      optEl.className = 'custom-select-option';
      if (o.value === sel.value) optEl.classList.add('selected');
      optEl.textContent = o.label;
      optEl.addEventListener('mousedown', (e) => { // mousedown fires before blur
        e.preventDefault();
        sel.value = o.value;
        input.value = o.value ? o.label : '';
        dropdown.classList.remove('open');
        sel.dispatchEvent(new Event('change'));
      });
      dropdown.appendChild(optEl);
    });
  };

  input.addEventListener('focus', () => {
    input.value = ''; // clear to allow easy searching
    renderDropdown('');
    dropdown.classList.add('open');
  });

  input.addEventListener('blur', () => {
    dropdown.classList.remove('open');
    // Restore text if they didn't click anything
    const selectedOpt = allOptions.find(o => o.value === sel.value);
    input.value = selectedOpt && selectedOpt.value ? selectedOpt.label : '';
  });

  input.addEventListener('input', () => {
    dropdown.classList.add('open');
    renderDropdown(input.value);
  });

  wrapper.appendChild(input);
  wrapper.appendChild(arrow);
  wrapper.appendChild(dropdown);
  sel.parentNode.insertBefore(wrapper, sel.nextSibling);
}

function populateAllSelects() {
  const ids = ['scraper-novel', 'editor-novel-select', 'img-novel-select',
               'meta-novel-select', 'build-novel-select',
               'new-volume-novel'];
  ids.forEach(id => populateSelect(id, state.novels, 'Select Novel'));

  if (state.selectedNovel) {
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = state.selectedNovel;
    });
  }
}

async function loadVolumesForSelect(novelSelectId, volSelectId) {
  const sel = document.getElementById(novelSelectId);
  const novel = sel?.value;
  if (!novel) {
    populateSelect(volSelectId, [], 'Select Volume');
    return;
  }
  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes`);
    populateSelect(volSelectId, data.volumes || [], 'Select Volume');
    if (state.selectedVolume && (data.volumes || []).includes(state.selectedVolume)) {
      document.getElementById(volSelectId).value = state.selectedVolume;
    }
  } catch {}
}

// [Bug 2 fix] Helper to update both native select and custom UI safely
function setSelectValue(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = val;
  const input = el.nextElementSibling?.querySelector('.custom-select-input');
  if (input) input.value = val;
}

function syncSelectsTo(novel, volume) {
  const novelSelects = ['scraper-novel', 'editor-novel-select', 'img-novel-select',
                        'meta-novel-select', 'build-novel-select'];
  novelSelects.forEach(id => {
    const el = document.getElementById(id);
    if (el && el.value !== novel) setSelectValue(id, novel);
  });
  // Trigger volume loading for each panel
  scraperNovelChange().then(() => setSelectValue('scraper-volume', volume));
  editorNovelChange().then(() => {
    setSelectValue('editor-volume-select', volume);
    editorVolumeChange();
  });
  imgNovelChange().then(() => setSelectValue('img-volume-select', volume));
  metaNovelChange().then(() => setSelectValue('meta-volume-select', volume));
  buildNovelChange().then(() => setSelectValue('build-volume-select', volume));
}

// ══════════════════════════════════════════════════════════════════
// OVERVIEW — quick actions
// ══════════════════════════════════════════════════════════════════
document.getElementById('btn-refresh-lib').addEventListener('click', () => {
  loadLibrary();
  toast('Library refreshed', 'success');
});

document.getElementById('btn-quick-build').addEventListener('click', () => {
  if (!state.selectedNovel || !state.selectedVolume) {
    toast('Select a volume first', 'error'); return;
  }
  showPanel('builder');
  setTimeout(startBuild, 300);
});

document.getElementById('btn-new-novel').addEventListener('click', () => openModal('modal-new-novel'));
document.getElementById('btn-new-volume').addEventListener('click', () => {
  populateSelect('new-volume-novel', state.novels, 'Select Novel');
  if (state.selectedNovel) document.getElementById('new-volume-novel').value = state.selectedNovel;
  openModal('modal-new-volume');
});

document.getElementById('btn-create-novel').addEventListener('click', async () => {
  const name = document.getElementById('new-novel-name').value.trim();
  if (!name) return;
  try {
    await POST('/api/novels', { novel: name });
    closeModal('modal-new-novel');
    document.getElementById('new-novel-name').value = '';
    await loadLibrary();
    toast(`Novel "${name}" created!`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});

document.getElementById('btn-create-volume').addEventListener('click', async () => {
  const novel = document.getElementById('new-volume-novel').value;
  const volume = document.getElementById('new-volume-name').value.trim();
  if (!novel || !volume) return;
  try {
    await POST('/api/volumes', { novel, volume });
    closeModal('modal-new-volume');
    document.getElementById('new-volume-name').value = '';
    await loadLibrary();
    toast(`Volume "${volume}" created!`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});

// ══════════════════════════════════════════════════════════════════
// SCRAPER PANEL
// ══════════════════════════════════════════════════════════════════
let batchUrls = []; // [{url, filename}]

function initScraperPanel() {
  populateSelect('scraper-novel', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('scraper-novel').value = state.selectedNovel;
    scraperNovelChange();
  }
}

async function scraperNovelChange() {
  await loadVolumesForSelect('scraper-novel', 'scraper-volume');
}

function logScrape(msg, cls = '') {
  const log = document.getElementById('scrape-log');
  const line = document.createElement('span');
  if (cls) line.className = `log-${cls}`;
  line.textContent = msg + '\n';
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
    logScrape(`✅ Saved as "${res.filename}" (${res.chars} chars)`, 'ok');
    toast(`Scraped → ${res.filename}`, 'success');
    document.getElementById('scraper-url').value = '';
  } catch (e) {
    logScrape(`❌ Error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🌐 Scrape Chapter';
  }
});

// Batch URL list rendering
function renderBatchList() {
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
    const res = await POST('/api/scrape/batch', { urls: valid, novel, volume });
    (res.results || []).forEach(r => {
      if (r.ok) logScrape(`✅ ${r.filename} (${r.chars} chars)`, 'ok');
      else       logScrape(`❌ ${r.filename}: ${r.error}`, 'err');
    });
    toast(`Batch done: ${valid.length} chapters`, 'success');
  } catch (e) {
    logScrape(`❌ Batch error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Scrape All';
  }
});

// HTML paste modal
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

// Single HTML Scrape
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
    logScrape(`✅ ${res.filename} (${res.chars} chars)`, 'ok');
    toast(`Scraped: ${res.filename}`, 'success');
    closeModal('modal-scrape-html');
    document.getElementById('scrape-html-input').value = '';
    
    // Automatically open the file in the editor so they can see the result
    openInEditor(novel, volume, res.filename);
  } catch (e) {
    logScrape(`❌ HTML Scrape error: ${e.message}`, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Scrape HTML';
  }
});

// ══════════════════════════════════════════════════════════════════
// MARKDOWN EDITOR — with syntax highlighting
// ══════════════════════════════════════════════════════════════════
let previewDebounce = null;

// ── Syntax highlighter ───────────────────────────────────────────
/**
 * Converts a plain text markdown string into HTML with highlight
 * <span> tags. The pre layer renders this while the textarea
 * sits transparently on top.
 */
function highlightMarkdown(text) {
  const esc = s => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Track if we are inside a fenced code block
  let inCode = false;

  const lines = text.split('\n');
  const result = lines.map(rawLine => {
    const line = esc(rawLine);

    // ── Fenced code block toggle
    if (/^```/.test(rawLine)) {
      inCode = !inCode;
      return `<span class="hl-codeblock">${line}</span>`;
    }
    if (inCode) {
      return `<span class="hl-codeblock">${line}</span>`;
    }

    // ── Scene break: line is only ***, ---, or ❖ chars
    if (/^\s*([\*\-]{3,}|❖[\s❖]+)\s*$/.test(rawLine)) {
      return `<span class="hl-scenebrk">${line}</span>`;
    }

    // ── Headings (whole-line color)
    if (/^#{4,}\s/.test(rawLine)) return `<span class="hl-h4">${line}</span>`;
    if (/^###\s/.test(rawLine))    return `<span class="hl-h3">${line}</span>`;
    if (/^##\s/.test(rawLine))     return `<span class="hl-h2">${line}</span>`;
    if (/^#\s/.test(rawLine))      return `<span class="hl-h1">${line}</span>`;

    // ── Blockquote
    if (/^>\s?/.test(rawLine)) return `<span class="hl-blockquote">${line}</span>`;

    // ── Custom tags (whole-line)
    if (/^\[UI\]|^\[\/UI\]/.test(rawLine.trim()))    return `<span class="hl-ui">${line}</span>`;
    if (/^\[stats\]|^\[\/stats\]/i.test(rawLine.trim())) return `<span class="hl-stats">${line}</span>`;

    // ── (thought) tag line
    if (/^\(thought\)/.test(rawLine.trim())) return `<span class="hl-thought">${line}</span>`;

    // ── Horizontal rule (--- or ___)
    if (/^[-_]{3,}\s*$/.test(rawLine)) return `<span class="hl-hr">${line}</span>`;

    // ── List items
    if (/^(\s*[-*+]\s)/.test(rawLine)) {
      // highlight just the bullet marker, rest is inline
      return rawLine.replace(/^(\s*)([-*+])(\s.*)$/, (_, sp, mk, rest) =>
        esc(sp) + `<span class="hl-listbullet">${esc(mk)}</span>` + applyInline(esc(rest))
      );
    }
    if (/^\s*\d+\.\s/.test(rawLine)) {
      return rawLine.replace(/^(\s*)(\d+\.)(\s.*)$/, (_, sp, num, rest) =>
        esc(sp) + `<span class="hl-listnumber">${esc(num)}</span>` + applyInline(esc(rest))
      );
    }

    // ── Normal line — apply inline patterns
    return `<span class="hl-plain">${applyInline(line)}</span>`;
  });

  // trailing newline to avoid textarea/pre height mismatch
  return result.join('\n') + '\n';
}

/**
 * Apply inline markdown spans to an already-HTML-escaped string.
 * Order matters: bold+italic first, then bold, then italic.
 */
function applyInline(s) {
  // Images  ![alt](src)
  s = s.replace(/(!\[([^\]]*?)\]\([^)]*?\))/g,
    (_, m) => `<span class="hl-image">${m}</span>`);
  // Links  [text](url)
  s = s.replace(/(\[[^\]]*?\]\([^)]*?\))/g,
    (_, m) => `<span class="hl-link">${m}</span>`);
  // Bold+italic  ***text***
  s = s.replace(/(\*{3}[^*\n]+?\*{3})/g,
    m => `<span class="hl-boldital">${m}</span>`);
  // Bold  **text**
  s = s.replace(/(\*{2}[^*\n]+?\*{2})/g,
    m => `<span class="hl-bold">${m}</span>`);
  // Italic  *text*
  s = s.replace(/(\*[^*\n]+?\*)/g,
    m => `<span class="hl-italic">${m}</span>`);
  // Inline code  `code`
  s = s.replace(/(`[^`\n]+?`)/g,
    m => `<span class="hl-codeinline">${m}</span>`);
  // (thought) inline
  s = s.replace(/(\(thought\)[^\n]*)/gi,
    m => `<span class="hl-thought">${m}</span>`);
  return s;
}

// ── Scroll Sync (Editor ↔ Preview) ──────────────────
let isSyncingLeft = false;
let isSyncingRight = false;

function syncScroll() {
  if (isSyncingLeft) return;
  isSyncingRight = true;
  
  const ta  = document.getElementById('md-textarea');
  const pre = document.getElementById('editor-highlight-layer');
  const preview = document.getElementById('md-preview');
  const linesEl = document.getElementById('editor-line-numbers');
  
  if (!pre || !ta) return;
  pre.scrollTop  = ta.scrollTop;
  pre.scrollLeft = ta.scrollLeft;
  
  if (linesEl) {
    linesEl.scrollTop = ta.scrollTop;
  }
  
  if (preview && ta.scrollHeight > ta.clientHeight) {
    const scrollPercent = ta.scrollTop / (ta.scrollHeight - ta.clientHeight);
    preview.scrollTop = scrollPercent * (preview.scrollHeight - preview.clientHeight);
  }
  
  // Reset flag safely after the scroll event cascade
  requestAnimationFrame(() => isSyncingRight = false);
}

function syncScrollRight() {
  if (isSyncingRight) return;
  isSyncingLeft = true;
  
  const ta  = document.getElementById('md-textarea');
  const pre = document.getElementById('editor-highlight-layer');
  const preview = document.getElementById('md-preview');
  const linesEl = document.getElementById('editor-line-numbers');
  
  if (ta && preview && preview.scrollHeight > preview.clientHeight) {
    const scrollPercent = preview.scrollTop / (preview.scrollHeight - preview.clientHeight);
    ta.scrollTop = scrollPercent * (ta.scrollHeight - ta.clientHeight);
    if (pre) pre.scrollTop = ta.scrollTop;
    if (linesEl) linesEl.scrollTop = ta.scrollTop;
  }
  
  requestAnimationFrame(() => isSyncingLeft = false);
}
function updateHighlight() {
  const ta  = document.getElementById('md-textarea');
  const pre = document.getElementById('editor-highlight-layer');
  const linesEl = document.getElementById('editor-line-numbers');
  if (!pre || !ta) return;
  pre.innerHTML = highlightMarkdown(ta.value);
  
  if (linesEl) {
    const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const lines = ta.value.split('\n');
    let numbersHTML = '';
    for (let i = 0; i < lines.length; i++) {
      const text = esc(lines[i]) || '&#8203;';
      numbersHTML += `<span class="num-line" data-n="${i + 1}">${text}</span>\n`;
    }
    if (numbersHTML.endsWith('\n')) numbersHTML = numbersHTML.slice(0, -1);
    linesEl.innerHTML = numbersHTML;
  }
  
  syncScroll();
}

// ── Find and Replace Widget ─────────────────────────────────────────
let frMatches = [];
let frCurrentMatchIndex = -1;

function updateFrMatches() {
  const frFindInput = document.getElementById('fr-find-input');
  const ta = document.getElementById('md-textarea');
  const query = frFindInput.value.toLowerCase();
  frMatches = [];
  if (!query) {
    document.getElementById('fr-count').textContent = '0/0';
    return;
  }
  const text = ta.value.toLowerCase();
  let idx = text.indexOf(query);
  while (idx !== -1) {
    frMatches.push({ start: idx, end: idx + query.length });
    idx = text.indexOf(query, idx + 1);
  }
  if (frCurrentMatchIndex >= frMatches.length) frCurrentMatchIndex = 0;
  if (frMatches.length === 0) frCurrentMatchIndex = -1;
  else if (frCurrentMatchIndex === -1) frCurrentMatchIndex = 0;
  
  updateFrDisplay();
}

function updateFrDisplay() {
  const ta = document.getElementById('md-textarea');
  if (frMatches.length === 0) {
    document.getElementById('fr-count').textContent = '0/0';
    return;
  }
  document.getElementById('fr-count').textContent = `${frCurrentMatchIndex + 1}/${frMatches.length}`;
  const match = frMatches[frCurrentMatchIndex];
  
  const activeEl = document.activeElement;
  ta.focus();
  ta.setSelectionRange(match.start, match.end);

  // Scroll to match (approximate by line number)
  const textBefore = ta.value.substring(0, match.start);
  const lineCount = textBefore.split('\n').length;
  // lineHeight ≈ 22.75px (13px * 1.75), paddingTop = 16px
  const targetY = (lineCount - 1) * 22.75 + 16;
  ta.scrollTop = targetY - (ta.clientHeight / 2);
  
  syncScroll(); 
  
  if (activeEl && activeEl !== ta) {
    activeEl.focus();
  }
}

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    if (state.currentPanel === 'editor') {
      e.preventDefault();
      const frWidget = document.getElementById('find-replace-widget');
      const frFindInput = document.getElementById('fr-find-input');
      const ta = document.getElementById('md-textarea');
      frWidget.classList.remove('hidden');
      frFindInput.focus();
      if (ta.selectionStart !== ta.selectionEnd) {
        frFindInput.value = ta.value.substring(ta.selectionStart, ta.selectionEnd);
      }
      updateFrMatches();
    }
  }
  if (e.key === 'Escape') {
    const frWidget = document.getElementById('find-replace-widget');
    if (!frWidget.classList.contains('hidden')) {
      frWidget.classList.add('hidden');
      document.getElementById('md-textarea').focus();
    }
  }
});

document.getElementById('fr-find-input').addEventListener('input', updateFrMatches);
document.getElementById('fr-find-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    if (e.shiftKey) document.getElementById('btn-fr-prev').click();
    else document.getElementById('btn-fr-next').click();
  }
});

document.getElementById('btn-fr-next').addEventListener('click', () => {
  if (frMatches.length > 0) {
    frCurrentMatchIndex = (frCurrentMatchIndex + 1) % frMatches.length;
    updateFrDisplay();
  }
});

document.getElementById('btn-fr-prev').addEventListener('click', () => {
  if (frMatches.length > 0) {
    frCurrentMatchIndex = (frCurrentMatchIndex - 1 + frMatches.length) % frMatches.length;
    updateFrDisplay();
  }
});

document.getElementById('btn-fr-close').addEventListener('click', () => {
  document.getElementById('find-replace-widget').classList.add('hidden');
});

document.getElementById('btn-fr-replace').addEventListener('click', () => {
  if (frMatches.length === 0 || frCurrentMatchIndex === -1) return;
  const ta = document.getElementById('md-textarea');
  const match = frMatches[frCurrentMatchIndex];
  const replaceWith = document.getElementById('fr-replace-input').value;
  
  const before = ta.value.substring(0, match.start);
  const after = ta.value.substring(match.end);
  
  ta.value = before + replaceWith + after;
  ta.setSelectionRange(match.start, match.start + replaceWith.length);
  ta.dispatchEvent(new Event('input'));
  updateFrMatches();
});

document.getElementById('btn-fr-replace-all').addEventListener('click', () => {
  if (frMatches.length === 0) return;
  const ta = document.getElementById('md-textarea');
  const replaceStr = document.getElementById('fr-replace-input').value;
  
  const matches = [...frMatches].reverse();
  let text = ta.value;
  matches.forEach(m => {
    const before = text.substring(0, m.start);
    const after = text.substring(m.end);
    text = before + replaceStr + after;
  });
  
  ta.value = text;
  ta.dispatchEvent(new Event('input'));
  updateFrMatches();
  toast(`Replaced ${matches.length} occurrences`, 'success');
});

function initEditorPanel() {
  populateSelect('editor-novel-select', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('editor-novel-select').value = state.selectedNovel;
    editorNovelChange().then(() => {
      if (state.selectedVolume) {
        document.getElementById('editor-volume-select').value = state.selectedVolume;
        editorVolumeChange();
      }
    });
  }
}

async function editorNovelChange() {
  await loadVolumesForSelect('editor-novel-select', 'editor-volume-select');
  populateSelect('editor-file-select', [], 'Select File');
}

async function editorVolumeChange() {
  const novel = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  if (!novel || !volume) return;
  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
    populateSelect('editor-file-select', data.md_files || [], 'Select File');
  } catch (e) {
    toast('Error loading files: ' + e.message, 'error');
  }
}

async function editorFileChange() {
  const novel  = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  const file   = document.getElementById('editor-file-select').value;
  if (!novel || !volume || !file) return;

  if (state.mdDirty && state.currentMdPath) {
    if (!confirm('You have unsaved changes. Discard?')) {
      const oldFile = state.currentMdPath.split('/').pop();
      document.getElementById('editor-file-select').value = oldFile;
      return;
    }
  }

  const path = `${novel}/${volume}/${file}`;
  state.currentMdPath = path;
  state.mdDirty = false;

  try {
    const data = await GET(`/api/md?path=${encodeURIComponent(path)}`);
    document.getElementById('md-textarea').value = data.content || '';
    updateCharCount();
    updateHighlight();
    updatePreview();
  } catch (e) {
    toast('Error loading file: ' + e.message, 'error');
  }
}

function updateCharCount() {
  const len = document.getElementById('md-textarea').value.length;
  document.getElementById('editor-char-count').textContent =
    len.toLocaleString() + ' chars';
}

function updatePreview() {
  const md = document.getElementById('md-textarea').value;
  const preview = document.getElementById('md-preview');
  
  const novel  = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  let processedMd = md;
  if (novel && volume) {
    // Transform local image paths for the previewer
    processedMd = processedMd.replace(/!\[(.*?)\]\((images\/[^)]+)\)/g, (match, alt, relPath) => {
      return `![${alt}](/api/images/serve?path=${encodeURIComponent(novel + '/' + volume + '/' + relPath)})`;
    });
  }

  if (typeof marked !== 'undefined') {
    preview.innerHTML = marked.parse(processedMd);
  } else {
    preview.textContent = processedMd;
  }
}

let highlightRaf;

document.getElementById('md-textarea').addEventListener('input', () => {
  state.mdDirty = true;
  updateCharCount();
  
  if (highlightRaf) cancelAnimationFrame(highlightRaf);
  highlightRaf = requestAnimationFrame(updateHighlight);
  
  clearTimeout(previewDebounce);
  previewDebounce = setTimeout(updatePreview, 350);
});

document.getElementById('md-textarea').addEventListener('scroll', syncScroll);
document.getElementById('md-preview').addEventListener('scroll', syncScrollRight);

// Tab key inserts spaces instead of moving focus
document.getElementById('md-textarea').addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const ta = e.target;
    const start = ta.selectionStart;
    const end   = ta.selectionEnd;
    ta.value = ta.value.slice(0, start) + '    ' + ta.value.slice(end);
    ta.selectionStart = ta.selectionEnd = start + 4;
    updateHighlight();
  }
});

let isWordWrap = false;
document.getElementById('btn-toggle-wrap').addEventListener('click', () => {
  isWordWrap = !isWordWrap;
  const wrapEl = document.getElementById('editor-highlight-wrap');
  if (isWordWrap) {
    wrapEl.classList.add('wrap-enabled');
    toast('Word Wrap ON', 'info', 2000);
  } else {
    wrapEl.classList.remove('wrap-enabled');
    toast('Word Wrap OFF', 'info', 2000);
  }
});


document.getElementById('btn-save-md').addEventListener('click', saveMd);

async function saveMd() {
  if (!state.currentMdPath) { toast('No file selected', 'error'); return; }
  const content = document.getElementById('md-textarea').value;
  try {
    await POST('/api/md', { path: state.currentMdPath, content });
    state.mdDirty = false;
    toast('Saved!', 'success');
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

// Keyboard shortcut: Ctrl+S
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    if (state.currentPanel === 'editor') saveMd();
    if (state.currentPanel === 'metadata') saveMeta();
    if (state.currentPanel === 'settings') saveSettings();
  }
});

// View toggles
document.getElementById('btn-view-split').addEventListener('click', () => {
  document.getElementById('editor-layout').className = 'editor-layout';
});
document.getElementById('btn-view-editor').addEventListener('click', () => {
  document.getElementById('editor-layout').className = 'editor-layout editor-only';
});
document.getElementById('btn-view-preview').addEventListener('click', () => {
  document.getElementById('editor-layout').className = 'editor-layout preview-only';
  updatePreview();
});

// New file
document.getElementById('btn-new-file').addEventListener('click', () => {
  openModal('modal-new-file');
  document.getElementById('new-file-name').value = '';
});

document.getElementById('btn-create-file').addEventListener('click', async () => {
  const novel  = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  const fname  = document.getElementById('new-file-name').value.trim();
  if (!novel || !volume || !fname) return;
  const path = `${novel}/${volume}/${fname.endsWith('.md') ? fname : fname + '.md'}`;
  try {
    const form = new FormData();
    form.append('path', path);
    const res = await fetch('/api/md/new', { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json()).detail);
    closeModal('modal-new-file');
    await editorVolumeChange();
    document.getElementById('editor-file-select').value = path.split('/').pop();
    editorFileChange();
    toast('File created!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});

// Rename file
document.getElementById('btn-rename-file').addEventListener('click', () => {
  if (!state.currentMdPath) { toast('No file selected', 'error'); return; }
  const currentName = state.currentMdPath.split('/').pop();
  document.getElementById('rename-file-name').value = currentName;
  openModal('modal-rename-file');
});

document.getElementById('btn-confirm-rename').addEventListener('click', async () => {
  let newName = document.getElementById('rename-file-name').value.trim();
  if (!newName) return;
  if (!newName.endsWith('.md')) newName += '.md';
  
  const oldPath = state.currentMdPath;
  const parts = oldPath.split('/');
  parts.pop();
  const newPath = parts.join('/') + '/' + newName;
  
  try {
    await POST('/api/rename', { old_path: oldPath, new_path: newPath });
    closeModal('modal-rename-file');
    await editorVolumeChange();
    setSelectValue('editor-file-select', newName);
    editorFileChange();
    toast('File renamed!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});

// Delete file
document.getElementById('btn-delete-file').addEventListener('click', async () => {
  if (!state.currentMdPath) { toast('No file selected', 'error'); return; }
  const filename = state.currentMdPath.split('/').pop();
  
  if (!confirm(`Are you sure you want to delete ${filename}? This cannot be undone.`)) return;
  
  try {
    await DEL('/api/delete', { path: state.currentMdPath });
    state.currentMdPath = null;
    document.getElementById('md-textarea').value = '';
    updateCharCount();
    updateHighlight();
    updatePreview();
    
    await editorVolumeChange();
    toast('File deleted!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});

// ══════════════════════════════════════════════════════════════════
// IMAGES PANEL
// ══════════════════════════════════════════════════════════════════
function initImagesPanel() {
  populateSelect('img-novel-select', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('img-novel-select').value = state.selectedNovel;
    imgNovelChange().then(() => {
      if (state.selectedVolume) {
        document.getElementById('img-volume-select').value = state.selectedVolume;
        loadImages();
      }
    });
  }
}

async function imgNovelChange() {
  await loadVolumesForSelect('img-novel-select', 'img-volume-select');
}

async function imgVolumeChange() {
  loadImages();
}

async function loadImages() {
  const novel = document.getElementById('img-novel-select').value;
  const volume = document.getElementById('img-volume-select').value;
  if (!novel || !volume) return;

  const grid = document.getElementById('image-grid');
  grid.innerHTML = '<div class="text-muted text-sm">Loading…</div>';

  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
    const images = data.images || [];
    state.images = images;
    grid.innerHTML = '';
    images.forEach(imgPath => {
      const card = document.createElement('div');
      card.className = 'image-card';
      const relPath = `${novel}/${volume}/${imgPath}`;
      const name = imgPath.split('/').pop();
      const src = `/api/images/serve?path=${encodeURIComponent(relPath)}`;
      card.innerHTML = `
        <img src="${src}" alt="${name}" loading="lazy"
             onerror="this.style.display='none'" style="cursor:pointer;" onclick="openLightbox('${src}')">
        <div class="img-label" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px;">
          <span title="${name}" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${name}</span>
          <button class="btn btn-ghost btn-sm" onclick="copyToClipboard('images/${name}')" title="Copy Markdown Path" style="padding: 2px 6px; margin-left: 4px;">📋</button>
        </div>
      `;
      grid.appendChild(card);
    });
    if (!images.length) {
      grid.innerHTML = '<div class="text-muted text-sm" style="grid-column:span 4;text-align:center;padding:40px">No images yet — upload some above.</div>';
    }
  } catch (e) {
    grid.innerHTML = `<div style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

// Upload dropzone
const dropzone = document.getElementById('upload-dropzone');
const fileInput = document.getElementById('img-file-input');

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  handleImageFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => handleImageFiles(fileInput.files));

async function handleImageFiles(files) {
  const novel = document.getElementById('img-novel-select').value;
  const volume = document.getElementById('img-volume-select').value;
  if (!novel || !volume) { toast('Select novel and volume first', 'error'); return; }

  let ok = 0, fail = 0;
  for (const file of files) {
    const form = new FormData();
    form.append('file', file);
    form.append('novel', novel);
    form.append('volume', volume);
    try {
      const res = await fetch('/api/images/upload', { method: 'POST', body: form });
      if (!res.ok) throw new Error((await res.json()).detail);
      ok++;
    } catch (e) {
      fail++;
      toast(`Upload failed: ${file.name} — ${e.message}`, 'error');
    }
  }
  if (ok) toast(`Uploaded ${ok} image(s)`, 'success');
  loadImages();
}

// ══════════════════════════════════════════════════════════════════
// METADATA PANEL (main.md editor)
// ══════════════════════════════════════════════════════════════════
let metaRawMode = false;

function initMetaPanel() {
  populateSelect('meta-novel-select', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('meta-novel-select').value = state.selectedNovel;
    metaNovelChange().then(() => {
      if (state.selectedVolume) {
        document.getElementById('meta-volume-select').value = state.selectedVolume;
        loadMeta();
      }
    });
  }
}

async function metaNovelChange() {
  await loadVolumesForSelect('meta-novel-select', 'meta-volume-select');
}

async function metaVolumeChange() {
  loadMeta();
}

async function loadMeta() {
  const novel = document.getElementById('meta-novel-select').value;
  const volume = document.getElementById('meta-volume-select').value;
  if (!novel || !volume) return;
  try {
    const data = await GET(`/api/mainmd?novel=${encodeURIComponent(novel)}&volume=${encodeURIComponent(volume)}`);
    const content = data.content || '';
    document.getElementById('meta-raw-textarea').value = content;
    parseMetaToForm(content);
  } catch (e) {
    toast('Error loading main.md: ' + e.message, 'error');
  }
}

function parseMetaToForm(raw) {
  const get = (key) => {
    const m = raw.match(new RegExp(`^${key}\\s*:\\s*\\[(.*)\\]`, 'm'));
    const val = m ? m[1] : '';
    // Auto-clear old template placeholders
    const placeholders = [
      'Insert Japanese Title Here', 'Insert Indonesian Title Here', 'Insert English Title Here',
      'Author Name', 'Illustrator/Artist Name', 'Genre 1, Genre 2, Genre 3',
      'Translator Name', 'EPUB Compiler Name', 
      'Cover Image URL (e.g. https://...) OR Local Cover File Path (e.g. images/cover.jpg)'
    ];
    return placeholders.includes(val) ? '' : val;
  };
  document.getElementById('meta-title-jp').value   = get('Title Japan');
  document.getElementById('meta-title-id').value   = get('Title Indonesia');
  document.getElementById('meta-title-en').value   = get('Title Inggris');
  document.getElementById('meta-title-ro').value   = get('Title Romanji');
  document.getElementById('meta-volume-num').value = get('Volume');
  document.getElementById('meta-author').value     = get('Author');
  document.getElementById('meta-artist').value     = get('Artist');
  document.getElementById('meta-translator').value = get('Translator');
  document.getElementById('meta-compiler').value   = get('EPUB Compiler') || 'TakoYune';
  document.getElementById('meta-genres').value     = get('Genres');
  document.getElementById('meta-cover').value      = get('Cover');

  // Primary title dropdown
  const ptVal = get('Primary Title').trim().toLowerCase();
  const ptSel = document.getElementById('meta-primary-title');
  if (ptSel && ptVal && ['id','en','jp','romaji'].includes(ptVal)) {
    ptSel.value = ptVal;
  } else if (ptSel) {
    ptSel.value = 'id'; // default
  }

  // Parse TOC block
  const tocMatch = raw.match(/Table of Content\[\s*([\s\S]*?)\n\s*\]/);
  let tocItems = [];
  if (tocMatch) {
    tocItems = tocMatch[1].trim().split('\n').map(l => l.trim()).filter(Boolean);
  }
  renderTocBuilder(tocItems);
}

// ── TOC Builder Logic ────────────────────────────────────────────────
function renderTocBuilder(items) {
  const container = document.getElementById('toc-builder');
  container.innerHTML = '';
  if (!items || !items.length) {
    container.innerHTML = '<div class="text-muted text-sm" style="padding:16px;text-align:center;">No items. Click "Auto Scan" to load files.</div>';
    return;
  }
  items.forEach(item => addTocItemDOM(item));
}

function addTocItemDOM(value) {
  const container = document.getElementById('toc-builder');
  if (container.querySelector('.text-muted')) container.innerHTML = ''; // clear empty state
  
  const el = document.createElement('div');
  el.className = 'toc-item';
  el.draggable = true;
  el.innerHTML = `
    <div class="toc-handle" title="Drag to reorder">↕</div>
    <input class="toc-input" value="${value.replace(/"/g, '&quot;')}">
    <button class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()" title="Remove">✕</button>
  `;
  
  el.addEventListener('dragstart', () => el.classList.add('dragging'));
  el.addEventListener('dragend', () => el.classList.remove('dragging'));
  container.appendChild(el);
}

// Initialize Container Drag & Drop once
document.addEventListener('DOMContentLoaded', () => {
  const tocContainer = document.getElementById('toc-builder');
  if (!tocContainer) return;
  
  tocContainer.addEventListener('dragover', e => {
    e.preventDefault();
    const dragging = tocContainer.querySelector('.dragging');
    if (!dragging) return;
    
    // Auto-scroll logic
    const rect = tocContainer.getBoundingClientRect();
    const scrollThreshold = 35;
    if (e.clientY - rect.top < scrollThreshold) {
      tocContainer.scrollTop -= 8;
    } else if (rect.bottom - e.clientY < scrollThreshold) {
      tocContainer.scrollTop += 8;
    }
    
    const draggableElements = [...tocContainer.querySelectorAll('.toc-item:not(.dragging)')];
    const afterElement = draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = e.clientY - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;

    if (afterElement == null) {
      tocContainer.appendChild(dragging);
    } else {
      tocContainer.insertBefore(dragging, afterElement);
    }
  });
});

document.getElementById('btn-add-toc-item').addEventListener('click', () => {
  addTocItemDOM('[Chapter X.md(file)]');
});

document.getElementById('btn-auto-toc').addEventListener('click', async () => {
  const novel = document.getElementById('meta-novel-select').value;
  const volume = document.getElementById('meta-volume-select').value;
  if (!novel || !volume) { toast('Select novel and volume first', 'error'); return; }
  
  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
    const files = data.md_files || [];
    
    // Intelligent Natural Sort
    files.sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      // Prologue always first
      if (aLower.includes('prolog') && !bLower.includes('prolog')) return -1;
      if (bLower.includes('prolog') && !aLower.includes('prolog')) return 1;
      // Epilogue always last
      if (aLower.includes('epilog') && !bLower.includes('epilog')) return 1;
      if (bLower.includes('epilog') && !aLower.includes('epilog')) return -1;
      
      // Natural number sort for chapters (e.g. Chapter 2 before Chapter 10)
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });
    
    const currentInputs = [...document.querySelectorAll('#toc-builder .toc-input')];
    const currentItems = currentInputs.map(inp => inp.value.trim()).filter(Boolean);
    
    if (currentItems.length === 0) {
      currentItems.push(`[Cover (images/cover.webp)]`);
      currentItems.push(`[Table of Contents]`);
      currentItems.push(`[About]`);
    }

    let addedCount = 0;
    // [Bug 4 fix] Case-insensitive duplicate check for TOC items
    const lowerItems = currentItems.map(i => i.toLowerCase());
    
    files.forEach(f => {
      if (f.toLowerCase() !== 'main.md') {
        const item = `[${f}(file)]`;
        if (!lowerItems.includes(item.toLowerCase())) {
          currentItems.push(item);
          lowerItems.push(item.toLowerCase());
          addedCount++;
        }
      }
    });
    
    renderTocBuilder(currentItems);
    toast(`TOC Auto-Scanned: Added ${addedCount} new items`, 'success');
  } catch (e) {
    toast('Failed to scan: ' + e.message, 'error');
  }
});

function buildMetaFromForm() {
  const f = id => document.getElementById(id).value.trim();
  const primaryLang = document.getElementById('meta-primary-title')?.value || 'id';
  
  // Read TOC from the UI builder inputs
  const tocInputs = [...document.querySelectorAll('#toc-builder .toc-input')];
  const toc = tocInputs.map(inp => inp.value.trim()).filter(Boolean)
    .map(l => '    ' + l).join('\n');

  // Build title lines — skip blank ones
  const titleLines = [];
  const titleJp = f('meta-title-jp');
  const titleId = f('meta-title-id');
  const titleEn = f('meta-title-en');
  const titleRo = f('meta-title-ro');
  const volumeNum = f('meta-volume-num');
  
  if (titleJp) titleLines.push(`Title Japan: [${titleJp}]`);
  if (titleId) titleLines.push(`Title Indonesia: [${titleId}]`);
  if (titleEn) titleLines.push(`Title Inggris : [${titleEn}]`);
  if (titleRo) titleLines.push(`Title Romanji: [${titleRo}]`);
  if (volumeNum) titleLines.push(`Volume: [${volumeNum}]`);

  return `# Main\n\n${titleLines.join('\n')}\nAuthor: [${f('meta-author')}]\nArtist: [${f('meta-artist')}]\nGenres: [${f('meta-genres')}]\nTranslator: [${f('meta-translator')}]\nEPUB Compiler : [${f('meta-compiler')}]\nPrimary Title: [${primaryLang}]\n\nCover : [${f('meta-cover')}]\n\nTable of Content[\n${toc}\n]\n`;
}

document.getElementById('btn-meta-raw').addEventListener('click', () => {
  metaRawMode = !metaRawMode;
  document.getElementById('meta-form-view').classList.toggle('hidden', metaRawMode);
  document.getElementById('meta-raw-view').classList.toggle('hidden', !metaRawMode);
  document.getElementById('btn-meta-raw').textContent = metaRawMode ? 'Form View' : 'Raw MD';
  if (metaRawMode) {
    // Sync form → raw
    document.getElementById('meta-raw-textarea').value = buildMetaFromForm();
  } else {
    // Sync raw → form
    parseMetaToForm(document.getElementById('meta-raw-textarea').value);
  }
});

document.getElementById('btn-save-meta').addEventListener('click', saveMeta);

async function saveMeta() {
  const novel = document.getElementById('meta-novel-select').value;
  const volume = document.getElementById('meta-volume-select').value;
  if (!novel || !volume) { toast('Select novel and volume', 'error'); return; }

  if (!metaRawMode) {
    const tJp = document.getElementById('meta-title-jp').value.trim();
    const tId = document.getElementById('meta-title-id').value.trim();
    const tEn = document.getElementById('meta-title-en').value.trim();
    const tRo = document.getElementById('meta-title-ro').value.trim();
    if (!tJp && !tId && !tEn && !tRo) {
      toast('Error: At least one Title field must be filled!', 'error');
      return;
    }
  }

  const content = metaRawMode
    ? document.getElementById('meta-raw-textarea').value
    : buildMetaFromForm();

  try {
    await POST('/api/mainmd', { path: `${novel}/${volume}/main.md`, content });
    toast('main.md saved!', 'success');
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

// ══════════════════════════════════════════════════════════════════
// EPUB BUILDER PANEL
// ══════════════════════════════════════════════════════════════════
function initBuilderPanel() {
  populateSelect('build-novel-select', state.novels, 'Select Novel');
  if (state.selectedNovel) {
    document.getElementById('build-novel-select').value = state.selectedNovel;
    buildNovelChange().then(() => {
      if (state.selectedVolume) {
        document.getElementById('build-volume-select').value = state.selectedVolume;
      }
    });
  }
}

async function buildNovelChange() {
  await loadVolumesForSelect('build-novel-select', 'build-volume-select');
}

document.getElementById('btn-build').addEventListener('click', startBuild);

function setPhase(phaseId, status) {
  // status: 'idle' | 'active' | 'done' | 'error'
  const el = document.getElementById(phaseId);
  const badge = document.getElementById(phaseId + '-badge');
  el.className = `build-phase ${status}`;
  const labels = { idle: 'Idle', active: 'Running…', done: 'Done ✓', error: 'Error ✗' };
  const badgeClass = { idle: 'badge-muted', active: 'badge-amber', done: 'badge-green', error: 'badge-red' };
  if (badge) {
    badge.textContent = labels[status] || status;
    badge.className = `badge ${badgeClass[status] || 'badge-muted'} ml-auto`;
  }
}

function resetPhases() {
  ['phase-audit','phase-format','phase-images','phase-compile','phase-done'].forEach(id => setPhase(id, 'idle'));
}

function logBuild(msg, cls = '') {
  const log = document.getElementById('build-log');
  const line = document.createElement('span');
  if (cls) line.className = `bl-${cls}`;
  line.textContent = msg + '\n';
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}

async function startBuild() {
  const novel  = document.getElementById('build-novel-select').value;
  const volume = document.getElementById('build-volume-select').value;
  if (!novel || !volume) { toast('Select novel and volume', 'error'); return; }

  const btn = document.getElementById('btn-build');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Building…';

  document.getElementById('build-log').textContent = '';
  resetPhases();

  logBuild(`▶ Starting build: ${novel} / ${volume}`, 'info');
  logBuild(`  Python: running build_novel.py…`, 'info');

  // Animate phases while building
  const phases = ['phase-audit','phase-format','phase-images','phase-compile'];
  let phaseIdx = 0;
  const phaseTimer = setInterval(() => {
    if (phaseIdx > 0) setPhase(phases[phaseIdx - 1], 'done');
    if (phaseIdx < phases.length) setPhase(phases[phaseIdx], 'active');
    phaseIdx++;
    if (phaseIdx >= phases.length) clearInterval(phaseTimer);
  }, 1500);

  try {
    const res = await POST('/api/build', { novel, volume });
    clearInterval(phaseTimer);
    phases.forEach(p => setPhase(p, 'done'));

    if (res.stdout) res.stdout.split('\n').forEach(line => {
      const cls = line.includes('✅') || line.includes('Done') ? 'ok'
        : line.includes('Warning') ? 'warn'
        : line.includes('Error') || line.includes('error') ? 'err' : '';
      logBuild(line, cls);
    });
    if (res.stderr) res.stderr.split('\n').filter(l => l.trim()).forEach(line => logBuild(line, 'err'));

    if (res.ok) {
      setPhase('phase-done', 'done');
      logBuild(`\n✅ Build complete!`, 'ok');
      if (res.epub_path) logBuild(`📄 Output: ${res.epub_path}`, 'info');
      toast('EPUB compiled successfully!', 'success', 5000);
    } else {
      setPhase('phase-done', 'error');
      phases.forEach(p => {
        if (document.getElementById(p)?.className.includes('active')) setPhase(p, 'error');
      });
      logBuild(`\n❌ Build failed (exit code ${res.returncode})`, 'err');
      toast('Build failed — check the log', 'error');
    }
  } catch (e) {
    clearInterval(phaseTimer);
    setPhase('phase-compile', 'error');
    setPhase('phase-done', 'error');
    logBuild(`\n❌ Error: ${e.message}`, 'err');
    toast('Build error: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Compile EPUB';
  }
}

// ══════════════════════════════════════════════════════════════════
// SETTINGS PANEL
// ══════════════════════════════════════════════════════════════════
let currentSettings = {};

async function initSettingsPanel() {
  try {
    const data = await GET('/api/settings');
    currentSettings = data;
    applySettingsToForm(data);
    fetchLogs();
  } catch (e) {
    toast('Error loading settings: ' + e.message, 'error');
  }
}

async function fetchLogs() {
  try {
    const data = await GET('/api/logs');
    document.getElementById('system-log-viewer').value = data.logs || 'No logs yet.';
    const logEl = document.getElementById('system-log-viewer');
    logEl.scrollTop = logEl.scrollHeight;
  } catch (e) {
    document.getElementById('system-log-viewer').value = 'Failed to load logs.';
  }
}

document.getElementById('btn-refresh-logs').addEventListener('click', fetchLogs);

function applySettingsToForm(data) {
  const img = data.image || {};
  const out = data.output || {};
  const sty = data.styling || {};
  const bld = data.build || {};

  setVal('set-img-format',    img.format || 'webp');
  setVal('set-img-quality',   img.quality || '90');
  setVal('set-img-maxsize',   img.max_size_mb || '1.5');
  setVal('set-img-maxdim',    img.max_dimension || '2000');
  setVal('set-img-method',    img.webp_method || '4');

  setVal('set-out-lang',      out.language || 'id');
  setVal('set-out-location',  out.output_location || 'parent');
  setVal('set-out-format',    out.output_name_format || '{folder_name}');

  setVal('set-sty-dropcap',    sty.drop_cap || 'false');
  setVal('set-sty-scenebreak', sty.scene_break_symbol || '❖ ❖ ❖');
  setVal('set-sty-fontsize',   sty.font_size || '1.0');
  setVal('set-sty-lineheight', sty.line_height || '1.8');
  setVal('set-sty-indent',     sty.text_indent || '1.5');

  setVal('set-bld-autoconvert',  bld.auto_convert_images || 'true');
  setVal('set-bld-autocompress', bld.auto_compress || 'true');
  setVal('set-bld-download',     bld.download_online_images || 'true');
  setVal('set-bld-retries',      bld.download_retries || '3');
  setVal('set-bld-timeout',      bld.download_timeout || '30');

  const sys = data.Settings || {};
  setVal('set-sys-maxlogs',      sys.max_logs || '1000');
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

document.getElementById('btn-save-settings').addEventListener('click', saveSettings);

async function saveSettings() {
  const newSettings = {
    image: {
      format:         document.getElementById('set-img-format').value,
      quality:        document.getElementById('set-img-quality').value,
      max_size_mb:    document.getElementById('set-img-maxsize').value,
      max_dimension:  document.getElementById('set-img-maxdim').value,
      webp_method:    document.getElementById('set-img-method').value,
    },
    output: {
      language:             document.getElementById('set-out-lang').value,
      output_location:      document.getElementById('set-out-location').value,
      output_name_format:   document.getElementById('set-out-format').value,
    },
    styling: {
      drop_cap:             document.getElementById('set-sty-dropcap').value,
      scene_break_symbol:   document.getElementById('set-sty-scenebreak').value,
      font_size:            document.getElementById('set-sty-fontsize').value,
      line_height:          document.getElementById('set-sty-lineheight').value,
      text_indent:          document.getElementById('set-sty-indent').value,
    },
    build: {
      auto_convert_images:  document.getElementById('set-bld-autoconvert').value,
      auto_compress:        document.getElementById('set-bld-autocompress').value,
      download_online_images: document.getElementById('set-bld-download').value,
      download_retries:     document.getElementById('set-bld-retries').value,
      download_timeout:     document.getElementById('set-bld-timeout').value,
    },
    Settings: {
      max_logs: document.getElementById('set-sys-maxlogs').value,
    }
  };

  try {
    await POST('/api/settings', { settings: newSettings });
    toast('Settings saved!', 'success');
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}

// ══════════════════════════════════════════════════════════════════
// BOOT
// ══════════════════════════════════════════════════════════════════
async function boot() {
  await loadLibrary();
  toast('NarrativeOS ready', 'info', 2000);
}

boot();
