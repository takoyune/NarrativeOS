export async function api(method, url, body) {
  const opts = { method, headers: { 'X-API-Key': window.API_KEY || '' } };
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
export const GET  = (url)        => api('GET', url);
export const POST = (url, body)  => api('POST', url, body);
export const DEL  = (url, body)  => api('DELETE', url, body);
export async function sendLog(level, message) {
  try {
    await fetch('/api/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': window.API_KEY || '' },
      body: JSON.stringify({ level, message })
    });
  } catch(e) {}
}
