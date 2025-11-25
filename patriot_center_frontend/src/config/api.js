export const API_BASE = (process.env.REACT_APP_API_BASE || 'https://academic-lauren-tommys-code-for-fun-d5473d9d.koyeb.app').replace(/\/+$/,'');

export function apiGet(path, params = {}) {
  const url = new URL(API_BASE + path);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  });
  return fetch(url.toString(), { headers: { Accept: 'application/json' } })
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

export function sanitizeManager(m) {
  return String(m).trim().replace(/\s+/g, '_');
}