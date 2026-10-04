import { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, friendlyError } from '../api.js';
import CourseCard from '../components/CourseCard.jsx';
import ErrorBox from '../components/ErrorBox.jsx';
import ToggleGroup from '../components/ToggleGroup.jsx';
import TopicsDropdown from '../components/TopicsDropdown.jsx';
import CreatorsDropdown from '../components/CreatorsDropdown.jsx';
import Pagination from '../components/Pagination.jsx';
import { CardGridSkeleton, TextSkeleton } from '../components/Loader.jsx';
import { SearchIcon, SparkleIcon, ArrowRight } from '../components/Icons.jsx';

const PAGE_SIZE = 9; // multiple of 3 → full rows in the 3-up grid
const POPULAR = ['Python', 'Data Analytics', 'UI/UX', 'AI', 'Marketing'];
const AUTO_RETRIES = 2; // the Django dev server is often mid-restart — retry quietly

export default function Discover() {
  const [params, setParams] = useSearchParams();
  // The URL holds every filter (?q= &category= &type= &free= &lang= &creator= &top=),
  // so category cards, trending chips, the tabs and the browser back button all
  // behave as deep links.
  const search = params.get('q') || '';
  const topic = params.get('category') || '';
  const tab = params.get('type') === 'youtube' ? 'youtube' : 'all';
  const free = params.get('free') || 'all';
  const language = params.get('lang') || ''; // '' = all | en | hi
  // Inside the YouTube tab only: one channel (?creator=) or the starred ones (?top=1)
  const creator = params.get('creator') || '';
  const topCreators = params.get('top') === '1';

  const [input, setInput] = useState(search);
  const [page, setPage] = useState(1);

  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [topics, setTopics] = useState([]);
  const [creators, setCreators] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [creatorsLoading, setCreatorsLoading] = useState(true);
  const [ytCount, setYtCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { title, detail }
  const reqId = useRef(0);
  const attempts = useRef(0);
  const retryTimer = useRef(null);

  /** Merge filter changes into the query string (empty value clears the filter). */
  const setFilters = useCallback(
    (patch) => {
      const next = new URLSearchParams(params);
      Object.entries(patch).forEach(([key, value]) => {
        if (value) next.set(key, String(value));
        else next.delete(key);
      });
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  useEffect(() => {
    // Three small side requests: hero badge, topic filter, creator filter. Each
    // clears its own loading flag so those controls can show a spinner instead
    // of looking silently empty while the API answers.
    api.stats().then(setStats).catch(() => {});
    api.categories()
      .then((res) => setTopics(res))
      .catch(() => {})
      .finally(() => setTopicsLoading(false));
    // channels for the YouTube tab's creator dropdown (top creators first)
    api.creators({ platform: 'youtube' })
      .then(setCreators)
      .catch(() => {})
      .finally(() => setCreatorsLoading(false));
  }, []);

  // Number on the YouTube tab label — counted with the *current* search / topic /
  // free / language filters, so it never claims 97 courses for a search that has 2.
  useEffect(() => {
    let ignore = false;
    api.resources({
      platform: 'youtube', search, category: topic, free, language, pageSize: 1,
    })
      .then((res) => { if (!ignore) setYtCount(res.count); })
      .catch(() => {});
    return () => { ignore = true; };
  }, [search, topic, free, language]);

  const fetchResources = useCallback(async () => {
    const myReq = ++reqId.current;
    setLoading(true);
    setError(null);
    try {
      const res = await api.resources({
        search,
        category: topic,
        free,
        language,
        page,
        pageSize: PAGE_SIZE,
        // the YouTube tab = every resource whose link is a YouTube video/playlist
        platform: tab === 'youtube' ? 'youtube' : '',
        // creator filters only exist inside the YouTube tab
        provider: tab === 'youtube' ? creator : '',
        topCreators: tab === 'youtube' && topCreators,
        // inside the tab, hand-picked channels (CodeWithHarry, codebasics …) lead
        ordering: tab === 'youtube' ? 'top_creators' : '-rating',
      });
      if (myReq === reqId.current) {
        setData(res);
        attempts.current = 0;
      }
    } catch (err) {
      if (myReq === reqId.current) {
        setError(friendlyError(err));
        if (attempts.current < AUTO_RETRIES) {
          attempts.current += 1;
          retryTimer.current = window.setTimeout(fetchResources, 1500);
        }
      }
    } finally {
      if (myReq === reqId.current) setLoading(false);
    }
  }, [search, topic, tab, free, language, creator, topCreators, page]);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  useEffect(() => () => window.clearTimeout(retryTimer.current), []);

  // filters arrive through the URL, so any change restarts the list at page 1
  useEffect(() => {
    setPage(1);
  }, [search, topic, tab, free, language, creator, topCreators]);

  // keep the search box in sync when a link rewrites ?q= (trending chips, nav bar)
  useEffect(() => {
    setInput(search);
  }, [search]);

  const retryNow = () => {
    window.clearTimeout(retryTimer.current);
    attempts.current = 0;
    fetchResources();
  };

  const runSearch = (e) => {
    if (e) e.preventDefault();
    setFilters({ q: input.trim() });
  };

  const useChip = (label) => {
    setInput(label);
    setFilters({ q: label });
  };

  const activeCategory = topics.find((t) => t.slug === topic);
  const searching = search.trim().length > 0;
  const filtered = searching || !!topic || tab === 'youtube' || !!language
    || !!creator || topCreators;
  const count = data?.count ?? 0;

  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="hero">
        <div className="container">
          <span className="hero__badge">
            <SparkleIcon size={16} />
            {stats ? (
              `${stats.total.toLocaleString()}+ courses, one smart search`
            ) : (
              <TextSkeleton width={150} label="Loading the course count" />
            )}
          </span>
          <h1 className="hero__title">
            Every course on the internet, <span className="accent">in one place.</span>
          </h1>
          <p className="hero__subtitle">
            Compare the best free and paid courses from trusted universities, creators, and learning
            platforms. Find your next skill without the endless searching.
          </p>

          <form className="searchbar" onSubmit={runSearch}>
            <span className="searchbar__icon">
              <SearchIcon size={22} />
            </span>
            <input
              className="searchbar__input"
              placeholder='What do you want to learn? Try "Python"'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              aria-label="Search courses"
            />
            <button type="submit" className="btn btn--primary btn--lg">
              Search courses
            </button>
          </form>

          <div className="hero__popular">
            <span className="hero__popular-label">Popular:</span>
            {POPULAR.map((p) => (
              <button key={p} className="chip" onClick={() => useChip(p)}>
                {p}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Explore / Results ---------- */}
      <section className="section section--tint" id="results">
        <div className="container">
          <div className="section__head">
            <div>
              <span className="eyebrow">
                {tab === 'youtube'
                  ? creator || (topCreators ? 'YouTube · top creators' : 'YouTube')
                  : searching
                    ? 'Search results'
                    : activeCategory
                      ? activeCategory.name
                      : 'Curated for you'}
              </span>
              <h2 className="section__title">
                {tab === 'youtube' ? (
                  <>
                    <span className="accent">YouTube</span> courses
                  </>
                ) : searching ? (
                  <>
                    Results for <span className="accent">“{search}”</span>
                  </>
                ) : activeCategory ? (
                  <>
                    <span className="accent">{activeCategory.name}</span> courses
                  </>
                ) : (
                  'Explore top courses'
                )}
              </h2>
              <p className="section__subtitle">
                {filtered
                  ? `${count.toLocaleString()} resources found${
                      tab === 'youtube' && creator
                        ? ` from ${creator}`
                        : ' across trusted learning platforms'
                    }.`
                  : 'High-quality picks from trusted learning platforms.'}
              </p>
            </div>

            <div className="section__controls">
              <ToggleGroup
                value={tab}
                onChange={(v) =>
                  setFilters({
                    type: v === 'youtube' ? 'youtube' : '',
                    // the creator filter only lives inside the YouTube tab
                    ...(v === 'youtube' ? {} : { creator: '', top: '' }),
                  })
                }
                options={[
                  { value: 'all', label: 'All courses' },
                  {
                    value: 'youtube',
                    // count follows the current filters (this search's YouTube total),
                    // not the whole library — an honest number on the tab.
                    label: `YouTube${ytCount ? ` (${ytCount.toLocaleString()})` : ''}`,
                  },
                ]}
              />
              <ToggleGroup
                value={language || 'all'}
                onChange={(v) => setFilters({ lang: v === 'all' ? '' : v })}
                options={[
                  { value: 'all', label: 'Any language' },
                  { value: 'en', label: 'English' },
                  { value: 'hi', label: 'हिंदी' },
                ]}
              />
              <ToggleGroup
                value={free}
                onChange={(v) => setFilters({ free: v === 'all' ? '' : v })}
                options={[
                  { value: 'all', label: 'All' },
                  { value: 'free', label: 'Free' },
                  { value: 'paid', label: 'Paid' },
                ]}
              />
              <TopicsDropdown
                topics={topics}
                loading={topicsLoading}
                value={topic}
                onChange={(v) => setFilters({ category: v })}
              />
              {tab === 'youtube' && (
                <CreatorsDropdown
                  creators={creators}
                  loading={creatorsLoading}
                  value={creator}
                  topActive={topCreators}
                  onChange={(name) => setFilters({ creator: name, top: '' })}
                  onToggleTop={(on) => setFilters({ top: on ? '1' : '', creator: '' })}
                />
              )}
            </div>
          </div>

          {loading ? (
            <CardGridSkeleton count={PAGE_SIZE} label="Loading courses…" />
          ) : error ? (
            <ErrorBox
              title={error.title}
              detail={error.detail}
              onRetry={retryNow}
              retrying={loading}
            />
          ) : count === 0 ? (
            <div className="error-box">
              {tab === 'youtube' ? (
                <>
                  <strong>No YouTube courses yet</strong>
                  Pull them from the YouTube Data API with{' '}
                  <code>manage.py import_resources --only youtube</code> (needs{' '}
                  <code>YOUTUBE_API_KEY</code> in <code>backend/.env</code>), then reload this page.
                </>
              ) : (
                <>
                  <strong>No resources found</strong>
                  Try a different keyword, or reset the{' '}
                  <button
                    type="button"
                    className="btn btn--ghost btn--sm"
                    onClick={() => setFilters({ q: '', category: '', type: '', free: '', lang: '', creator: '', top: '' })}
                  >
                    All filters
                  </button>
                </>
              )}
            </div>
          ) : (
            <>
              <div className="grid-courses">
                {data.results.map((r) => (
                  <CourseCard key={r.id} resource={r} />
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

      {/* ---------- CTA ---------- */}
      <section className="section">
        <div className="container">
          <div className="cta">
            <span className="cta__eyebrow">Not sure where to start?</span>
            <h2 className="cta__title">Get a learning path built around your goals.</h2>
            <p className="cta__text">
              Tell us what you want to learn and get a personalized roadmap of free and paid courses
              to get there — hand-picked from trusted platforms.
            </p>
            <div className="cta__actions">
              <a className="btn btn--primary btn--lg" href="/categories">
                Build my learning path
              </a>
              <a className="btn btn--white btn--lg" href="/categories">
                Browse categories <ArrowRight size={17} />
              </a>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
