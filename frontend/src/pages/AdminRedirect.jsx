import { useEffect } from 'react';
import { ADMIN_URL } from '../api.js';
import ErrorBox from '../components/ErrorBox.jsx';

/**
 * `/admin` — the SPA's front door to the Django admin.
 *
 * Why this page exists: on Render the site is a *static* bundle, so anything
 * the rewrite can't find (`/*` → /index.html) lands in the SPA. React Router
 * used to match nothing at `/admin` → the app rendered an empty <main> → a
 * completely white page (that was the bug). The admin itself is Django, on the
 * API service, so the right fix is a real route that hands the browser over.
 *
 * Locally the Vite dev server proxies `/admin` to Django *before* the SPA is
 * served, so this component normally never runs in dev — it is the production
 * (static host) path.
 */
export default function AdminRedirect() {
  // True when ADMIN_URL is this very page (VITE_API_URL missing on a static
  // host). Redirecting would just reload ourselves, so we stop and explain.
  const samePlace =
    ADMIN_URL.replace(/\/+$/, '') === `${window.location.origin}${window.location.pathname}`.replace(/\/+$/, '');

  useEffect(() => {
    if (samePlace) return undefined;
    // Small delay so the "Opening…" screen is painted once instead of flashing.
    const timer = window.setTimeout(() => window.location.replace(ADMIN_URL), 120);
    return () => window.clearTimeout(timer);
  }, [ADMIN_URL, samePlace]);

  if (samePlace) {
    return (
      <div className="container" style={{ padding: '56px 0' }}>
        <ErrorBox
          title="Admin panel address is not configured"
          detail={
            'This build has no API origin, so /admin would only point back at this page. '
            + 'Set VITE_API_URL on the web service (Render → Environment → Environment Variables) '
            + 'to your API URL, e.g. https://coursescout-api.onrender.com, then redeploy — '
            + 'Vite bakes it into the bundle at build time.'
          }
        />
      </div>
    );
  }

  return (
    <div className="loading" role="status" aria-live="polite">
      <div>
        <div className="spinner" />
        Opening the admin panel…
        <div style={{ marginTop: 14, fontSize: 14 }}>
          If nothing happens,{' '}
          <a href={ADMIN_URL} rel="noreferrer follow">
            open the admin panel directly
          </a>
          .
        </div>
      </div>
    </div>
  );
}