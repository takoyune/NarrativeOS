import { loadVolumesForSelect, showVolumeInfo, openInEditor } from './library.js';
import { saveMeta } from './metadata.js';
import { saveSettings } from './settings.js';

import { state } from '../core/state.js';
import { api, GET, POST, DEL } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from '../core/utils.js';


let previewDebounce = null;
export function highlightMarkdown(text) {
  const esc = s => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  let inCode = false;
  const lines = text.split('\n');
  const result = lines.map(rawLine => {
    const line = esc(rawLine);
    if (/^```/.test(rawLine)) {
      inCode = !inCode;
      return `<span class="hl-codeblock">${line}</span>`;
    }
    if (inCode) {
      return `<span class="hl-codeblock">${line}</span>`;
    }
    if (/^\s*([\*\-]{3,}|❖[\s❖]+)\s*$/.test(rawLine)) {
      return `<span class="hl-scenebrk">${line}</span>`;
    }
    if (/^#{4,}\s/.test(rawLine)) return `<span class="hl-h4">${line}</span>`;
    if (/^###\s/.test(rawLine))    return `<span class="hl-h3">${line}</span>`;
    if (/^##\s/.test(rawLine))     return `<span class="hl-h2">${line}</span>`;
    if (/^#\s/.test(rawLine))      return `<span class="hl-h1">${line}</span>`;
    if (/^>\s?/.test(rawLine)) return `<span class="hl-blockquote">${line}</span>`;
    if (/^\[UI\]|^\[\/UI\]/.test(rawLine.trim()))    return `<span class="hl-ui">${line}</span>`;
    if (/^\[stats\]|^\[\/stats\]/i.test(rawLine.trim())) return `<span class="hl-stats">${line}</span>`;
    if (/^\(thought\)/.test(rawLine.trim())) return `<span class="hl-thought">${line}</span>`;
    if (/^[-_]{3,}\s*$/.test(rawLine)) return `<span class="hl-hr">${line}</span>`;
    if (/^(\s*[-*+]\s)/.test(rawLine)) {
      return rawLine.replace(/^(\s*)([-*+])(\s.*)$/, (_, sp, mk, rest) =>
        esc(sp) + `<span class="hl-listbullet">${esc(mk)}</span><span class="hl-plain">${applyInline(esc(rest))}</span>`
      );
    }
    if (/^\s*\d+\.\s/.test(rawLine)) {
      return rawLine.replace(/^(\s*)(\d+\.)(\s.*)$/, (_, sp, num, rest) =>
        esc(sp) + `<span class="hl-listnumber">${esc(num)}</span><span class="hl-plain">${applyInline(esc(rest))}</span>`
      );
    }
    return `<span class="hl-plain">${applyInline(line)}</span>`;
  });
  return result.join('\n') + '\n';
}
export function applyInline(s) {
  s = s.replace(/(!\[([^\]]*?)\]\([^)]*?\))/g,
    (_, m) => `<span class="hl-image">${m}</span>`);
  s = s.replace(/(\[[^\]]*?\]\([^)]*?\))/g,
    (_, m) => `<span class="hl-link">${m}</span>`);
  s = s.replace(/(\*{3}[^*\n]+?\*{3})/g,
    m => `<span class="hl-boldital">${m}</span>`);
  s = s.replace(/(\*{2}[^*\n]+?\*{2})/g,
    m => `<span class="hl-bold">${m}</span>`);
  s = s.replace(/(\*[^*\n]+?\*)/g,
    m => `<span class="hl-italic">${m}</span>`);
  s = s.replace(/(`[^`\n]+?`)/g,
    m => `<span class="hl-codeinline">${m}</span>`);
  s = s.replace(/(\(thought\)[^\n]*)/gi,
    m => `<span class="hl-thought">${m}</span>`);
  return s;
}
let isSyncingLeft = false;
let isSyncingRight = false;
export function syncScroll() {
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
    const hScrollbarHeight = ta.offsetHeight - ta.clientHeight;
    linesEl.style.paddingBottom = (16 + hScrollbarHeight) + 'px';
    linesEl.scrollTop = ta.scrollTop;
  }
  if (preview && ta.scrollHeight > ta.clientHeight) {
    const scrollPercent = ta.scrollTop / (ta.scrollHeight - ta.clientHeight);
    preview.scrollTop = scrollPercent * (preview.scrollHeight - preview.clientHeight);
  }
  requestAnimationFrame(() => isSyncingRight = false);
}
export function syncScrollRight() {
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
export function updateHighlight() {
  const ta  = document.getElementById('md-textarea');
  const pre = document.getElementById('editor-highlight-layer');
  const linesEl = document.getElementById('editor-line-numbers');
  if (!pre || !ta) return;

  let val = ta.value;
  const frWidget = document.getElementById('find-replace-widget');
  if (typeof frMatches !== 'undefined' && frMatches.length > 0 && frCurrentMatchIndex >= 0 && frWidget && !frWidget.classList.contains('hidden')) {
    const match = frMatches[frCurrentMatchIndex];
    val = val.substring(0, match.start) + '___SRCH_START___' + val.substring(match.start, match.end) + '___SRCH_END___' + val.substring(match.end);
  }

  let html = highlightMarkdown(val);
  html = html.replace(/___SRCH_START___/g, '<mark id="active-search-match" class="hl-search-match" style="background: rgba(245,166,35,0.6); color: #fff; border-radius: 2px;">');
  html = html.replace(/___SRCH_END___/g, '</mark>');
  pre.innerHTML = html;

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
let frMatches = [];
let frCurrentMatchIndex = -1;
export function updateFrMatches() {
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
document.getElementById('fr-find-input').addEventListener('input', updateFrMatches);
export function updateFrDisplay() {
  const ta = document.getElementById('md-textarea');
  if (typeof frMatches === 'undefined' || frMatches.length === 0) {
    document.getElementById('fr-count').textContent = '0/0';
    updateHighlight();
    return;
  }
  document.getElementById('fr-count').textContent = `${frCurrentMatchIndex + 1}/${frMatches.length}`;
  const match = frMatches[frCurrentMatchIndex];
  const activeEl = document.activeElement;
  ta.focus();
  ta.setSelectionRange(match.start, match.end);

  updateHighlight();

  const matchEl = document.getElementById('active-search-match');
  if (matchEl) {
    const pre = document.getElementById('editor-highlight-layer');
    let offsetTop = matchEl.offsetTop;
    let offsetParent = matchEl.offsetParent;
    while(offsetParent && offsetParent !== pre) {
        offsetTop += offsetParent.offsetTop;
        offsetParent = offsetParent.offsetParent;
    }
    ta.scrollTop = offsetTop - (ta.clientHeight / 2);
  } else {
    const textBefore = ta.value.substring(0, match.start);
    const lineCount = textBefore.split('\n').length;
    ta.scrollTop = (lineCount - 1) * 22.75 + 16 - (ta.clientHeight / 2);
  }

  syncScroll(); 
  if (activeEl && activeEl !== ta) {
    activeEl.focus();
  }
}
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
  updateHighlight();
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
export function initEditorPanel() {
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
export async function editorNovelChange() {
  await loadVolumesForSelect('editor-novel-select', 'editor-volume-select');
}
export async function editorVolumeChange() {
  const novel = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  if (!novel || !volume) return;
  const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
  populateSelect('editor-file-select', data.md_files || [], 'Select File');
}
export async function editorFileChange() {
  const novel = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  const file = document.getElementById('editor-file-select').value;
  if (!novel || !volume || !file) {
    document.getElementById('md-textarea').value = '';
    updateCharCount();
    updateHighlight();
    document.getElementById('md-preview').innerHTML = '';
    return;
  }
  if (file === 'main.md') {
    toast('main.md can only be edited in the Metadata panel', 'error');
    return;
  }
  const performChange = async () => {
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
  };
  if (state.mdDirty && state.currentMdPath) {
    const oldFile = state.currentMdPath.split('/').pop();
    if (file === oldFile) {
      showPanel('editor'); 
      return;
    }
    pendingAction = performChange;
    openModal('modal-unsaved-changes');
    return;
  }
  await performChange();
}
export function updateCharCount() {
  const len = document.getElementById('md-textarea').value.length;
  document.getElementById('editor-char-count').textContent =
    len.toLocaleString() + ' chars';
}
export function updatePreview() {
  const ta = document.getElementById('md-textarea');
  const md = ta.value;
  const preview = document.getElementById('md-preview');
  const novel  = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  let processedMd = md;
  if (novel && volume) {
    processedMd = processedMd.replace(/!\[(.*?)\]\((images\/[^)]+)\)/g, (match, alt, relPath) => {
      return `![${alt}](/api/images/serve?path=${encodeURIComponent(novel + '/' + volume + '/' + relPath)}&token=${window.API_KEY || ''})`;
    });
  }
  if (typeof marked !== 'undefined') {
    let html = marked.parse(processedMd);
    if (ta && ta.selectionStart !== ta.selectionEnd) {
      let selText = ta.value.substring(ta.selectionStart, ta.selectionEnd).trim();
      selText = selText.replace(/^[#*>-]+\s*/, '').replace(/[*_`]/g, '').trim();
      if (selText.length >= 3) {
        const regex = new RegExp('(' + selText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
        html = html.replace(/(^|>)([^<]+)(<|$)/g, (match, g1, g2, g3) => {
          return g1 + g2.replace(regex, '<mark class="preview-highlight" style="background: rgba(245,166,35,0.4); color: inherit; border-radius: 2px;">$1</mark>') + g3;
        });
      }
    }
    preview.innerHTML = html;
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
  checkAutocomplete();
});
document.getElementById('md-textarea').addEventListener('scroll', syncScroll);
document.getElementById('md-preview').addEventListener('scroll', syncScrollRight);

document.addEventListener('selectionchange', () => {
  const ta = document.getElementById('md-textarea');
  if (document.activeElement === ta) {
    if (ta.selectionStart !== ta.selectionEnd) {
      clearTimeout(previewDebounce);
      previewDebounce = setTimeout(updatePreview, 300);
    } else if (window.lastSelectionLength > 0) {
      clearTimeout(previewDebounce);
      previewDebounce = setTimeout(updatePreview, 300);
    }
    window.lastSelectionLength = ta.selectionEnd - ta.selectionStart;
  }
});
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
export async function saveMd() {
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

// --- Autocomplete Logic ---
let imageAutocompleteActive = false;

async function checkAutocomplete() {
  const ta = document.getElementById('md-textarea');
  const pos = ta.selectionStart;
  const textBefore = ta.value.substring(0, pos);
  
  const match = textBefore.match(/!\[(.*?)\]\($/);
  
  if (match) {
    await showAutocompletePopup();
  } else {
    hideAutocompletePopup();
  }
}

async function showAutocompletePopup() {
  const popup = document.getElementById('image-autocomplete-popup');
  const grid = document.getElementById('image-autocomplete-grid');
  
  const novel = document.getElementById('editor-novel-select').value;
  const volume = document.getElementById('editor-volume-select').value;
  if (!novel || !volume) return;

  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes/${encodeURIComponent(volume)}/files`);
    grid.innerHTML = '';
    
    if (!data.images || data.images.length === 0) {
      grid.innerHTML = '<div style="color:var(--text-muted); grid-column: 1/-1; text-align:center; padding:20px;">No images found in this volume.</div>';
    } else {
      data.images.forEach(imgPath => {
        const filename = imgPath.split('/').pop();
        const item = document.createElement('div');
        item.className = 'ac-item';
        
        const img = document.createElement('img');
        img.src = `/api/images/serve?path=${encodeURIComponent(novel + '/' + volume + '/' + imgPath)}&token=${window.API_KEY || ''}`;
        
        const label = document.createElement('div');
        label.className = 'ac-label';
        label.textContent = filename;
        
        item.appendChild(img);
        item.appendChild(label);
        
        item.addEventListener('click', (e) => {
          e.preventDefault();
          insertAutocomplete(filename);
        });
        
        grid.appendChild(item);
      });
    }
    
    popup.classList.remove('hidden');
    imageAutocompleteActive = true;
  } catch (e) {
    console.error('Autocomplete fetch error:', e);
  }
}

function hideAutocompletePopup() {
  const popup = document.getElementById('image-autocomplete-popup');
  if (popup && !popup.classList.contains('hidden')) {
    popup.classList.add('hidden');
    imageAutocompleteActive = false;
  }
}

function insertAutocomplete(filename) {
  const ta = document.getElementById('md-textarea');
  const pos = ta.selectionStart;
  
  const textBefore = ta.value.substring(0, pos);
  const textAfter = ta.value.substring(pos);
  
  ta.value = textBefore + filename + ')' + textAfter;
  
  const newPos = pos + filename.length + 1;
  ta.setSelectionRange(newPos, newPos);
  
  hideAutocompletePopup();
  ta.focus();
  ta.dispatchEvent(new Event('input'));
}

document.addEventListener('click', (e) => {
  if (imageAutocompleteActive && !e.target.closest('#image-autocomplete-popup') && e.target.id !== 'md-textarea') {
    hideAutocompletePopup();
  }
});

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    if (state.currentPanel === 'editor') saveMd();
    if (state.currentPanel === 'metadata') saveMeta();
    if (state.currentPanel === 'settings') saveSettings();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    if (state.currentPanel === 'editor') {
      e.preventDefault();
      document.getElementById('find-replace-widget').classList.remove('hidden');
      document.getElementById('fr-find-input').focus();
      if (typeof updateFrMatches === 'function') updateFrMatches();
    }
  }
});
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
    const res = await fetch('/api/md/new', { method: 'POST', headers: { 'X-API-Key': window.API_KEY || '' }, body: form });
    if (!res.ok) throw new Error((await res.json()).detail);
    closeModal('modal-new-file');
    try {
      const mdData = await GET(`/api/md?path=${encodeURIComponent(novel + '/' + volume + '/main.md')}`).catch(() => ({content: ''}));
      let mdContent = mdData.content || '';
      const newItem = `    [${path.split('/').pop()}(file)]`;
      mdContent = mdContent.replace(/\n\s*\]\s*$/, `\n${newItem}\n]`);
      await POST('/api/md', { path: `${novel}/${volume}/main.md`, content: mdContent });
    } catch(e) { console.error("Could not auto-add to TOC", e); }
    await showVolumeInfo(novel, volume);
    openInEditor(novel, volume, path.split('/').pop());
    toast('File created!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});
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
    const novel = document.getElementById('editor-novel-select').value;
    const volume = document.getElementById('editor-volume-select').value;
    try {
      const mdData = await GET(`/api/md?path=${encodeURIComponent(novel + '/' + volume + '/main.md')}`);
      if (mdData.content) {
        let content = mdData.content.replace(`[${oldPath.split('/').pop()}(file)]`, `[${newName}(file)]`);
        await POST('/api/md', { path: `${novel}/${volume}/main.md`, content });
      }
    } catch(e) { console.error("Could not rename in TOC", e); }
    await showVolumeInfo(novel, volume);
    openInEditor(novel, volume, newName);
    toast('File renamed!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});
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
    const novel = document.getElementById('editor-novel-select').value;
    const volume = document.getElementById('editor-volume-select').value;
    try {
      const mdData = await GET(`/api/md?path=${encodeURIComponent(novel + '/' + volume + '/main.md')}`);
      if (mdData.content) {
        const regex = new RegExp(`\\n\\s*\\[${filename.replace(/[.*+?^$\{tr}()|[\]\\]/g, '\\$&')}\\(file\\)\\]`, 'g');
        let content = mdData.content.replace(regex, '');
        await POST('/api/md', { path: `${novel}/${volume}/main.md`, content });
      }
    } catch(e) { console.error("Could not delete from TOC", e); }
    await showVolumeInfo(novel, volume);
    toast('File deleted!', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
});
