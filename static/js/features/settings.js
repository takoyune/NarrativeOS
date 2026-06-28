import { state, setPendingAction, setPendingSelectTarget } from '../core/state.js';
import { api, GET, POST, DEL, sendLog } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard, upgradeStaticSelect } from '../core/utils.js';
let currentSettings = {};

export async function initSettingsPanel() {
  const scopeSelect = document.getElementById('settings-scope-select');
  scopeSelect.innerHTML = '<option value="">Global Settings</option>';
  state.novels.forEach(novel => {
    const opt = document.createElement('option');
    opt.value = novel;
    opt.textContent = 'Override: ' + novel;
    scopeSelect.appendChild(opt);
  });
  upgradeStaticSelect('settings-scope-select');
  
  scopeSelect.addEventListener('change', async () => {
    const isGlobal = scopeSelect.value === '';
    const cardsToHide = [
      document.getElementById('set-out-lang')?.closest('.card'),
      document.getElementById('set-ed-autosave')?.closest('.card'),
      document.getElementById('set-sys-maxlogs')?.closest('.card')
    ];
    cardsToHide.forEach(card => { if (card) card.style.display = isGlobal ? '' : 'none'; });
    await fetchSettings(scopeSelect.value);
  });

  await fetchSettings('');
}

async function fetchSettings(novel = '') {
  try {
    const url = novel ? `/api/settings?novel=${encodeURIComponent(novel)}` : '/api/settings';
    const data = await GET(url);
    currentSettings = data;
    applySettingsToForm(data);
    if (!novel) fetchLogs();
  } catch (e) {
    toast('Error loading settings: ' + e.message, 'error');
  }
}
export async function fetchLogs() {
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
export function applySettingsToForm(data) {
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
  setVal('set-sty-scenebreak', sty.scene_break_symbol || '* * *');
  setVal('set-sty-fontsize',   sty.font_size || '1.0');
  setVal('set-sty-lineheight', sty.line_height || '1.8');
  setVal('set-sty-indent',     sty.text_indent || '1.5');
  setVal('set-sty-theme',      sty.theme || 'zinc-purple');
  setVal('set-bld-autoconvert',  bld.auto_convert_images || 'true');
  setVal('set-bld-autocompress', bld.auto_compress || 'true');
  setVal('set-bld-download',     bld.download_online_images || 'true');
  setVal('set-bld-retries',      bld.download_retries || '3');
  setVal('set-bld-timeout',      bld.download_timeout || '30');
  const sys = data.Settings || {};
  setVal('set-sys-maxlogs',      sys.max_logs || '1000');
}
export function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}
document.getElementById('btn-save-settings').addEventListener('click', saveSettings);
document.getElementById('set-sty-theme').addEventListener('change', (e) => {
  document.documentElement.setAttribute('data-theme', e.target.value);
  saveSettings(); 
});
export async function saveSettings() {
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
      theme:                document.getElementById('set-sty-theme').value,
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
    const scope = document.getElementById('settings-scope-select').value;
    const reqBody = { settings: newSettings };
    if (scope) reqBody.novel = scope;
    
    await POST('/api/settings', reqBody);
    toast('Settings saved!', 'success');
  } catch (e) {
    toast('Save failed: ' + e.message, 'error');
  }
}
