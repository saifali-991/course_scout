import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'coursescout:theme';
const EVENT = 'coursescout:theme-changed';

function readTheme() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {
    /* private mode - fall through to the OS preference */
  }
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}

function applyToDom(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', theme === 'dark' ? '#0b1120' : '#ffffff');
}

function store(theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* private mode - theme just will not persist */
  }
}

/**
 * Dark/light theme shared across the app.
 *
 * The initial value is applied by the inline script in index.html before
 * first paint (no white flash). This hook keeps <html data-theme> in sync,
 * persists the choice and syncs every component through a window event -
 * the same pattern as useAuth / useSaved.
 */
export default function useTheme() {
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    applyToDom(theme); // idempotent - covers first mount & external changes
    const sync = () => setTheme(readTheme());
    window.addEventListener(EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, [theme]);

  const setThemeNow = useCallback((next) => {
    if (next !== 'light' && next !== 'dark') return;
    // Short animation window so colors cross-fade instead of snapping.
    const root = document.documentElement;
    root.classList.add('theme-anim');
    window.setTimeout(() => root.classList.remove('theme-anim'), 400);
    applyToDom(next);
    store(next);
    window.dispatchEvent(new Event(EVENT));
  }, []);

  const toggleTheme = useCallback(
    () => setThemeNow(readTheme() === 'dark' ? 'light' : 'dark'),
    [setThemeNow],
  );

  return { theme, toggleTheme };
}