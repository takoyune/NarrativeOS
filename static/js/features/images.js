import { loadVolumesForSelect } from './library.js';
import { state, setPendingAction, setPendingSelectTarget } from '../core/state.js';
import { api, GET, POST, DEL, sendLog } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from '../core/utils.js';


export function initImagesPanel() {
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
export async function imgNovelChange() {
  await loadVolumesForSelect('img-novel-select', 'img-volume-select');
}
export async function imgVolumeChange() {
  loadImages();
}
export async function loadImages() {
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
      const src = `/api/images/serve?path=${encodeURIComponent(relPath)}&token=${window.API_KEY || ''}`;
      card.innerHTML = `
        <img src="${src}" alt="${name}" loading="lazy"
             onerror="this.style.display='none'" style="cursor:pointer;" onclick="openLightbox('${src}')">
        <div class="img-label" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px;">
          <span title="${name}" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${name}</span>
          <button class="btn btn-ghost btn-sm" onclick="copyToClipboard('images/${name}')" title="Copy Markdown Path" style="padding: 2px 6px; margin-left: 4px;"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg></button>
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
export async function handleImageFiles(files) {
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
      const res = await fetch('/api/images/upload', { method: 'POST', headers: { 'X-API-Key': window.API_KEY || '' }, body: form });
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
let metaRawMode = false;
