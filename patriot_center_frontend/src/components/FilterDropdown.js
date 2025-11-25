import React, { useEffect, useState } from 'react';
import { fetchOptions } from '../services/options';

export function FilterDropdown({ value, onChange, loadingExternal }) {
  // value shape: { year: number|null, week: number|null, manager: string|null }
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState({ seasons: [], weeks: [], managers: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // local draft selections
  const [draft, setDraft] = useState(value);

  useEffect(() => {
    setLoading(true);
    fetchOptions()
      .then(data => setOptions(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggleOpen = () => setOpen(o => !o);

  const selectSingle = (category, val) => {
    setDraft(d => ({
      ...d,
      [category]: d[category] === val ? null : val // click again to unset -> ALL
    }));
  };

  const apply = () => {
    onChange(draft); // commit selections
    setOpen(false);
  };

  const resetAll = () => {
    setDraft({ year: null, week: null, manager: null });
  };

  return (
    <div style={{ position: 'relative', marginBottom: '1rem' }}>
      <button
        type="button"
        onClick={toggleOpen}
        style={{
          background: 'var(--accent)',
          color: '#fff',
            border: 'none',
            padding: '8px 14px',
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 500
        }}
        disabled={loadingExternal}
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
                <strong>Season (one or ALL)</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
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
                        type="checkbox"
                        checked={draft.year === season}
                        onChange={() => selectSingle('year', season)}
                        style={{ cursor: 'pointer' }}
                      />
                      {season}
                    </label>
                  ))}
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
                      type="checkbox"
                      checked={draft.year === null}
                      onChange={() => selectSingle('year', null)}
                      style={{ cursor: 'pointer' }}
                    />
                    ALL
                  </label>
                </div>
              </section>

              <section style={{ marginBottom: 10 }}>
                <strong>Week (one or ALL)</strong>
                <div style={{ maxHeight: 120, overflowY: 'auto', paddingRight: 4 }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
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
                          type="checkbox"
                          checked={draft.week === w}
                          onChange={() => selectSingle('week', w)}
                          style={{ cursor: 'pointer' }}
                        />
                        {w}
                      </label>
                    ))}
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
                        type="checkbox"
                        checked={draft.week === null}
                        onChange={() => selectSingle('week', null)}
                        style={{ cursor: 'pointer' }}
                      />
                      ALL
                    </label>
                  </div>
                </div>
              </section>

              <section style={{ marginBottom: 10 }}>
                <strong>Manager (one or ALL)</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: 6 }}>
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
                        type="checkbox"
                        checked={draft.manager === m}
                        onChange={() => selectSingle('manager', m)}
                        style={{ cursor: 'pointer' }}
                      />
                      {m}
                    </label>
                  ))}
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
                      type="checkbox"
                      checked={draft.manager === null}
                      onChange={() => selectSingle('manager', null)}
                      style={{ cursor: 'pointer' }}
                    />
                    ALL
                  </label>
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
      <div style={{ marginTop: 6, fontSize: 12, color: 'var(--muted)' }}>
        Path preview: {['year','week','manager'].map(k => value[k] ?? 'ALL').join(' / ')}
      </div>
    </div>
  );
}