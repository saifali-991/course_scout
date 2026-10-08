import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';

const TOKEN_KEY = 'coursescout:auth:token';
const USER_KEY = 'coursescout:auth:user';
const EVENT = 'coursescout:auth-changed';

function readSession() {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const rawUser = localStorage.getItem(USER_KEY);
    const user = rawUser ? JSON.parse(rawUser) : null;
    return token && user ? { token, user } : null;
  } catch {
    return null;
  }
}

function writeSession(session) {
  try {
    if (session) {
      localStorage.setItem(TOKEN_KEY, session.token);
      localStorage.setItem(USER_KEY, JSON.stringify(session.user));
    } else {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  } catch {
    /* storage unavailable (private mode) - session stays in-memory only */
  }
  window.dispatchEvent(new Event(EVENT));
}

/**
 * Login state shared by the whole app (Navbar, AuthModal).
 *
 * Sign-in is Google-only: AuthModal gets an ID token (credential) from
 * Google Identity Services and hands it to loginWithGoogle(). The backend
 * verifies it and returns our DRF token, stored here in localStorage -
 * same event-driven sync pattern as useSaved.js.
 */
export default function useAuth() {
  const [session, setSession] = useState(() => readSession());
  const [checking, setChecking] = useState(!!session?.token);

  useEffect(() => {
    const sync = () => setSession(readSession());
    window.addEventListener(EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  // Validate a stored token against /api/auth/me/ once on mount - a token
  // revoked server-side (logout elsewhere, user deleted) shouldn't leave a
  // stale "Hi, ..." in the navbar. Network errors keep the optimistic session:
  // the API may just be briefly unreachable.
  const token = session?.token;
  useEffect(() => {
    if (!token) {
      setChecking(false);
      return undefined;
    }
    let cancelled = false;
    api
      .me(token)
      .then((data) => {
        if (!cancelled) writeSession({ token, user: data.user });
      })
      .catch((err) => {
        // 401/403 = token no longer valid -> sign out; anything else keep going.
        if (!cancelled && err && (err.status === 401 || err.status === 403)) {
          writeSession(null);
        }
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  /** Exchange Google's ID token for our DRF token (signs in OR signs up). */
  const loginWithGoogle = useCallback(async (credential) => {
    const data = await api.googleLogin(credential);
    writeSession(data);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    const current = readSession();
    // Clear locally first so the UI flips even if the network call fails.
    writeSession(null);
    if (current?.token) {
      try {
        await api.logout(current.token);
      } catch {
        /* token already invalid server-side - nothing left to do */
      }
    }
  }, []);

  return {
    user: session?.user ?? null,
    token: session?.token ?? null,
    isAuthenticated: !!session,
    checking,
    loginWithGoogle,
    logout,
  };
}