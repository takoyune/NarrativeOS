import { loadVolumesForSelect } from './library.js';
import { state, setPendingAction, setPendingSelectTarget } from '../core/state.js';
import { api, GET, POST, DEL, sendLog } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from '../core/utils.js';


export function initMetaPanel() {
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
export async function metaNovelChange() {
  await loadVolumesForSelect('meta-novel-select', 'meta-volume-select');
}
export async function metaVolumeChange() {
  loadMeta();
}
export async function loadMeta() {
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
window.syncPrimaryLangOptions = function() {
  const sel = document.getElementById('meta-primary-title');
  if (!sel) return;
  const currentVal = sel.value;
  const standardOptions = [
    {val: 'id', text: 'Indonesian (default)'},
    {val: 'en', text: 'English'},
    {val: 'jp', text: 'Japanese'},
    {val: 'romaji', text: 'Romanji'}
  ];
  sel.innerHTML = '';
  standardOptions.forEach(opt => {
    const el = document.createElement('option');
    el.value = opt.val;
    el.textContent = opt.text;
    sel.appendChild(el);
  });
  document.querySelectorAll('#custom-lang-container .field').forEach(row => {
    const langInput = row.querySelector('input[placeholder="e.g. Spanish"]');
    const lang = langInput ? langInput.value.trim() : '';
    if (lang) {
      const el = document.createElement('option');
      el.value = lang.toLowerCase();
      el.textContent = lang;
      sel.appendChild(el);
    }
  });
  if ([...sel.options].some(o => o.value === currentVal)) {
    sel.value = currentVal;
  } else {
    sel.value = 'id';
  }
};

window.addCustomLanguageRow = function(lang = '', val = '') {
  const container = document.getElementById('custom-lang-container');
  const row = document.createElement('div');
  row.className = 'field';
  row.innerHTML = `
    <div style="display:flex; gap:8px; margin-bottom:4px; align-items:center;">
      <label class="label" style="margin:0;">Language Name:</label>
      <input class="input" style="padding:4px 8px; font-size:12px; height:24px; width:120px;" placeholder="e.g. Spanish" value="${lang}" onchange="syncPrimaryLangOptions()" onkeyup="syncPrimaryLangOptions()">
      <button type="button" class="btn btn-ghost btn-sm" style="margin-left:auto; color:var(--red); padding:0 8px; height:24px; cursor:pointer;" onclick="this.closest('.field').remove(); syncPrimaryLangOptions();">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Remove
      </button>
    </div>
    <input class="input custom-lang-val" placeholder="Title in this language" value="${val.replace(/"/g, '&quot;')}">
  `;
  container.appendChild(row);
  syncPrimaryLangOptions();
};

export function parseMetaToForm(raw) {
  const get = (key) => {
    const m = raw.match(new RegExp(`^${key}\\s*:\\s*\\[(.*)\\]`, 'm'));
    const val = m ? m[1] : '';
    const placeholders = [
      'Insert Japanese Title Here', 'Insert Indonesian Title Here', 'Insert English Title Here',
      'Author Name', 'Illustrator/Artist Name', 'Genre 1, Genre 2, Genre 3',
      'Translator Name', 'EPUB Compiler Name', 
      'Cover Image URL (e.g. https://...) OR Local Cover File Path (e.g. images/cover.jpg)'
    ];
    return placeholders.includes(val) ? '' : val;
  };
  const customLangContainer = document.getElementById('custom-lang-container');
  if (customLangContainer) customLangContainer.innerHTML = '';
  document.getElementById('meta-title-jp').value = '';
  document.getElementById('meta-title-id').value = '';
  document.getElementById('meta-title-en').value = '';
  document.getElementById('meta-title-ro').value = '';
  
  const titleRegex = /^Title\s+(.*?)\s*:\s*\[(.*?)\]/gm;
  let match;
  while ((match = titleRegex.exec(raw)) !== null) {
    const lang = match[1].trim();
    let val = match[2].trim();
    if (val.startsWith('Insert ')) val = '';
    
    if (lang === 'Japan') document.getElementById('meta-title-jp').value = val;
    else if (lang === 'Indonesia') document.getElementById('meta-title-id').value = val;
    else if (lang === 'Inggris') document.getElementById('meta-title-en').value = val;
    else if (lang === 'Romanji') document.getElementById('meta-title-ro').value = val;
    else if (lang && typeof addCustomLanguageRow === 'function') {
      addCustomLanguageRow(lang, val);
    }
  }

  document.getElementById('meta-volume-num').value = get('Volume');
  document.getElementById('meta-author').value     = get('Author');
  document.getElementById('meta-artist').value     = get('Artist');
  document.getElementById('meta-translator').value = get('Translator');
  document.getElementById('meta-compiler').value   = get('EPUB Compiler') || 'TakoYune';
  document.getElementById('meta-genres').value     = get('Genres');
  document.getElementById('meta-cover').value      = get('Cover');
  
  if (typeof syncPrimaryLangOptions === 'function') syncPrimaryLangOptions();
  
  const ptVal = get('Primary Title').trim().toLowerCase();
  const ptSel = document.getElementById('meta-primary-title');
  if (ptSel && ptVal) {
    if (![...ptSel.options].some(o => o.value === ptVal)) {
      const el = document.createElement('option');
      el.value = ptVal;
      el.textContent = ptVal.charAt(0).toUpperCase() + ptVal.slice(1);
      ptSel.appendChild(el);
    }
    ptSel.value = ptVal;
  } else if (ptSel) {
    ptSel.value = 'id'; 
  }
  const tocMatch = raw.match(/Table of Content\[\s*([\s\S]*?)\n\s*\]/);
  let tocItems = [];
  if (tocMatch) {
    tocItems = tocMatch[1].trim().split('\n').map(l => l.trim()).filter(Boolean);
  }
  renderTocBuilder(tocItems);
}
export function renderTocBuilder(items) {
  const container = document.getElementById('toc-builder');
  container.innerHTML = '';
  if (!items || !items.length) {
    container.innerHTML = '<div class="text-muted text-sm" style="padding:16px;text-align:center;">No items. Click "Auto Scan" to load files.</div>';
    return;
  }
  items.forEach(item => addTocItemDOM(item));
}
export function addTocItemDOM(value) {
  const container = document.getElementById('toc-builder');
  if (container.querySelector('.text-muted')) container.innerHTML = ''; 
  const el = document.createElement('div');
  el.className = 'toc-item';
  el.draggable = true;
  el.innerHTML = `
    <div class="toc-handle" title="Drag to reorder">↕</div>
    <input class="toc-input" value="${value.replace(/"/g, '&quot;')}">
    <button class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()" title="Remove">✕</button>
  `;
  el.addEventListener('dragstart', () => {
    el.classList.add('dragging');
    container.classList.add('is-dragging');
  });
  el.addEventListener('dragend', () => {
    el.classList.remove('dragging');
    container.classList.remove('is-dragging');
  });
  container.appendChild(el);
}
document.addEventListener('DOMContentLoaded', () => {
  const tocContainer = document.getElementById('toc-builder');
  if (!tocContainer) return;
  tocContainer.addEventListener('dragover', e => {
    e.preventDefault();
    const dragging = tocContainer.querySelector('.dragging');
    if (!dragging) return;
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
    files.sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      if (aLower.includes('prolog') && !bLower.includes('prolog')) return -1;
      if (bLower.includes('prolog') && !aLower.includes('prolog')) return 1;
      if (aLower.includes('epilog') && !bLower.includes('epilog')) return 1;
      if (bLower.includes('epilog') && !aLower.includes('epilog')) return -1;
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });
    const currentInputs = [...document.querySelectorAll('#toc-builder .toc-input')];
    let currentItems = currentInputs.map(inp => inp.value.trim()).filter(Boolean);
    if (currentItems.length === 0) {
      currentItems.push(`[Cover]`);
      currentItems.push(`[Table of Contents]`);
      currentItems.push(`[About]`);
    }
    let prunedCount = 0;
    const filesLower = files.map(f => f.toLowerCase());
    currentItems = currentItems.filter(item => {
      const m = item.match(/^\[(.*)\(file\)]$/i);
      if (m) {
        const fname = m[1].trim().toLowerCase();
        if (!filesLower.includes(fname)) {
          prunedCount++;
          return false; 
        }
      }
      return true; 
    });
    let addedCount = 0;
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
    let msg = `TOC Auto-Scanned: Added ${addedCount} new items`;
    if (prunedCount > 0) msg += `, Pruned ${prunedCount} missing files`;
    toast(msg, 'success');
  } catch (e) {
    toast('Failed to scan: ' + e.message, 'error');
  }
});
export function buildMetaFromForm() {
  const f = id => document.getElementById(id).value.trim();
  const primaryLang = document.getElementById('meta-primary-title')?.value || 'id';
  const tocInputs = [...document.querySelectorAll('#toc-builder .toc-input')];
  const toc = tocInputs.map(inp => inp.value.trim()).filter(Boolean)
    .map(l => '    ' + l).join('\n');
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
  
  document.querySelectorAll('#custom-lang-container .field').forEach(row => {
    const langInput = row.querySelector('input[placeholder="e.g. Spanish"]');
    const valInput = row.querySelector('.custom-lang-val');
    if (langInput && valInput) {
      const lang = langInput.value.trim();
      const val = valInput.value.trim();
      if (lang) titleLines.push(`Title ${lang}: [${val}]`);
    }
  });
  if (volumeNum) titleLines.push(`Volume: [${volumeNum}]`);
  return `# Main\n\n${titleLines.join('\n')}\nAuthor: [${f('meta-author')}]\nArtist: [${f('meta-artist')}]\nGenres: [${f('meta-genres')}]\nTranslator: [${f('meta-translator')}]\nEPUB Compiler : [${f('meta-compiler')}]\nPrimary Title: [${primaryLang}]\n\nCover : [${f('meta-cover')}]\n\nTable of Content[\n${toc}\n]\n`;
}
document.getElementById('btn-add-language')?.addEventListener('click', () => {
  openModal('modal-add-language');
  setTimeout(() => document.getElementById('add-lang-input').focus(), 100);
});

document.getElementById('btn-lang-cancel')?.addEventListener('click', () => {
  closeModal('modal-add-language');
  document.getElementById('add-lang-input').value = '';
});

document.getElementById('btn-lang-confirm')?.addEventListener('click', () => {
  const input = document.getElementById('add-lang-input');
  const lang = input.value.trim();
  if (lang) {
    if (typeof addCustomLanguageRow === 'function') {
      addCustomLanguageRow(lang);
      const container = document.getElementById('custom-lang-container');
      const newRow = container.lastElementChild;
      if (newRow) {
        const valInput = newRow.querySelector('.custom-lang-val');
        if (valInput) valInput.focus();
      }
    }
  }
  input.value = '';
  closeModal('modal-add-language');
});
document.getElementById('btn-meta-raw').addEventListener('click', () => {
  metaRawMode = !metaRawMode;
  document.getElementById('meta-form-view').classList.toggle('hidden', metaRawMode);
  document.getElementById('meta-raw-view').classList.toggle('hidden', !metaRawMode);
  document.getElementById('btn-meta-raw').textContent = metaRawMode ? 'Form View' : 'Raw MD';
  if (metaRawMode) {
    document.getElementById('meta-raw-textarea').value = buildMetaFromForm();
  } else {
    parseMetaToForm(document.getElementById('meta-raw-textarea').value);
  }
});
document.getElementById('btn-save-meta').addEventListener('click', saveMeta);
export async function saveMeta() {
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
    await POST('/api/md', { path: `${novel}/${volume}/main.md`, content });
    toast('main.md saved!', 'success');
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}
