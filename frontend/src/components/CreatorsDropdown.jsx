import { useEffect, useRef, useState } from 'react';
import { ChevronDown } from './Icons.jsx';
import { Spinner } from './Loader.jsx';

/**
 * Channel filter for the YouTube tab — fed by /api/creators/?platform=youtube.
 *
 * The API already sorts hand-picked top creators first, so the list reads
 * "Top creators" → CodeWithHarry / codebasics / … → everyone else by size.
 * Picking a channel writes ?creator=<name>; "Top creators" writes ?top=1.
 *
 * `loading` is true while /api/creators/ is in flight: an empty list at that
 * point means "not here yet", not "no creators", so we show a spinner row.
 */
export default function CreatorsDropdown({
  creators = [],
  value = '',
  topActive = false,
  onChange = () => {},
  onToggleTop = () => {},
  label = 'All creators',
  loading = false,
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const active = creators.find((c) => c.name === value);
  const shown = topActive ? 'Top creators' : active ? active.name : label;
  const visible = creators.slice(0, 60);

  const pick = (fn) => {
    fn();
    setOpen(false);
  };

  return (
    <div className="dropdown" ref={ref}>
      <button className="dropdown__btn" onClick={() => setOpen((v) => !v)}>
        {topActive && <span aria-hidden="true">★</span>}
        {shown}
        {loading ? (
          <Spinner size={15} className="dropdown__spinner" />
        ) : (
          <ChevronDown size={16} className={`chev ${open ? 'chev--open' : ''}`} />
        )}
      </button>

      {open && (
        <div className="dropdown__menu">
          {loading && creators.length === 0 ? (
            <div className="dropdown__item dropdown__item--muted dropdown__item--loading">
              <Spinner size={15} />
              Loading channels…
            </div>
          ) : (
            <>
          <button
            className={`dropdown__item ${!value && !topActive ? 'dropdown__item--active' : ''}`}
            onClick={() => pick(() => onChange(''))}
          >
            {label}
          </button>
          <button
            className={`dropdown__item dropdown__item--top ${topActive ? 'dropdown__item--active' : ''}`}
            onClick={() => pick(() => onToggleTop(!topActive))}
          >
            ★ Top creators only
            <span className="dropdown__count">
              {creators.filter((c) => c.is_top).length} channels
            </span>
          </button>
          <hr className="dropdown__sep" />
          {visible.map((c) => (
            <button
              key={c.name}
              className={`dropdown__item ${value === c.name ? 'dropdown__item--active' : ''}`}
              onClick={() => pick(() => onChange(c.name))}
              title={c.languages?.includes('hi') ? 'Hindi + English' : c.name}
            >
              {c.is_top && <span aria-hidden="true">★</span>} {c.name}
              <span className="dropdown__count">{c.count?.toLocaleString()}</span>
            </button>
          ))}
          {creators.length > visible.length && (
            <div className="dropdown__item dropdown__item--muted">
              +{creators.length - visible.length} more channels
            </div>
          )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
