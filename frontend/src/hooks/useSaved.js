import { useEffect, useState, useCallback } from 'react';

const STORAGE_KEY = 'coursescout:saved';
const EVENT = 'coursescout:saved-changed';

function read() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function write(ids) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    /* storage unavailable (private mode) — keep in-memory only */
  }
  window.dispatchEvent(new Event(EVENT));
}

/**
 * Saved-resources store (localStorage based — works without login,
 * exactly like the reference video: bookmark on Discover → Saved tab).
 */
export default function useSaved() {
  const [ids, setIds] = useState(() => read());

  useEffect(() => {
    const sync = () => setIds(read());
    window.addEventListener(EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  const isSaved = useCallback((id) => ids.includes(id), [ids]);

  const toggle = useCallback((id) => {
    const current = read();
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    write(next);
  }, []);

  const clear = useCallback(() => write([]), []);

  return { savedIds: ids, isSaved, toggle, clear };
}
