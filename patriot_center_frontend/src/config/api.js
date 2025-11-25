const DEFAULT_BASE = 'https://academic-lauren-tommys-code-for-fun-d5473d9d.koyeb.app';
const rawBase = process.env.REACT_APP_API_BASE;
const BASE = (
  rawBase && rawBase.trim() && !/localhost|127\.0\.0\.1/i.test(rawBase)
    ? rawBase.trim()
    : DEFAULT_BASE
).replace(/\/+$/, '');

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