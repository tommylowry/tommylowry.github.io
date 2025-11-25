import { useEffect, useState } from 'react';

export function usePlayerManagers(playerSlug, { year = null, week = null } = {}) {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!playerSlug) return;
    let active = true;
    setLoading(true);
    setError(null);

    // playerSlug already capitalized and encoded (Amon-Ra_St._Brown, etc.)
    const segments = [playerSlug];
    if (year) segments.push(String(year));
    if (week) segments.push(String(week));
    const path = segments.join('/');

    fetch(`${process.env.REACT_APP_API_BASE}/get_aggregated_managers/${path}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (!active) return;
        // Endpoint returns flattened records (list of dicts)
        setManagers(Array.isArray(data) ? data : []);
      })
      .catch(e => active && setError(e.message))
      .finally(() => active && setLoading(false));

    return () => { active = false; };
  }, [playerSlug, year, week]);

  return { managers, loading, error };
}