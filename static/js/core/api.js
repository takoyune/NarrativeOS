export async function api(method, url, body) {
  const opts = { method, headers: { 'X-API-Key': window.API_KEY || '' } };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(url, opts);
  } catch (err) {
    throw new Error(`Network Error: Cannot connect to server (${err.message})`);
  }
  if (!res.ok) {
    let errDetail = res.statusText;
    try {
      const err = await res.json();
      errDetail = err.error || err.detail || res.statusText;
    } catch(e) {}
    throw new Error(`Server Error (${res.status}): ${errDetail}`);
  }
  try {
    return await res.json();
  } catch (err) {
    throw new Error(`Invalid Response: Server returned malformed data.`);
  }
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
