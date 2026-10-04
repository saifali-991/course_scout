import { useEffect, useRef, useState } from 'react';
import { FilterIcon, ChevronDown } from './Icons.jsx';
import { Spinner } from './Loader.jsx';

/**
 * "All topics" filter dropdown fed by /api/categories/
 *
 * `loading` is true while that request is in flight — until then the list is
 * legitimately empty, so we show a spinner row instead of a blank menu.
 */
export default function TopicsDropdown({ topics, value, onChange, loading = false }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const active = topics.find((t) => t.slug === value);

  return (
    <div className="dropdown" ref={ref}>
      <button className="dropdown__btn" onClick={() => setOpen((v) => !v)}>
        <FilterIcon size={16} />
        {active ? active.name : 'All topics'}
        {loading ? (
          <Spinner size={15} className="dropdown__spinner" />
        ) : (
          <ChevronDown size={16} className={`chev ${open ? 'chev--open' : ''}`} />
        )}
      </button>

      {open && (
        <div className="dropdown__menu">
          {loading && topics.length === 0 ? (
            <div className="dropdown__item dropdown__item--muted dropdown__item--loading">
              <Spinner size={15} />
              Loading topics…
            </div>
          ) : (
            <>
              <button
                className={`dropdown__item ${!value ? 'dropdown__item--active' : ''}`}
                onClick={() => {
                  onChange('');
                  setOpen(false);
                }}
              >
                All topics
              </button>
              {topics.map((t) => (
                <button
                  key={t.slug}
                  className={`dropdown__item ${value === t.slug ? 'dropdown__item--active' : ''}`}
                  onClick={() => {
                    onChange(t.slug);
                    setOpen(false);
                  }}
                >
                  {t.name}
                  <span className="dropdown__count">{t.course_count?.toLocaleString()}</span>
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
