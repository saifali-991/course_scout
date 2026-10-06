import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { PlayIcon } from './Icons.jsx';
import AuthModal from './AuthModal.jsx';
import useAuth from '../hooks/useAuth.js';

const links = [
  { to: '/', label: 'Discover' },
  { to: '/categories', label: 'Categories' },
  { to: '/saved', label: 'Saved' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  // null = closed, 'login' | 'register' = which AuthModal tab to show
  const [authTab, setAuthTab] = useState(null);
  const { user, isAuthenticated, logout } = useAuth();

  const closeMenu = () => setOpen(false);

  return (
    <header className={`navbar ${open ? 'navbar--open' : ''}`}>
      <div className="container navbar__inner">
        <Link to="/" className="brand" onClick={closeMenu}>
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
              onClick={closeMenu}
            >
              {l.label}
            </NavLink>
          ))}
          {/* Desktop par .nav__signin chhupa deta hai ye (860px CSS) — burger
              menu ke andar se mobile users bhi sign in / sign out kar sakte hain. */}
          {isAuthenticated ? (
            <button
              type="button"
              className="nav__link nav__authlink"
              onClick={() => {
                closeMenu();
                logout();
              }}
            >
              Sign out
            </button>
          ) : (
            <button
              type="button"
              className="nav__link nav__authlink"
              onClick={() => {
                closeMenu();
                setAuthTab('login');
              }}
            >
              Sign in
            </button>
          )}
        </nav>

        <div className="nav__actions">
          {isAuthenticated ? (
            <>
              <span className="nav__user" title={user?.email || user?.username}>
                <span className="nav__avatar">
                  {(user?.username || '?').charAt(0).toUpperCase()}
                </span>
                <span className="nav__username">{user?.username}</span>
              </span>
              <button
                type="button"
                className="nav__signin"
                onClick={() => {
                  closeMenu();
                  logout();
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="nav__signin"
                onClick={() => {
                  closeMenu();
                  setAuthTab('login');
                }}
              >
                Sign in
              </button>
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => {
                  closeMenu();
                  setAuthTab('register');
                }}
              >
                Join free
              </button>
            </>
          )}
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

      {authTab && (
        <AuthModal initialTab={authTab} onClose={() => setAuthTab(null)} />
      )}
    </header>
  );
}
