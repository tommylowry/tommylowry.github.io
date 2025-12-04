import React, { useState, useEffect } from 'react';
import './App.css';
import { useAggregatedPlayers } from './hooks/useAggregatedPlayers';
import { PlayerRow } from './components/PlayerRow';
import { fetchOptions } from './services/options';
import { BrowserRouter as Router, Routes, Route, useSearchParams } from 'react-router-dom';
import PlayerPage from './pages/PlayerPage';
import Layout from './components/Layout';

function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize from URL params or defaults
  const [year, setYear] = useState(searchParams.get('year') || '2025');
  const [week, setWeek] = useState(searchParams.get('week') ? parseInt(searchParams.get('week')) : null);
  const [manager, setManager] = useState(searchParams.get('manager') || null);
  const [positionFilter, setPositionFilter] = useState(searchParams.get('position') || 'ALL');

  // Fetch filter options
  const [options, setOptions] = useState({ seasons: [], weeks: [], managers: [] });
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [optionsError, setOptionsError] = useState(null);

  useEffect(() => {
    setOptionsLoading(true);
    fetchOptions()
      .then(data => setOptions(data))
      .catch(e => setOptionsError(e.message))
      .finally(() => setOptionsLoading(false));
  }, []);

  const { players, loading, error } = useAggregatedPlayers(year, week, manager);

  // Update URL when filters change
  useEffect(() => {
    const params = {};
    if (year) params.year = year;
    if (week) params.week = week;
    if (manager) params.manager = manager;
    if (positionFilter && positionFilter !== 'ALL') params.position = positionFilter;
    setSearchParams(params, { replace: true });
  }, [year, week, manager, positionFilter, setSearchParams]);

  const [sortKey, setSortKey] = useState('ffWAR');
  const [sortDir, setSortDir] = useState('desc');

  const toggleSort = (key) => {
    setSortKey(prev => key);
    setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
  };

  const filteredPlayers = positionFilter === 'ALL'
    ? players
    : players.filter(p => p.position === positionFilter);

  // Added: normalize games started for consistent sorting/display
  const normalizedPlayers = filteredPlayers.map(p => ({
    ...p,
    num_games_started: Number(p.num_games_started ?? p.games_started ?? p.started ?? 0),
  }));

  const sortedPlayers = [...normalizedPlayers].sort((a, b) => {
    const dir = sortDir === 'asc' ? 1 : -1;
    let av = a[sortKey];
    let bv = b[sortKey];
    // normalize for string comparison
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  // Generate dynamic header based on filters
  const getHeaderText = () => {
    const parts = [];
    if (manager) parts.push(manager);
    if (year) parts.push(year);
    if (week) parts.push(`week ${week}`);

    // Add position with pluralization if not ALL
    if (positionFilter !== 'ALL') {
      const playerCount = filteredPlayers.length;
      if (playerCount === 1) {
        parts.push(positionFilter);
      } else if (playerCount > 1) {
        // Pluralize position
        parts.push(positionFilter + 's');
      }
    }

    return parts.length > 0 ? parts.join(' ') : 'All Data';
  };

  return (
    <div className="App">
      {/* Title centered */}
      <h2 style={{ margin: '1rem 0', fontWeight: 600 }}>
        {getHeaderText()}
      </h2>

      {/* Inline filters centered */}
      <div style={{ marginBottom: '1.5rem', maxWidth: '900px', margin: '0 auto 1.5rem' }}>
        {/* Season Filter */}
        <section style={{ marginBottom: '1rem' }}>
          <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Season</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                background: year === null ? 'var(--accent)' : 'var(--bg-alt)',
                padding: '6px 12px',
                borderRadius: 4,
                cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                fontSize: 14,
                opacity: optionsLoading || optionsError ? 0.5 : 1
              }}
            >
              <input
                type="radio"
                name="year"
                checked={year === null}
                onChange={() => setYear(null)}
                disabled={optionsLoading || optionsError}
                style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
              />
              ALL
            </label>
            {options.seasons.map(y => (
              <label
                key={y}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  background: year === y ? 'var(--accent)' : 'var(--bg-alt)',
                  padding: '6px 12px',
                  borderRadius: 4,
                  cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                  fontSize: 14,
                  opacity: optionsLoading || optionsError ? 0.5 : 1
                }}
              >
                <input
                  type="radio"
                  name="year"
                  checked={year === y}
                  onChange={() => setYear(y)}
                  disabled={optionsLoading || optionsError}
                  style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
                />
                {y}
              </label>
            ))}
          </div>
        </section>

        {/* Week Filter */}
        <section style={{ marginBottom: '1rem' }}>
          <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Week</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                background: week === null ? 'var(--accent)' : 'var(--bg-alt)',
                padding: '6px 12px',
                borderRadius: 4,
                cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                fontSize: 14,
                opacity: optionsLoading || optionsError ? 0.5 : 1
              }}
            >
              <input
                type="radio"
                name="week"
                checked={week === null}
                onChange={() => setWeek(null)}
                disabled={optionsLoading || optionsError}
                style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
              />
              ALL
            </label>
            {options.weeks.map(w => (
              <label
                key={w}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  background: week === w ? 'var(--accent)' : 'var(--bg-alt)',
                  padding: '6px 12px',
                  borderRadius: 4,
                  cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                  fontSize: 14,
                  opacity: optionsLoading || optionsError ? 0.5 : 1
                }}
              >
                <input
                  type="radio"
                  name="week"
                  checked={week === w}
                  onChange={() => setWeek(w)}
                  disabled={optionsLoading || optionsError}
                  style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
                />
                {w}
              </label>
            ))}
          </div>
        </section>

        {/* Manager Filter */}
        <section style={{ marginBottom: '1rem' }}>
          <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Manager</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                background: manager === null ? 'var(--accent)' : 'var(--bg-alt)',
                padding: '6px 12px',
                borderRadius: 4,
                cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                fontSize: 14,
                opacity: optionsLoading || optionsError ? 0.5 : 1
              }}
            >
              <input
                type="radio"
                name="manager"
                checked={manager === null}
                onChange={() => setManager(null)}
                disabled={optionsLoading || optionsError}
                style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
              />
              ALL
            </label>
            {options.managers.map(m => (
              <label
                key={m}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  background: manager === m ? 'var(--accent)' : 'var(--bg-alt)',
                  padding: '6px 12px',
                  borderRadius: 4,
                  cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer',
                  fontSize: 14,
                  opacity: optionsLoading || optionsError ? 0.5 : 1
                }}
              >
                <input
                  type="radio"
                  name="manager"
                  checked={manager === m}
                  onChange={() => setManager(m)}
                  disabled={optionsLoading || optionsError}
                  style={{ cursor: optionsLoading || optionsError ? 'not-allowed' : 'pointer' }}
                />
                {m}
              </label>
            ))}
          </div>
        </section>

        {/* Position Filter */}
        <section>
          <strong style={{ display: 'block', marginBottom: '0.5rem' }}>Position</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            {['ALL', 'QB', 'RB', 'WR', 'TE', 'DEF', 'K'].map(pos => (
              <label
                key={pos}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  background: positionFilter === pos ? 'var(--accent)' : 'var(--bg-alt)',
                  padding: '6px 12px',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: 14
                }}
              >
                <input
                  type="radio"
                  name="position"
                  checked={positionFilter === pos}
                  onChange={() => setPositionFilter(pos)}
                  style={{ cursor: 'pointer' }}
                />
                {pos}
              </label>
            ))}
          </div>
        </section>
      </div>

      {players.length > 0 && (
        <div className="table-wrapper">
          {loading && <div className="loading-overlay">Loading...</div>}
          <table style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('key')}>
                  Player {sortKey === 'key' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('position')}>
                  Pos {sortKey === 'position' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_points')}>
                  Points {sortKey === 'total_points' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('num_games_started')}>
                  Games Started {sortKey === 'num_games_started' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR')}>
                  ffWAR {sortKey === 'ffWAR' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedPlayers.map((p, i) => (
                <PlayerRow key={i} player={p} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/player/:playerSlug" element={<PlayerPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
