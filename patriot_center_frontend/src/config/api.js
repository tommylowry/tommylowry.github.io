const BASE = (process.env.REACT_APP_API_BASE || 'http://localhost:8080').replace(/\/+$/, '');

export async function apiGet(path) {
  const url = path.startsWith('http') ? path : `${BASE}${path.startsWith('/') ? '' : '/'}${path}`;
  const res = await fetch(url, { credentials: 'omit' });
  const ct = res.headers.get('content-type') || '';
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`GET ${url} failed: ${res.status} ${res.statusText} ${text.slice(0,80)}`);
  }
  if (!ct.includes('application/json')) {
    const text = await res.text().catch(() => '');
    throw new Error(`Non-JSON from ${url}: ${text.slice(0, 120)}`);
  }
  return res.json();
}

export function sanitizeManager(m) {
  if (m == null) return '';
  return encodeURIComponent(String(m).trim()); // remove toLowerCase
}