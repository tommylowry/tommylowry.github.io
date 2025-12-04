import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { displayFromSlug } from '../components/player/PlayerNameFormatter';
import { usePlayerManagers } from '../hooks/usePlayerManagers';
import { useMetaOptions } from '../hooks/useMetaOptions';

export default function PlayerPage() {
    const { playerSlug } = useParams();
    const slug = playerSlug || 'Amon-Ra_St._Brown'; // default capitalized
    const displayName = displayFromSlug(slug);

    const { years, weeksByYear, loading: optionsLoading, error: optionsError } = useMetaOptions();

    const [year, setYear] = useState(null);    // default: ALL years
    const [week, setWeek] = useState(null);      // default: ALL weeks
    const [imageError, setImageError] = useState(false);

    React.useEffect(() => {
        setWeek(null);
    }, [year]);

    const { managers, loading, error } = usePlayerManagers(slug, { year, week });

    // Extract player image URL from first manager object
    const playerImageUrl = managers?.[0]?.player_image_endpoint;

    // Reset image error when player changes
    React.useEffect(() => {
        setImageError(false);
    }, [playerImageUrl]);

    // Count playoff placements and track details for hover
    const { playoffCounts, playoffDetails } = React.useMemo(() => {
        const counts = { 1: 0, 2: 0, 3: 0 };
        const details = { 1: [], 2: [], 3: [] };

        managers.forEach(manager => {
            const managerName = manager.manager || manager.player || manager.key || '';
            // API returns flattened keys like "playoff_placement.PlayerName.2021": 1
            Object.keys(manager).forEach(key => {
                if (key.startsWith('playoff_placement.')) {
                    const placement = manager[key];
                    if (placement === 1 || placement === 2 || placement === 3) {
                        counts[placement]++;
                        // Extract year from key: "playoff_placement.PlayerName.2021" -> "2021"
                        const parts = key.split('.');
                        const year = parts[parts.length - 1];
                        details[placement].push({ manager: managerName, year });
                    }
                }
            });
        });

        // Sort details by year (descending)
        Object.keys(details).forEach(placement => {
            details[placement].sort((a, b) => b.year - a.year);
        });

        return { playoffCounts: counts, playoffDetails: details };
    }, [managers]);

    // Sorting state + helpers
    const [sortKey, setSortKey] = useState('ffWAR');
    const [sortDir, setSortDir] = useState('desc');
    const toggleSort = (key) => {
        setSortKey(prev => key);
        setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
    };

    // Normalize and sort managers
    const mrows = Array.isArray(managers) ? managers.map(m => {
        // Extract playoff placements for this specific manager
        const managerPlacements = { 1: [], 2: [], 3: [] };
        Object.keys(m).forEach(key => {
            if (key.startsWith('playoff_placement.')) {
                const placement = m[key];
                if (placement === 1 || placement === 2 || placement === 3) {
                    const parts = key.split('.');
                    const year = parts[parts.length - 1];
                    managerPlacements[placement].push(year);
                }
            }
        });

        return {
            manager: m.manager ?? m.player ?? m.key ?? '',
            total_points: Number(m.total_points ?? m.points ?? 0),
            num_games_started: Number(m.num_games_started ?? m.games_started ?? m.started ?? 0),
            ffWAR: Number(m.ffWAR ?? 0),
            placements: managerPlacements
        };
    }) : [];

    const sortedManagers = [...mrows].sort((a, b) => {
        const dir = sortDir === 'asc' ? 1 : -1;
        let av = a[sortKey];
        let bv = b[sortKey];
        if (typeof av === 'string') av = av.toLowerCase();
        if (typeof bv === 'string') bv = bv.toLowerCase();
        if (av < bv) return -1 * dir;
        if (av > bv) return 1 * dir;
        return 0;
    });

    // Fallback: handle year as string/number just in case
    const wk = (year != null)
        ? (weeksByYear[year] ?? [])
        : [];
    const availableWeeks = Array.isArray(wk) ? wk : [];

    if (process.env.NODE_ENV === 'development') {
        console.debug('years:', years, 'weeksByYear:', weeksByYear, 'year:', year, 'availableWeeks:', availableWeeks);
    }

    return (
        <div className="App" style={{ paddingTop: '1rem' }}>
            <style>{`
                .ribbon-tooltip {
                    position: relative;
                }
                .ribbon-tooltip::after {
                    content: attr(data-tooltip);
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0, 0, 0, 0.9);
                    color: white;
                    padding: 0.5rem 0.75rem;
                    border-radius: 6px;
                    font-size: 0.85rem;
                    white-space: pre-line;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.15s ease;
                    margin-bottom: 0.5rem;
                    z-index: 1000;
                    min-width: 150px;
                    text-align: center;
                }
                .ribbon-tooltip:hover::after {
                    opacity: 1;
                }
            `}</style>

            {/* Player Hero Section */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1.5rem',
                marginBottom: '2rem',
                padding: '1.5rem',
                background: 'var(--bg-alt)',
                borderRadius: '12px',
                border: '1px solid var(--border)'
            }}>
                {playerImageUrl && !imageError && (
                    <img
                        src={playerImageUrl}
                        alt={displayName}
                        onError={() => setImageError(true)}
                        style={{
                            width: '120px',
                            height: '120px',
                            objectFit: 'cover',
                            borderRadius: '12px',
                            border: '2px solid var(--border)',
                            backgroundColor: 'var(--bg)',
                            flexShrink: 0
                        }}
                    />
                )}
                <div style={{ flex: 1 }}>
                    <h1 style={{ margin: 0, marginBottom: '0.25rem' }}>{displayName}</h1>
                    {managers?.[0]?.position && (
                        <p style={{
                            margin: 0,
                            color: 'var(--muted)',
                            fontSize: '1.1rem',
                            fontWeight: 500
                        }}>
                            {managers[0].position}
                        </p>
                    )}
                </div>
                {/* Playoff Ribbons */}
                {(playoffCounts[1] > 0 || playoffCounts[2] > 0 || playoffCounts[3] > 0) && (
                    <div style={{
                        display: 'flex',
                        gap: '1rem',
                        alignItems: 'center',
                        flexShrink: 0
                    }}>
                        {playoffCounts[1] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.25rem',
                                position: 'relative'
                            }}>
                                <div
                                    className="ribbon-tooltip"
                                    data-tooltip={playoffDetails[1].map(d => `${d.year}: ${d.manager}`).join('\n')}
                                    style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🥇
                                </div>
                                <span style={{
                                    fontSize: '0.9rem',
                                    fontWeight: 600,
                                    color: 'var(--muted)'
                                }}>
                                    ×{playoffCounts[1]}
                                </span>
                            </div>
                        )}
                        {playoffCounts[2] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.25rem',
                                position: 'relative'
                            }}>
                                <div
                                    className="ribbon-tooltip"
                                    data-tooltip={playoffDetails[2].map(d => `${d.year}: ${d.manager}`).join('\n')}
                                    style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🥈
                                </div>
                                <span style={{
                                    fontSize: '0.9rem',
                                    fontWeight: 600,
                                    color: 'var(--muted)'
                                }}>
                                    ×{playoffCounts[2]}
                                </span>
                            </div>
                        )}
                        {playoffCounts[3] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.25rem',
                                position: 'relative'
                            }}>
                                <div
                                    className="ribbon-tooltip"
                                    data-tooltip={playoffDetails[3].map(d => `${d.year}: ${d.manager}`).join('\n')}
                                    style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🥉
                                </div>
                                <span style={{
                                    fontSize: '0.9rem',
                                    fontWeight: 600,
                                    color: 'var(--muted)'
                                }}>
                                    ×{playoffCounts[3]}
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>
            <p style={{ marginBottom: '1rem' }}>
                <Link to="/" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                    ← Back
                </Link>
            </p>
            <div style={{ display: 'inline-flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem', justifyContent: 'center' }}>
                <label>
                    Year:{' '}
                    <select
                        value={year ?? ''}
                        disabled={optionsLoading || optionsError}
                        onChange={e => setYear(e.target.value || null)}
                    >
                        <option value="">ALL</option>
                        {years.map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </label>
                <label>
                    Week:{' '}
                    <select
                        value={week ?? ''}
                        disabled={optionsLoading || optionsError || year == null}
                        onChange={e => setWeek(e.target.value ? Number(e.target.value) : null)}
                    >
                        <option value="">ALL</option>
                        {(year && Array.isArray(weeksByYear[year]) ? weeksByYear[year] : []).map(w => (
                            <option key={w} value={w}>{w}</option>
                        ))}
                    </select>
                </label>
            </div>

            {loading && <p>Loading manager breakdown...</p>}
            {error && !loading && <p style={{ color: 'var(--danger)' }}>{error}</p>}
            {!loading && !error && mrows.length === 0 && (
                <p style={{ color: 'var(--muted)' }}>No manager stats found.</p>
            )}

            {!loading && mrows.length > 0 && (
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('manager')}>
                                    Manager {sortKey === 'manager' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_points')}>
                                    Total Points {sortKey === 'total_points' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('num_games_started')}>
                                    Games Started {sortKey === 'num_games_started' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR')}>
                                    ffWAR {sortKey === 'ffWAR' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedManagers.map((m, i) => {
                                const warClass = m.ffWAR > 0 ? 'war-positive' : m.ffWAR < 0 ? 'war-negative' : 'war-neutral';
                                const hasPlacements = m.placements[1].length > 0 || m.placements[2].length > 0 || m.placements[3].length > 0;

                                return (
                                    <tr key={i}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span>{m.manager || '—'}</span>
                                                {hasPlacements && (
                                                    <div style={{ display: 'flex', gap: '0.15rem' }}>
                                                        {/* Show one ribbon per year for 1st place */}
                                                        {m.placements[1].map((year, idx) => (
                                                            <span
                                                                key={`1-${idx}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                                title={`1st Place: ${year}`}
                                                            >
                                                                🥇
                                                            </span>
                                                        ))}
                                                        {/* Show one ribbon per year for 2nd place */}
                                                        {m.placements[2].map((year, idx) => (
                                                            <span
                                                                key={`2-${idx}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                                title={`2nd Place: ${year}`}
                                                            >
                                                                🥈
                                                            </span>
                                                        ))}
                                                        {/* Show one ribbon per year for 3rd place */}
                                                        {m.placements[3].map((year, idx) => (
                                                            <span
                                                                key={`3-${idx}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                                title={`3rd Place: ${year}`}
                                                            >
                                                                🥉
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>{m.total_points}</td>
                                        <td>{m.num_games_started}</td>
                                        <td className={warClass}>{m.ffWAR}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}