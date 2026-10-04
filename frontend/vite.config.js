import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // The backend origin lives in frontend/.env → VITE_API_URL. Nothing is
  // hardcoded here: loadEnv() reads .env / .env.local for this config file, and
  // client code sees the very same value as import.meta.env.VITE_API_URL.
  const env = loadEnv(mode, process.cwd(), '');
  const BACKEND = (env.VITE_API_URL || '').replace(/\/+$/, '');

  // Node resolves "localhost" to ::1 (IPv6) first while Django listens on IPv4
  // 127.0.0.1, and Node 18 does not retry the other family — that shows up as a
  // bogus "Backend not reachable". So the proxy dials 127.0.0.1 while .env keeps
  // the human-readable localhost.
  const PROXY_TARGET = BACKEND.replace('//localhost', '//127.0.0.1');

  // Proxy the API (plus Django admin/static) through the dev server, so the browser
  // only ever talks to http://localhost:5173. That removes two dev-machine traps:
  //   * CORS — nothing is cross-origin any more (no Origin preflight at all);
  //   * localhost-IPv6: Django binds 127.0.0.1 while browsers may try ::1 first,
  //     which shows up as a bogus "Backend not reachable" on the page.
  const proxy = BACKEND
    ? {
        '/api': { target: PROXY_TARGET, changeOrigin: true },
        '/admin': { target: PROXY_TARGET, changeOrigin: true },
        '/static': { target: PROXY_TARGET, changeOrigin: true },
        '/media': { target: PROXY_TARGET, changeOrigin: true },
      }
    : undefined;

  if (!BACKEND) {
    console.warn(
      '\n[CourseScout] VITE_API_URL is missing, so /api cannot be proxied to Django.\n'
      + '             Fix: cd frontend  →  Copy-Item .env.example .env  →  npm run dev\n'
      + '             (the file must contain e.g. VITE_API_URL=http://localhost:8000)\n',
    );
  }

  return {
    plugins: [react()],
    server: {
      // 127.0.0.1 (not "localhost") so the socket is always bound on IPv4 — Django
      // also listens on 127.0.0.1, and browsers that resolve localhost to ::1 first
      // otherwise fall back only after a failed attempt.
      host: '127.0.0.1',
      port: 5173,
      open: false,
      proxy,
    },
  };
});
