import React, { useState } from 'react';
import './App.css';
import { useAggregatedPlayers } from './hooks/useAggregatedPlayers';
import { PlayerRow } from './components/PlayerRow';
import { FilterDropdown } from './components/FilterDropdown';

function App() {
  // committed values (null means ALL)
  const [year, setYear] = useState('2025');
  const [week, setWeek] = useState(null);      // ALL weeks
  const [manager, setManager] = useState(null); // ALL managers

  // dropdown draft handled inside component; we just update committed via onChange
  const { players, loading, error } = useAggregatedPlayers(year, week, manager);

  const [sortKey, setSortKey] = useState('key');
  const [sortDir, setSortDir] = useState('asc');
  const [positionFilter, setPositionFilter] = useState('ALL');

  const toggleSort = (key) => {
    setSortKey(prev => key);
    setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
  };

  const positions = ['ALL', ...Array.from(new Set(players.map(p => p.position)))];

  const filteredPlayers = positionFilter === 'ALL'
    ? players
    : players.filter(p => p.position === positionFilter);

  const sortedPlayers = [...filteredPlayers].sort((a, b) => {
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

  const onApplyFilters = (sel) => {
    setYear(sel.year);
    setWeek(sel.week);
    setManager(sel.manager);
  };

  return (
    <div className="App">
      <h1>Aggregated Players</h1>
      <FilterDropdown
        value={{ year, week, manager }}
        onChange={onApplyFilters}
        loadingExternal={loading}
      />
      <div style={{ marginBottom: '0.75rem' }}>
        <label>
          Position:{' '}
          <select value={positionFilter} onChange={e => setPositionFilter(e.target.value)}>
            {positions.map(pos => (
              <option key={pos} value={pos}>{pos}</option>
            ))}
          </select>
        </label>
      </div>
      {players.length > 0 && (
        <div className="table-wrapper">
          {loading && <div className="loading-overlay">Loading...</div>}
          <table style={{ borderCollapse: 'collapse', width: '100%', maxWidth: '600px' }}>
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

export default App;
