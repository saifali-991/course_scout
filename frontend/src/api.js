/**
 * Tiny fetch wrapper around the Django REST API.
 *
 * Base URL
 * --------
 * The backend address is **not** written in this file (or anywhere in src/).
 * It comes from `frontend/.env` → `VITE_API_URL`, e.g. `http://localhost:8000`.
 * Vite only exposes names that start with `VITE_`, which is why it is spelled
 * exactly like that.
 *
 * Dev  : requests go to `/api` (relative) and the Vite dev server proxies them
 *        to `VITE_API_URL` (see vite.config.js). The browser stays same-origin,
 *        so there is no CORS and no localhost-IPv6-vs-IPv4 surprise.
 * Prod : `npm run build` bakes `VITE_API_URL + '/api'` into the bundle. On
 *        Render, set `VITE_API_URL` in the service's Environment Variables
 *        (Environment → Environment Variables) before the build runs.
 *
 * Need a full custom path instead (e.g. `https://site.com/v2/api`)? Set the
 * optional `VITE_API_BASE` and it wins over the two rules above.
 */
const BACKEND = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

export const API_BASE = (
  import.meta.env.VITE_API_BASE
  || (import.meta.env.DEV ? '/api' : `${BACKEND}/api`)   // '' + '/api' = same-origin
).replace(/\/+$/, '');

/**
 * Where the **Django** admin lives — the React bundle never renders it, so the
 * SPA only needs to know which origin to hand the browser over to.
 *
 *   Render (two services) : VITE_API_URL=https://coursescout-api.onrender.com
 *                           → https://coursescout-api.onrender.com/admin/
 *   Docker / nginx, dev   : the API base is relative ('/api') and the reverse
 *                           proxy forwards /admin to Django → '/admin/' on this
 *                           very origin (nginx.conf / vite.config.js).
 *
 * Used by src/pages/AdminRedirect.jsx (the `/admin` route). An unparsable or
 * missing base falls back to same-origin, which is what a single-host setup
 * wants anyway.
 */
export const ADMIN_URL = (() => {
  const raw = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || '').trim();
  if (!raw) return '/admin/';
  try {
    return `${new URL(raw, window.location.origin).origin}/admin/`;
  } catch {
    return '/admin/';
  }
})();

export class ApiError extends Error {
  constructor(message, { status = 0, url = '' } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status; // 0 = the request never reached the API
    this.url = url;
  }
}

/** Shorten HTML/JSON error bodies so they can be shown inside the UI. */
function snippet(text = '') {
  return text
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 160);
}

/**
 * Turn an unknown thrown value into `{ title, detail }` for the ErrorBox component.
 */
export function friendlyError(err) {
  if (err instanceof ApiError && err.status === 0) {
    return {
      title: 'Backend not reachable',
      detail:
        `No response from ${err.url}. Start Django with:  ` +
        'cd backend;  ..\\myenv\\Scripts\\python.exe manage.py runserver',
    };
  }
  if (err instanceof ApiError) {
    return { title: `API error ${err.status}`, detail: `${err.url} — ${err.message}` };
  }
  return { title: 'Something went wrong', detail: String(err?.message || err) };
}

async function request(path, params = {}) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '' && value !== 'all') {
      url.searchParams.append(key, value);
    }
  });

  let res;
  try {
    res = await fetch(url.toString());
  } catch (err) {
    // Network-level failure: Django (or the dev-server proxy) is not answering.
    throw new ApiError(err?.message || 'network error', { status: 0, url: url.toString() });
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(snippet(body) || res.statusText || 'request failed', {
      status: res.status,
      url: url.toString(),
    });
  }
  return res.json();
}

export const api = {
  /** GET /api/resources/ — search / filter / paginate */
  resources: ({
    search = '',
    category = '',
    platform = '',
    level = '',
    resourceType = '',
    language = '', // 'en' | 'hi' — the catalog keeps English + Hindi only
    provider = '', // exact channel / provider, e.g. CodeWithHarry
    topCreators = false, // only hand-picked channels (see api.creators)
    free = 'all', // all | free | paid
    ordering = '-rating', // '-rating' | 'rating' | 'newest' | 'title' | 'top_creators'
    page = 1,
    pageSize = 9,
    ids = [],
  } = {}) =>
    request('/resources/', {
      search,
      category,
      platform,
      level,
      resource_type: resourceType,
      language,
      provider,
      top_creators: topCreators ? 'true' : '',
      is_free: free !== 'all' ? free : '',
      ordering,
      page,
      page_size: pageSize,
      ids: ids.join(','),
    }),

  /** GET /api/resources/<id>/ */
  resource: (id) => request(`/resources/${id}/`),

  /** GET /api/categories/ — categories with live course counts */
  categories: () => request('/categories/'),

  /** GET /api/creators/?platform=youtube — channels, top creators first */
  creators: ({ platform = '', category = '' } = {}) =>
    request('/creators/', { platform, category }),

  /** GET /api/languages/ — English/Hindi counts */
  languages: () => request('/languages/'),

  /** GET /api/stats/ — total / free / paid counts for hero badge */
  stats: () => request('/stats/'),

  /** GET /api/recommendations/?interests=python,ai */
  recommendations: (interests = []) =>
    request('/recommendations/', { interests: interests.join(','), page_size: 4 }),
};
