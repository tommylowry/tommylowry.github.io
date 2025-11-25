import { useEffect, useState, useCallback } from 'react';

export function useAggregatedPlayers(year, week, manager) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sanitize = (m) => m.trim().replace(/\s+/g, '_');

  const fetchData = useCallback(() => {
    // Build path segments only for defined selections.
    const segments = [];
    if (year != null) segments.push(year);
    if (week != null) segments.push(week);
    if (manager != null) segments.push(manager);
    const url = '/get_aggregated_players' + (segments.length ? '/' + segments.join('/') : '');
    console.log('Fetching URL:', url);
    setLoading(true);
    setError(null);
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(json => setPlayers(Array.isArray(json) ? json : []))
      .catch(e => {
        setError(e.message);
        setPlayers([]);
      })
      .finally(() => setLoading(false));
  }, [year, week, manager]);

  useEffect(() => {
    fetchData(); // runs on mount and whenever year/week/manager change
  }, [fetchData]);

  return { players, loading, error, refetch: fetchData };
}