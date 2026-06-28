
window.addEventListener('unhandledrejection', (event) => {
  console.error("Unhandled Promise Rejection:", event.reason);
  import('./utils.js').then(({ toast }) => {
    toast(event.reason?.message || "An unexpected error occurred.", 'error');
  });
});
window.addEventListener('error', (event) => {
  console.error("Uncaught Error:", event.error);
  import('./utils.js').then(({ toast }) => {
    toast(`App crashed: ${event.message}`, 'error');
  });
});
import { state, pendingAction, pendingSelectTarget, setPendingAction, setPendingSelectTarget } from './core/state.js';
import { api, GET, POST, DEL, sendLog } from './core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from './core/utils.js';

import { loadLibrary, renderLibraryTree, loadVolumesInTree, updateStats, selectVolume, showVolumeInfo, openInEditor, populateAllSelects, loadVolumesForSelect, renameCurrentNovel, renameCurrentVolume } from './features/library.js';
import { highlightMarkdown, applyInline, syncScroll, syncScrollRight, updateHighlight, updateFrMatches, updateFrDisplay, saveMd, editorNovelChange, editorVolumeChange, editorFileChange, initEditorPanel, updateCharCount, updatePreview } from './features/editor.js';
import { initScraperPanel, scraperNovelChange, logScrape, renderBatchList } from './features/scraper.js';
import { initMetaPanel, parseMetaToForm, renderTocBuilder, addTocItemDOM, buildMetaFromForm, metaNovelChange, metaVolumeChange, loadMeta, saveMeta } from './features/metadata.js';
import { initBuilderPanel, setPhase, resetPhases, logBuild, buildNovelChange, startBuild } from './features/builder.js';
import { initImagesPanel, imgNovelChange, imgVolumeChange, loadImages, handleImageFiles } from './features/images.js';
import { initSettingsPanel, fetchLogs, applySettingsToForm, setVal, saveSettings } from './features/settings.js';
import { initPdf2mdPanel, pdf2mdNovelChange } from './features/pdf2md.js';

window.openModal = openModal;
window.closeModal = closeModal;
window.openLightbox = openLightbox;
window.copyToClipboard = copyToClipboard;
window.openInEditor = openInEditor;


window.scraperNovelChange = scraperNovelChange;
window.editorNovelChange = editorNovelChange;
window.editorVolumeChange = editorVolumeChange;
window.editorFileChange = editorFileChange;
window.imgNovelChange = imgNovelChange;
window.imgVolumeChange = imgVolumeChange;
window.metaNovelChange = metaNovelChange;
window.metaVolumeChange = metaVolumeChange;
window.buildNovelChange = buildNovelChange;
window.pdf2mdNovelChange = pdf2mdNovelChange;

window.renameCurrentNovel = renameCurrentNovel;
window.renameCurrentVolume = renameCurrentVolume;


window.showPanel = function(name) {
  document.querySelectorAll('#main .panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.rail-btn').forEach(n => n.classList.remove('active'));
  document.getElementById(`panel-${name}`)?.classList.add('active');
  document.querySelector(`.rail-btn[data-panel="${name}"]`)?.classList.add('active');
  state.currentPanel = name;
  if (name === 'scraper')  initScraperPanel();
  if (name === 'editor')   initEditorPanel();
  if (name === 'images')   initImagesPanel();
  if (name === 'metadata') initMetaPanel();
  if (name === 'builder')  initBuilderPanel();
  if (name === 'settings') initSettingsPanel();
  if (name === 'pdf2md')   initPdf2mdPanel();
};


