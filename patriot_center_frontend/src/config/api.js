const DEFAULT_BASE = 'https://patriot-center-api.fly.dev';
const rawBase = process.env.REACT_APP_API_BASE;
const DEV_FALLBACK = 'http://localhost:8080';

const BASE = (
  rawBase && rawBase.trim()
    ? rawBase.trim()
    : (process.env.NODE_ENV === 'development' ? DEV_FALLBACK : DEFAULT_BASE)
).replace(/\/+$/, '');

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${BASE}${p}`;
}

export async function apiGet(path) {
  const url = path.startsWith('http') ? path : apiUrl(path);
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
  return encodeURIComponent(String(m).trim());
}

export { BASE };