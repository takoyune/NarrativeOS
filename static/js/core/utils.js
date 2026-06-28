import { sendLog } from './api.js';

export function toast(msg, type = 'info', duration = 3500) {
  if (type === 'error' || type === 'success') {
    sendLog(type, msg);
  }
  const icons = { success: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>', error: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>', info: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:text-bottom;margin-right:6px;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'}</span><span>${msg}</span>`;
  const hideToast = () => {
    if (el.classList.contains('leaving')) return; 
    el.classList.add('leaving');
    setTimeout(() => el.remove(), 400); 
  };
  el.addEventListener('click', hideToast);
  el.style.cursor = 'pointer';
  document.getElementById('toast-container').appendChild(el);
  const displayTime = type === 'error' ? 10000 : duration;
  setTimeout(hideToast, displayTime);
}
export function openModal(id)  { document.getElementById(id).classList.add('open'); }
export function closeModal(id) { document.getElementById(id).classList.remove('open'); }
export function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  openModal('modal-lightbox');
}
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast('Copied to clipboard', 'success');
  } catch (e) {
    toast('Failed to copy', 'error');
  }
}
export function populateSelect(selectId, items, emptyLabel = '—') {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  const prev = sel.value;
  sel.innerHTML = `<option value="">— ${emptyLabel} —</option>` +
    items.map(i => `<option value="${i.replace(/"/g, '&quot;')}">${i}</option>`).join('');
  if (items.includes(prev)) sel.value = prev;
  sel.style.display = 'none';
  let wrapper = sel.nextElementSibling;
  if (wrapper && wrapper.classList.contains('custom-select-wrapper')) {
    wrapper.remove();
  }
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
      optEl.addEventListener('mousedown', (e) => { 
        e.preventDefault();
        sel.value = o.value;
        input.value = o.value ? o.label : '';
        dropdown.classList.remove('open');
        wrapper.style.zIndex = '';
        sel.dispatchEvent(new Event('change'));
        input.blur(); 
      });
      dropdown.appendChild(optEl);
    });
  };
  input.addEventListener('focus', () => {
    input.value = ''; 
    renderDropdown('');
    dropdown.classList.add('open');
    wrapper.style.zIndex = '9999';
  });
  input.addEventListener('click', () => {
    if (!dropdown.classList.contains('open')) {
      input.value = '';
      renderDropdown('');
      dropdown.classList.add('open');
      wrapper.style.zIndex = '9999';
    }
  });
  input.addEventListener('blur', () => {
    dropdown.classList.remove('open');
    wrapper.style.zIndex = '';
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

export function setSelectValue(selectId, value) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.value = value;
  const wrapper = sel.nextElementSibling;
  if (wrapper && wrapper.classList.contains('custom-select-wrapper')) {
    const input = wrapper.querySelector('.custom-select-input');
    if (input) {
      const selectedOpt = Array.from(sel.options).find(o => o.value === value);
      input.value = selectedOpt ? selectedOpt.textContent : (value || '');
    }
  }
}

export function upgradeStaticSelect(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.style.display = 'none';
  let wrapper = sel.nextElementSibling;
  if (wrapper && wrapper.classList.contains('custom-select-wrapper')) {
    wrapper.remove();
  }
  wrapper = document.createElement('div');
  wrapper.className = 'custom-select-wrapper';
  const input = document.createElement('input');
  input.className = 'custom-select-input';
  input.type = 'text';
  input.readOnly = true;
  input.style.cursor = 'pointer';
  const selectedOpt = Array.from(sel.options).find(o => o.value === sel.value) || sel.options[0];
  input.value = selectedOpt ? selectedOpt.textContent : ''; 
  const arrow = document.createElement('div');
  arrow.className = 'custom-select-arrow';
  arrow.innerHTML = '▼';
  const dropdown = document.createElement('div');
  dropdown.className = 'custom-select-dropdown';
  
  const allOptions = Array.from(sel.options).map(opt => ({ value: opt.value, label: opt.textContent }));
  
  const renderDropdown = () => {
    dropdown.innerHTML = '';
    allOptions.forEach(o => {
      const optEl = document.createElement('div');
      optEl.className = 'custom-select-option';
      if (o.value === sel.value) optEl.classList.add('selected');
      optEl.textContent = o.label;
      optEl.addEventListener('mousedown', (e) => { 
        e.preventDefault();
        sel.value = o.value;
        input.value = o.label;
        dropdown.classList.remove('open');
        wrapper.classList.remove('open');
        wrapper.style.zIndex = '';
        sel.dispatchEvent(new Event('change'));
        input.blur();
      });
      dropdown.appendChild(optEl);
    });
  };
  
  input.addEventListener('focus', () => {
    renderDropdown();
    dropdown.classList.add('open');
    wrapper.classList.add('open');
    wrapper.style.zIndex = '9999';
  });
  input.addEventListener('mousedown', (e) => {
    e.preventDefault(); 
    if (!dropdown.classList.contains('open')) {
      input.focus();
    } else {
      input.blur();
    }
  });
  input.addEventListener('blur', () => {
    dropdown.classList.remove('open');
    wrapper.classList.remove('open');
    wrapper.style.zIndex = '';
  });
  
  wrapper.appendChild(input);
  wrapper.appendChild(arrow);
  wrapper.appendChild(dropdown);
  sel.parentNode.insertBefore(wrapper, sel.nextSibling);
}

export function askConfirm(title, message, confirmBtnText = 'Confirm') {
  return new Promise((resolve) => {
    const modal = document.getElementById('modal-confirm');
    document.getElementById('modal-confirm-title').textContent = title;
    document.getElementById('modal-confirm-msg').textContent = message;
    document.getElementById('btn-confirm-ok').textContent = confirmBtnText;
    
    const cancelBtn = document.getElementById('btn-confirm-cancel');
    const okBtn = document.getElementById('btn-confirm-ok');
    
    const cleanup = () => {
      cancelBtn.removeEventListener('click', onCancel);
      okBtn.removeEventListener('click', onOk);
      closeModal('modal-confirm');
    };
    
    const onCancel = () => { cleanup(); resolve(false); };
    const onOk = () => { cleanup(); resolve(true); };
    
    cancelBtn.addEventListener('click', onCancel);
    okBtn.addEventListener('click', onOk);
    
    openModal('modal-confirm');
  });
}