window.syncSelectsTo = function(novel, volume) {
  const setSelectValue = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = val;
    const input = el.nextElementSibling?.querySelector('.custom-select-input');
    if (input) input.value = val;
  };
  const novelSelects = ['scraper-novel', 'editor-novel-select', 'img-novel-select',
                        'meta-novel-select', 'build-novel-select', 'pdf2md-novel'];
  novelSelects.forEach(id => {
    const el = document.getElementById(id);
    if (el && el.value !== novel) setSelectValue(id, novel);
  });
  const promises = [];
  promises.push(scraperNovelChange().then(() => setSelectValue('scraper-volume', volume)));
  promises.push(editorNovelChange().then(() => {
    setSelectValue('editor-volume-select', volume);
    return editorVolumeChange();
  }));
  promises.push(imgNovelChange().then(() => {
    setSelectValue('img-volume-select', volume);
    return imgVolumeChange();
  }));
  promises.push(metaNovelChange().then(() => {
    setSelectValue('meta-volume-select', volume);
    return metaVolumeChange();
  }));
  promises.push(buildNovelChange().then(() => setSelectValue('build-volume-select', volume)));
  promises.push(pdf2mdNovelChange().then(() => setSelectValue('pdf2md-volume', volume)));
  
  return Promise.all(promises);
};

document.querySelectorAll('.rail-btn').forEach(item => {
  item.addEventListener('click', () => {
    const targetPanel = item.dataset.panel;
    if (!targetPanel) return;
    if (state.mdDirty && state.currentPanel === 'editor' && targetPanel !== 'editor') {
      setPendingAction(() => showPanel(targetPanel));
      openModal('modal-unsaved-changes');
      return;
    }
    showPanel(targetPanel);
  });
});
document.getElementById('btn-epub-preview').addEventListener('click', () => {
  state.epubPreviewMode = !state.epubPreviewMode;
  const preview = document.getElementById('md-preview');
  const btn = document.getElementById('btn-epub-preview');
  if (state.epubPreviewMode) {
    preview.classList.add('epub-mode');
    btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:4px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>EPUB View: ON';
    btn.classList.add('active');
    preview.style.setProperty('--epub-font-size', '1.0em');
    preview.style.setProperty('--epub-line-height', '1.8');
    preview.style.setProperty('--epub-text-indent', '1.5em');
  } else {
    preview.classList.remove('epub-mode');
    btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:4px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>EPUB View: OFF';
    btn.classList.remove('active');
  }
});
document.getElementById('btn-unsaved-cancel').addEventListener('click', () => {
  setPendingAction(null);
  setPendingSelectTarget(null);
  closeModal('modal-unsaved-changes');
});
document.getElementById('btn-unsaved-discard').addEventListener('click', () => {
  state.mdDirty = false;
  closeModal('modal-unsaved-changes');
  if (pendingSelectTarget) {
    document.getElementById('editor-file-select').value = pendingSelectTarget;
  }
  if (pendingAction) pendingAction();
  setPendingAction(null);
  setPendingSelectTarget(null);
});
document.getElementById('btn-unsaved-save').addEventListener('click', async () => {
  await saveMd(); 
  state.mdDirty = false;
  closeModal('modal-unsaved-changes');
  if (pendingSelectTarget) {
    document.getElementById('editor-file-select').value = pendingSelectTarget;
  }
  if (pendingAction) pendingAction();
  setPendingAction(null);
  setPendingSelectTarget(null);
});
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});
function setSelectValue(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = val;
  const input = el.nextElementSibling?.querySelector('.custom-select-input');
  if (input) input.value = val;
}
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
async function boot() {
  try {
    const data = await GET('/api/settings');
    const theme = (data.styling && data.styling.theme) || 'zinc-purple';
    document.documentElement.setAttribute('data-theme', theme);
  } catch(e) {}
  await loadLibrary();
  toast('NarrativeOS ready', 'info', 2000);
}
boot();




const detailPanel = document.getElementById('detailPanel');
const collapseBtn = document.getElementById('collapseBtn');
let panelCollapsed = false;
collapseBtn?.addEventListener('click', () => {
  panelCollapsed = !panelCollapsed;
  if (panelCollapsed) {
    detailPanel.classList.add('collapsed');
  } else {
    detailPanel.classList.remove('collapsed');
  }
});

document.getElementById('searchInput')?.addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#library-tree .menu-item').forEach(item => {
    const lbl = item.querySelector('.menu-label');
    if (!lbl) return;
    const match = lbl.textContent.toLowerCase().includes(q);
    item.style.display = (!q || match) ? '' : 'none';
  });
});

window.addEventListener('beforeunload', e => {
  if (state.mdDirty) {
    e.preventDefault();
    e.returnValue = '';
  }
});
