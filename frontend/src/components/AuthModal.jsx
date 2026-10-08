import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertIcon, PlayIcon } from './Icons.jsx';
import useAuth from '../hooks/useAuth.js';

const CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim();
const GSI_SRC = 'https://accounts.google.com/gsi/client';

/** Load Google Identity Services once (Promise so init can wait for it). */
function loadGsiScript() {
  return new Promise((resolve, reject) => {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      resolve();
      return;
    }
    const existing = document.querySelector('script[src="' + GSI_SRC + '"]');
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', () => reject(new Error('Could not load Google sign-in')));
      return;
    }
    const script = document.createElement('script');
    script.src = GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Could not load Google sign-in'));
    document.head.appendChild(script);
  });
}

/**
 * "Sign in with Google" dialog - opened from the Navbar buttons.
 *
 * Google Identity Services renders the official button inside this card; its
 * callback hands us an ID token (credential) which we POST to /api/auth/google/
 * for verification. The backend answers with our DRF token -> useAuth stores
 * it and the Navbar flips to the signed-in state. No password forms anywhere.
 */
export default function AuthModal({ onClose }) {
  const { loginWithGoogle } = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const buttonRef = useRef(null);
  // Latest handlers without re-running the render effect (onClose is an
  // inline arrow from Navbar - re-running would rebuild the Google button).
  const handlersRef = useRef({});
  handlersRef.current = { loginWithGoogle, onClose };

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

  // Load Google's script, initialize, and render the official button once.
  useEffect(() => {
    let cancelled = false;

    if (!CLIENT_ID) {
      setError(
        'Google sign-in is not configured yet - set VITE_GOOGLE_CLIENT_ID in the frontend env and rebuild.',
      );
      return () => {
        cancelled = true;
      };
    }

    loadGsiScript()
      .then(() => {
        if (cancelled || !buttonRef.current || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: async ({ credential }) => {
            setBusy(true);
            setError('');
            try {
              await handlersRef.current.loginWithGoogle(credential);
              handlersRef.current.onClose();
            } catch (err) {
              setError((err && err.message) || 'Google sign-in failed. Please try again.');
            } finally {
              setBusy(false);
            }
          },
          error_callback: (err) => {
            // User closing the account chooser is normal - stay quiet.
            if (err && err.type !== 'popup_closed') {
              setError('Google sign-in could not start (' + (err.type || 'unknown error') + ').');
            }
          },
        });
        // Empty first: React StrictMode runs effects twice in dev.
        buttonRef.current.innerHTML = '';
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: 'outline',
          size: 'large',
          width: 340,
          text: 'signin_with',
        });
      })
      .catch((err) => {
        if (!cancelled) setError((err && err.message) || 'Could not load Google sign-in.');
      });

    return () => {
      cancelled = true;
    };
  }, []);
  // Portal out of <header> - the navbar's `backdrop-filter` would otherwise
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
      <div className="authmodal" role="dialog" aria-modal="true" aria-label="Sign in">
        <button type="button" className="authmodal__close" aria-label="Close" onClick={onClose}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="6" y1="6" x2="18" y2="18" />
            <line x1="18" y1="6" x2="6" y2="18" />
          </svg>
        </button>

        <span className="authmodal__mark">
          <PlayIcon size={18} />
        </span>

        <h2 className="authmodal__title">Sign in to CourseScout</h2>
        <p className="authmodal__subtitle">
          Save courses, get recommendations and more - one click with Google.
        </p>

        <div className="authmodal__google">
          <div ref={buttonRef} className="authmodal__gbutton" />
          {busy && <p className="authmodal__busy">Signing you in...</p>}
          {error && (
            <p className="authmodal__error" role="alert">
              <AlertIcon size={16} />
              <span>{error}</span>
            </p>
          )}
        </div>

        <p className="authmodal__note">
          Your CourseScout account is created automatically from your Google
          email - no password to remember.
        </p>
      </div>
    </div>,
    document.body,
  );
}