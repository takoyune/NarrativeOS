import { loadVolumesForSelect } from './library.js';
import { state, setPendingAction, setPendingSelectTarget } from '../core/state.js';
import { api, GET, POST, DEL, sendLog } from '../core/api.js';
import { toast, openModal, closeModal, openLightbox, copyToClipboard , populateSelect } from '../core/utils.js';



export function initBuilderPanel() {
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
export async function buildNovelChange() {
  await loadVolumesForSelect('build-novel-select', 'build-volume-select');
}
document.getElementById('btn-build').addEventListener('click', startBuild);
export function setPhase(phaseId, status) {
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
export function resetPhases() {
  ['phase-audit','phase-format','phase-images','phase-compile','phase-done'].forEach(id => setPhase(id, 'idle'));
}
export function logBuild(msg, cls = '') {
  const log = document.getElementById('build-log');
  const line = document.createElement('span');
  if (cls) line.className = `bl-${cls}`;
  line.innerHTML = msg + '\n';
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}
export async function startBuild() {
  const novel  = document.getElementById('build-novel-select').value;
  const volume = document.getElementById('build-volume-select').value;
  if (!novel || !volume) { toast('Select novel and volume', 'error'); return; }
  const btn = document.getElementById('btn-build');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Building…';
  document.getElementById('build-log').textContent = '';
  const dlBtn = document.getElementById('btn-download-epub');
  if (dlBtn) dlBtn.classList.add('hidden');
  resetPhases();
  logBuild(`▶ Starting build: ${novel} / ${volume}`, 'info');
  logBuild(`  Python: running build_novel.py…`, 'info');
  const phases = ['phase-audit','phase-format','phase-images','phase-compile'];
  let currentPhaseIdx = -1;
  try {
    const response = await fetch('/api/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': window.API_KEY || '' },
      body: JSON.stringify({ novel, volume })
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let resData = {};
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line
      for (const line of lines) {
        if (!line.trim()) continue;
        const data = JSON.parse(line);
        if (data.error) {
           logBuild(data.error, 'err');
        } else if (data.done) {
           resData = data;
        } else if (data.stdout !== undefined) {
           const out = data.stdout.trimEnd();
           if (out.startsWith('PHASE:')) {
             const p = out.split(':')[1];
             if (currentPhaseIdx >= 0) setPhase(phases[currentPhaseIdx], 'done');
             currentPhaseIdx = phases.indexOf(`phase-${p}`);
             if (currentPhaseIdx >= 0) setPhase(phases[currentPhaseIdx], 'active');
           } else {
             const cls = out.includes('<svg') || out.includes('Done') ? 'ok'
               : out.includes('Warning') ? 'warn'
               : out.includes('Error') || out.includes('error') ? 'err' : '';
             logBuild(out, cls);
           }
        }
      }
    }
    
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);
        if (data.error) logBuild(data.error, 'err');
        else if (data.done) resData = data;
      } catch(e) {}
    }
    
    if (currentPhaseIdx >= 0) setPhase(phases[currentPhaseIdx], 'done');
    
    if (resData && resData.ok) {
      phases.forEach(p => setPhase(p, 'done'));
      setPhase('phase-done', 'done');
      logBuild(`\n<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>Build complete!`, 'ok');
      if (resData.epub_path) {
        logBuild(`📄 Output: ${resData.epub_path}`, 'info');
        if (resData.size_bytes && resData.size_bytes > 15 * 1024 * 1024) {
          const mb = (resData.size_bytes / (1024 * 1024)).toFixed(1);
          logBuild(`\n⚠️ WARNING: EPUB file is quite large (${mb} MB).`, 'warn');
          logBuild(`Large EPUBs (>15MB) may cause problems on older ereaders.`, 'warn');
          logBuild(`Consider setting Image Output Format to 'WebP' or lowering quality in Settings.`, 'warn');
        }
        const dlBtn = document.getElementById('btn-download-epub');
        if (dlBtn) {
          dlBtn.onclick = () => {
             const filename = resData.epub_path.split(/[\\/]/).pop();
             window.location.href = `/api/download/${filename}?token=${window.API_KEY}`;
          };
          dlBtn.classList.remove('hidden');
        }
      }
      toast('Build Complete!', 'success');
    } else {
      if (currentPhaseIdx >= 0) setPhase(phases[currentPhaseIdx], 'error');
      setPhase('phase-done', 'error');
      logBuild(`\n❌ Build failed. Check the log above for details.`, 'err');
      toast('Build failed', 'error');
    }
  } catch (e) {
    logBuild(e.message, 'err');
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><polygon points="5 3 19 12 5 21 5 3"/></svg> Build EPUB';
  }
}
