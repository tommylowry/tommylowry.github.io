import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';

export function usePlayerManagers(playerSlug, { year = null, week = null } = {}) {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!playerSlug) return;
    let active = true;
    setLoading(true);
    setError(null);

    const segments = [playerSlug];
    if (year != null) segments.push(String(year));
    if (week != null) segments.push(String(week));
    const path = `/get_aggregated_managers/${segments.join('/')}`;

    apiGet(path)
      .then(data => {
        if (!active) return;
        setManagers(Array.isArray(data) ? data : []);
      })
      .catch(e => active && setError(e.message))
      .finally(() => active && setLoading(false));

    return () => { active = false; };
  }, [playerSlug, year, week]);

  return { managers, loading, error };
}