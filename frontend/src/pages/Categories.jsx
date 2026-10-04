import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, friendlyError } from '../api.js';
import ErrorBox from '../components/ErrorBox.jsx';
import { CategoryGridSkeleton } from '../components/Loader.jsx';
import {
  PythonIcon,
  CodeIcon,
  DataIcon,
  BotIcon,
  PenIcon,
  MegaphoneIcon,
} from '../components/Icons.jsx';

/* Category card visuals — icon + tint, matching the reference video */
const STYLE = {
  python: { icon: PythonIcon, bg: '#e8f2ff', fg: '#1d6ff2' },
  'web-development': { icon: CodeIcon, bg: '#fff0e8', fg: '#f97316' },
  'data-analytics': { icon: DataIcon, bg: '#ffe9ee', fg: '#ef4460' },
  'ai-machine-learning': { icon: BotIcon, bg: '#e8f0ff', fg: '#3b82f6' },
  'ui-ux-design': { icon: PenIcon, bg: '#e0fbff', fg: '#0891b2' },
  'digital-marketing': { icon: MegaphoneIcon, bg: '#ece9ff', fg: '#6366f1' },
  default: { icon: CodeIcon, bg: '#eef2f8', fg: '#475569' },
};

const TRENDING = [
  'Python for Beginners',
  'SQL for Data Analysis',
  'ChatGPT Prompt Engineering',
  'Excel for Beginners',
  'AWS Certification',
  'Figma UI Design',
  'Machine Learning',
  'Digital Marketing 101',
  'React JS Course',
  'Java Interview Prep',
];

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { title, detail }
  const attempts = useRef(0);
  const retryTimer = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.categories();
      setCategories(res);
      attempts.current = 0;
    } catch (err) {
      setError(friendlyError(err));
      if (attempts.current < 2) {
        attempts.current += 1;
        retryTimer.current = window.setTimeout(load, 1500);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    return () => window.clearTimeout(retryTimer.current);
  }, [load]);

  const retryNow = () => {
    window.clearTimeout(retryTimer.current);
    attempts.current = 0;
    load();
  };

  return (
    <>
      <section className="page-head">
        <div className="container">
          <span className="eyebrow">Browse by topic</span>
          <h1 className="section__title">Browse all categories</h1>
          <p className="section__subtitle">
            Explore courses across the most in-demand skills — from beginner tutorials to
            professional certificates.
          </p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 32 }}>
        <div className="container">
          {loading ? (
            <CategoryGridSkeleton count={6} label="Loading categories…" />
          ) : error ? (
            <ErrorBox
              title={error.title}
              detail={error.detail}
              onRetry={retryNow}
              retrying={loading}
            />
          ) : (
            <div className="categories-grid">
              {categories.map((c) => {
                const style = STYLE[c.slug] || STYLE.default;
                const Icon = style.icon;
                return (
                  <Link
                    key={c.slug}
                    to={`/?category=${encodeURIComponent(c.slug)}`}
                    className="catcard"
                  >
                    <span className="catcard__icon" style={{ background: style.bg, color: style.fg }}>
                      <Icon size={24} />
                    </span>
                    <h3 className="catcard__name">{c.name}</h3>
                    <p className="catcard__desc">{c.description}</p>
                    <span className="catcard__count">{c.course_count.toLocaleString()} courses</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section className="section section--tint">
        <div className="container">
          <h2 className="section__title">Trending searches</h2>
          <p className="section__subtitle">What learners are looking for right now.</p>
          <div className="trending">
            {TRENDING.map((t) => (
              <Link key={t} to={`/?q=${encodeURIComponent(t)}`} className="chip">
                {t}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
