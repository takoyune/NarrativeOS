import { editorVolumeChange, editorFileChange } from './editor.js';
import { state } from '../core/state.js';
import { api, GET, POST, DEL } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect, setSelectValue } from '../core/utils.js';


export async function loadLibrary() {
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
export function renderLibraryTree() {
  const tree = document.getElementById('library-tree');
  if (!state.novels.length) {
    tree.innerHTML = '<div class="text-muted text-sm" style="padding:8px">No novels found</div>';
    return;
  }
  tree.innerHTML = '';
  state.novels.forEach((novel, idx) => {
    const novelEl = document.createElement('div');
    novelEl.className = 'menu-item';
    novelEl.innerHTML = `
      <button class="menu-btn" title="${novel}">
        <svg class="item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        <span class="menu-label">${novel}</span>
        <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <div class="submenu"></div>
    `;
    tree.appendChild(novelEl);
    novelEl.querySelector('.menu-btn').addEventListener('click', async () => {
      const childrenEl = novelEl.querySelector('.submenu');
      if (novelEl.classList.contains('open')) {
        novelEl.classList.remove('open');
      } else {
        novelEl.classList.add('open');
        if (childrenEl.innerHTML === '') {
          await loadVolumesInTree(novel, childrenEl);
        }
      }
    });
  });
}
export async function loadVolumesInTree(novel, container) {
  container.innerHTML = '<div class="sub-btn text-muted text-sm" style="padding-left:14px;pointer-events:none;">Loading…</div>';
  try {
    const data = await GET(`/api/novels/${encodeURIComponent(novel)}/volumes`);
    container.innerHTML = '';
    (data.volumes || []).forEach(vol => {
      const el = document.createElement('button');
      el.className = 'sub-btn';
      el.dataset.novel = novel;
      el.dataset.volume = vol;
      el.title = vol;
      el.innerHTML = `<span class="sub-dot"></span>${vol}`;
      el.addEventListener('click', () => {
        document.querySelectorAll('.sub-btn.active').forEach(b => b.classList.remove('active'));
        el.classList.add('active');
        selectVolume(novel, vol);
      });
      container.appendChild(el);
    });
    if (!data.volumes?.length) {
      container.innerHTML = '<div class="sub-btn text-muted text-sm" style="padding-left:14px;pointer-events:none;">No volumes</div>';
    }
  } catch (e) {
    container.innerHTML = `<div class="sub-btn" style="color:var(--red);pointer-events:none;">Error: ${e.message}</div>`;
  }
}
export async function updateStats() {
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
export async function selectVolume(novel, volume) {
  state.selectedNovel = novel;
  state.selectedVolume = volume;
  document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
  document.querySelectorAll(`[data-novel="${novel}"][data-volume="${volume}"]`).forEach(el => el.classList.add('selected'));
  document.getElementById('breadcrumb').innerHTML =
    `<span>${novel}</span> / <span>${volume}</span>`;
  showVolumeInfo(novel, volume);
  syncSelectsTo(novel, volume);
}
export async function showVolumeInfo(novel, volume) {
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
      if (f === 'main.md') return; 
      const row = document.createElement('div');
      row.className = 'file-row';
      row.innerHTML = `
        <span class="fr-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></span>
        <span class="fr-name">${f}</span>
        <div class="fr-actions">
          <button class="btn btn-ghost btn-sm" title="Open in editor" onclick="openInEditor('${novel}','${volume}','${f}')"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg></button>
        </div>
      `;
      row.addEventListener('click', () => openInEditor(novel, volume, f));
      fileListEl.appendChild(row);
    });
    if (fileListEl.children.length === 0) {
      fileListEl.innerHTML = '<div class="text-muted text-sm" style="padding:8px">No markdown files yet</div>';
    }
  } catch (e) {
    toast('Error loading files: ' + e.message, 'error');
  }
}
export async function openInEditor(novel, volume, filename) {
  if (filename === 'main.md') {
    toast('main.md can only be edited in the Metadata panel', 'error');
    return;
  }
  state.selectedNovel = novel;
  state.selectedVolume = volume;
  window.showPanel('editor');
  await window.syncSelectsTo(novel, volume);
  setSelectValue('editor-file-select', filename);
  await editorFileChange();
}
export function populateAllSelects() {
  const ids = ['scraper-novel', 'editor-novel-select', 'img-novel-select',
               'meta-novel-select', 'build-novel-select',
               'new-volume-novel', 'pdf2md-novel'];
  ids.forEach(id => populateSelect(id, state.novels, 'Select Novel'));
  if (state.selectedNovel) {
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = state.selectedNovel;
    });
  }
}
export async function loadVolumesForSelect(novelSelectId, volSelectId) {
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
