import React, { useEffect, useState } from 'react';
import { fetchOptions } from '../services/options';

export function FilterDropdown({ value, onChange, loadingExternal, positionFilter, onPositionChange }) {
  // value shape: { year: number|null, week: number|null, manager: string|null }
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState({ seasons: [], weeks: [], managers: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // local draft selections
  const [draft, setDraft] = useState(value);
  const [draftPosition, setDraftPosition] = useState(positionFilter);

  useEffect(() => {
    setLoading(true);
    fetchOptions()
      .then(data => setOptions(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggleOpen = () => setOpen(o => !o);

  const apply = () => {
    onChange(draft); // commit selections
    onPositionChange(draftPosition); // commit position selection
    setOpen(false);
  };

  const resetAll = () => {
    setDraft({ year: null, week: null, manager: null });
    setDraftPosition('ALL');
  };

  return (
    <div style={{ position: 'relative', marginBottom: '1rem' }}>
      <button
        type="button"
        onClick={toggleOpen}
        style={{
          background: 'var(--bg-alt)',
          color: 'var(--text)',
          border: '1px solid var(--border)',
          padding: '8px 14px',
          borderRadius: 6,
          cursor: 'pointer',
          fontWeight: 500,
          transition: 'all 0.2s'
        }}
        disabled={loadingExternal}
        onMouseEnter={(e) => e.target.style.borderColor = 'var(--accent)'}
        onMouseLeave={(e) => e.target.style.borderColor = 'var(--border)'}
      >
        Filters {open ? '▲' : '▼'}
      </button>
      {open && (
        <div
          style={{
            position: 'absolute',
            top: '110%',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--bg-alt)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '12px 16px',
            width: 320,
            boxShadow: '0 4px 14px -4px rgba(0,0,0,.7)',
            zIndex: 20
          }}
        >
          {loading && <p style={{ margin: 0 }}>Loading options...</p>}
          {error && <p style={{ color: 'var(--danger)' }}>Error: {error}</p>}
          {!loading && !error && (
            <>
              <section style={{ marginBottom: 10 }}>
                <strong>Season</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: draft.year === null ? 'var(--accent)' : 'var(--bg)',
                      padding: '4px 8px',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 12
                    }}
                  >
                    <input
                      type="radio"
                      name="year"
                      checked={draft.year === null}
                      onChange={() => setDraft(d => ({ ...d, year: null }))}
                      style={{ cursor: 'pointer' }}
                    />
                    ALL
                  </label>
                  {options.seasons.map(season => (
                    <label
                      key={season}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        background: draft.year === season ? 'var(--accent)' : 'var(--bg)',
                        padding: '4px 8px',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: 12
                      }}
                    >
                      <input
                        type="radio"
                        name="year"
                        checked={draft.year === season}
                        onChange={() => setDraft(d => ({ ...d, year: season }))}
                        style={{ cursor: 'pointer' }}
                      />
                      {season}
                    </label>
                  ))}
                </div>
              </section>

              <section style={{ marginBottom: 10 }}>
                <strong>Week</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: draft.week === null ? 'var(--accent)' : 'var(--bg)',
                      padding: '4px 8px',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 12
                    }}
                  >
                    <input
                      type="radio"
                      name="week"
                      checked={draft.week === null}
                      onChange={() => setDraft(d => ({ ...d, week: null }))}
                      style={{ cursor: 'pointer' }}
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
                        background: draft.week === w ? 'var(--accent)' : 'var(--bg)',
                        padding: '4px 8px',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: 12
                      }}
                    >
                      <input
                        type="radio"
                        name="week"
                        checked={draft.week === w}
                        onChange={() => setDraft(d => ({ ...d, week: w }))}
                        style={{ cursor: 'pointer' }}
                      />
                      {w}
                    </label>
                  ))}
                </div>
              </section>

              <section style={{ marginBottom: 10 }}>
                <strong>Manager</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      background: draft.manager === null ? 'var(--accent)' : 'var(--bg)',
                      padding: '4px 8px',
                      borderRadius: 4,
                      cursor: 'pointer',
                      fontSize: 12
                    }}
                  >
                    <input
                      type="radio"
                      name="manager"
                      checked={draft.manager === null}
                      onChange={() => setDraft(d => ({ ...d, manager: null }))}
                      style={{ cursor: 'pointer' }}
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
                        background: draft.manager === m ? 'var(--accent)' : 'var(--bg)',
                        padding: '4px 8px',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: 12
                      }}
                    >
                      <input
                        type="radio"
                        name="manager"
                        checked={draft.manager === m}
                        onChange={() => setDraft(d => ({ ...d, manager: m }))}
                        style={{ cursor: 'pointer' }}
                      />
                      {m}
                    </label>
                  ))}
                </div>
              </section>

              <section style={{ marginBottom: 10 }}>
                <strong>Position</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
                  {['ALL', 'QB', 'RB', 'WR', 'TE', 'DEF', 'K'].map(pos => (
                    <label
                      key={pos}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        background: draftPosition === pos ? 'var(--accent)' : 'var(--bg)',
                        padding: '4px 8px',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: 12
                      }}
                    >
                      <input
                        type="radio"
                        name="position"
                        checked={draftPosition === pos}
                        onChange={() => setDraftPosition(pos)}
                        style={{ cursor: 'pointer' }}
                      />
                      {pos}
                    </label>
                  ))}
                </div>
              </section>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                <button
                  type="button"
                  onClick={resetAll}
                  style={{
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    padding: '6px 12px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontSize: 12
                  }}
                >
                  Clear
                </button>
                <button
                  type="button"
                  onClick={apply}
                  style={{
                    background: 'var(--accent)',
                    border: 'none',
                    color: '#fff',
                    padding: '6px 12px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: 500
                  }}
                >
                  Apply
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}