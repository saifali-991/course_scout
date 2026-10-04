import { useEffect, useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { api, friendlyError } from '../api.js';
import CourseCard from '../components/CourseCard.jsx';
import ErrorBox from '../components/ErrorBox.jsx';
import ToggleGroup from '../components/ToggleGroup.jsx';
import Pagination from '../components/Pagination.jsx';
import { CardGridSkeleton } from '../components/Loader.jsx';
import useSaved from '../hooks/useSaved.js';
import { BookmarkIcon, TrashIcon } from '../components/Icons.jsx';

const PAGE_SIZE = 12; // multiple of 3 → full rows in the 3-up grid

export default function Saved() {
  const { savedIds, clear } = useSaved();
  const [tab, setTab] = useState('all'); // all | course | youtube
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { title, detail }
  const attempts = useRef(0);
  const retryTimer = useRef(null);

  const fetchSaved = useCallback(async () => {
    if (savedIds.length === 0) {
      setData({ count: 0, results: [] });
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.resources({
        ids: savedIds,
        resourceType: tab === 'all' ? '' : tab,
        page,
        pageSize: PAGE_SIZE,
        ordering: '-rating',
      });
      setData(res);
      attempts.current = 0;
    } catch (err) {
      setError(friendlyError(err));
      if (attempts.current < 2) {
        attempts.current += 1;
        retryTimer.current = window.setTimeout(fetchSaved, 1500);
      }
    } finally {
      setLoading(false);
    }
  }, [savedIds, tab, page]);

  useEffect(() => {
    fetchSaved();
  }, [fetchSaved]);

  useEffect(() => () => window.clearTimeout(retryTimer.current), []);

  const retryNow = () => {
    window.clearTimeout(retryTimer.current);
    attempts.current = 0;
    fetchSaved();
  };

  useEffect(() => {
    setPage(1);
  }, [tab, savedIds.length]);

  const count = data?.count ?? 0;

  return (
    <>
      <section className="page-head">
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 20 }}>
          <div>
            <h1 className="section__title">Saved resources</h1>
            <p className="section__subtitle">Your personal collection of courses and tutorials.</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <ToggleGroup
              value={tab}
              onChange={setTab}
              options={[
                { value: 'all', label: 'All' },
                { value: 'course', label: 'Courses' },
                { value: 'youtube', label: 'Videos' },
              ]}
            />
            {savedIds.length > 0 && (
              <button className="danger-link" onClick={clear}>
                <TrashIcon size={16} /> Clear all
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 24 }}>
        <div className="container">
          {loading ? (
            // exactly as many placeholders as the page will show cards, so the
            // grid does not jump when the real data lands
            <CardGridSkeleton
              count={Math.min(savedIds.length, PAGE_SIZE)}
              label="Loading saved resources…"
            />
          ) : error ? (
            <ErrorBox
              title={error.title}
              detail={error.detail}
              onRetry={retryNow}
              retrying={loading}
            />
          ) : count === 0 ? (
            <div className="saved-empty">
              <span className="saved-empty__icon">
                <BookmarkIcon size={26} />
              </span>
              <h3>Nothing saved yet</h3>
              <p>
                Browse the Discover page and tap the bookmark icon on any course to build your
                personal collection.
              </p>
              <Link to="/" className="btn btn--primary">
                Explore courses
              </Link>
            </div>
          ) : (
            <>
              <div className="grid-courses">
                {data.results.map((r) => (
                  <CourseCard key={r.id} resource={r} openLabel="Open resource" />
                ))}
              </div>
              <Pagination
                page={page}
                count={count}
                pageSize={PAGE_SIZE}
                onPage={(p) => {
                  setPage(p);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              />
            </>
          )}
        </div>
      </section>
    </>
  );
}
