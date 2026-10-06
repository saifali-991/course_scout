import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertIcon, PlayIcon } from './Icons.jsx';
import useAuth from '../hooks/useAuth.js';

/**
 * Sign in / Join free dialog — opened from the Navbar buttons.
 *
 * Two tabs share one card; submitting calls useAuth().login/register, which
 * stores the DRF token and flips the Navbar to the signed-in state. Errors
 * (wrong password, username taken, backend down) render inline under the form.
 */
export default function AuthModal({ initialTab = 'login', onClose }) {
  const { login, register } = useAuth();
  const [tab, setTab] = useState(initialTab === 'register' ? 'register' : 'login');
  const [identifier, setIdentifier] = useState(''); // login: username or email
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // Escape closes the dialog; body scroll locks while it's open.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  const switchTab = (next) => {
    setTab(next);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setError('');
    setBusy(true);
    try {
      if (tab === 'login') {
        await login(identifier.trim(), password);
      } else {
        await register({
          username: username.trim(),
          email: email.trim(),
          password,
        });
      }
      onClose();
    } catch (err) {
      setError(err?.message || 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  // Portal out of <header> — the navbar's `backdrop-filter` would otherwise
  // become the containing block for this position:fixed backdrop and clip the
  // modal to the 76px-tall header.
  return createPortal(
    <div
      className="authmodal__backdrop"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="authmodal" role="dialog" aria-modal="true" aria-label="Account">
        <button type="button" className="authmodal__close" aria-label="Close" onClick={onClose}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="6" y1="6" x2="18" y2="18" />
            <line x1="18" y1="6" x2="6" y2="18" />
          </svg>
        </button>

        <span className="authmodal__mark">
          <PlayIcon size={18} />
        </span>

        <div className="authmodal__tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'login'}
            className={`authmodal__tab ${tab === 'login' ? 'authmodal__tab--active' : ''}`}
            onClick={() => switchTab('login')}
          >
            Sign in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'register'}
            className={`authmodal__tab ${tab === 'register' ? 'authmodal__tab--active' : ''}`}
            onClick={() => switchTab('register')}
          >
            Join free
          </button>
        </div>

        <h2 className="authmodal__title">
          {tab === 'login' ? 'Welcome back' : 'Create your account'}
        </h2>
        <p className="authmodal__subtitle">
          {tab === 'login'
            ? 'Sign in to pick up where you left off.'
            : 'Free forever — save courses and get recommendations.'}
        </p>

        <form className="authmodal__form" onSubmit={handleSubmit}>
          {tab === 'login' ? (
            <label className="authmodal__field">
              <span>Username or email</span>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="e.g. harry or harry@example.com"
                autoComplete="username"
                required
                autoFocus
              />
            </label>
          ) : (
            <>
              <label className="authmodal__field">
                <span>Username</span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="letters and numbers only"
                  autoComplete="username"
                  pattern="[A-Za-z0-9]+"
                  title="Username can only contain letters and numbers"
                  required
                  autoFocus
                />
              </label>
              <label className="authmodal__field">
                <span>Email <em>(optional)</em></span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </label>
            </>
          )}

          <label className="authmodal__field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === 'register' ? 'At least 8 characters' : 'Your password'}
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              minLength={tab === 'register' ? 8 : undefined}
              required
            />
          </label>

          {error && (
            <p className="authmodal__error" role="alert">
              <AlertIcon size={16} />
              <span>{error}</span>
            </p>
          )}

          <button type="submit" className="btn btn--primary authmodal__submit" disabled={busy}>
            {busy ? 'Please wait…' : tab === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="authmodal__switch">
          {tab === 'login' ? (
            <>
              New to CourseScout?{' '}
              <button type="button" onClick={() => switchTab('register')}>
                Join free
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button type="button" onClick={() => switchTab('login')}>
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>,
    document.body,
  );
}
