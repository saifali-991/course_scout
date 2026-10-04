import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { PlayIcon } from './Icons.jsx';

const links = [
  { to: '/', label: 'Discover' },
  { to: '/categories', label: 'Categories' },
  { to: '/saved', label: 'Saved' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className={`navbar ${open ? 'navbar--open' : ''}`}>
      <div className="container navbar__inner">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand__mark">
            <PlayIcon size={18} />
          </span>
          <span>
            Course<span className="brand__text--blue">Scout</span>
          </span>
        </Link>

        <nav className="nav__links">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) => `nav__link ${isActive ? 'nav__link--active' : ''}`}
              onClick={() => setOpen(false)}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="nav__actions">
          <a className="nav__signin" href="#signin">
            Sign in
          </a>
          <a className="btn btn--primary" href="#join">
            Join free
          </a>
          <button
            className="nav__burger"
            aria-label="Toggle menu"
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {open ? (
                <>
                  <line x1="5" y1="5" x2="19" y2="19" />
                  <line x1="19" y1="5" x2="5" y2="19" />
                </>
              ) : (
                <>
                  <line x1="4" y1="7" x2="20" y2="7" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="17" x2="20" y2="17" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
