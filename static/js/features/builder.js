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
  resetPhases();
  logBuild(`▶ Starting build: ${novel} / ${volume}`, 'info');
  logBuild(`  Python: running build_novel.py…`, 'info');
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
      const cls = line.includes('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>') || line.includes('Done') ? 'ok'
        : line.includes('Warning') ? 'warn'
        : line.includes('Error') || line.includes('error') ? 'err' : '';
      logBuild(line, cls);
    });
    if (res.stderr) res.stderr.split('\n').filter(l => l.trim()).forEach(line => logBuild(line, 'err'));
    if (res.ok) {
      setPhase('phase-done', 'done');
      logBuild(`\n<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>Build complete!`, 'ok');
      if (res.epub_path) logBuild(`📄 Output: ${res.epub_path}`, 'info');
      toast('EPUB compiled successfully!', 'success', 5000);
    } else {
      setPhase('phase-done', 'error');
      phases.forEach(p => {
        if (document.getElementById(p)?.className.includes('active')) setPhase(p, 'error');
      });
      logBuild(`\n<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>Build failed (exit code ${res.returncode})`, 'err');
      toast('Build failed — check the log', 'error');
    }
  } catch (e) {
    clearInterval(phaseTimer);
    setPhase('phase-compile', 'error');
    setPhase('phase-done', 'error');
    logBuild(`\n<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>Error: ${e.message}`, 'err');
    toast('Build error: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Compile EPUB';
  }
}
let currentSettings = {};
