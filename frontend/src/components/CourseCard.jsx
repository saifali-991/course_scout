import useSaved from '../hooks/useSaved.js';
import { BookmarkIcon, ClockIcon, StarIcon, ChevronRight } from './Icons.jsx';

/* Stable dot color per provider — mirrors the multi-color dots in the video */
const PALETTE = ['#1d6ff2', '#ef4444', '#f59e0b', '#22d3ee', '#a855f7', '#10b981', '#f97316', '#6366f1'];

/* Gradient per category — a last-resort card image if a CDN photo ever fails,
   so a tile is never left blank. Mirrors resources/thumbnails.TOPIC_COLORS. */
const TOPIC_COLORS = {
  python: ['#1d6ff2', '#7c3aed'],
  'web-development': ['#f97316', '#ef4444'],
  'data-analytics': ['#ef4460', '#f59e0b'],
  'ai-machine-learning': ['#3b82f6', '#22d3ee'],
  'ui-ux-design': ['#0891b2', '#22d3ee'],
  'digital-marketing': ['#6366f1', '#a855f7'],
};
const DEFAULT_COLORS = ['#1d6ff2', '#0b1029'];

function fallbackThumb(resource) {
  const [c1, c2] = TOPIC_COLORS[resource.category] || DEFAULT_COLORS;
  const words = String(resource.title || 'Course').split(/\s+/).filter(Boolean);
  const initials = (words.slice(0, 2).map((w) => w[0]).join('') || 'CS').toUpperCase();
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="470" viewBox="0 0 800 470">` +
    `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/>` +
    `</linearGradient></defs><rect width="800" height="470" fill="url(#g)"/>` +
    `<circle cx="660" cy="70" r="140" fill="#ffffff" opacity="0.08"/>` +
    `<text x="400" y="290" text-anchor="middle" fill="#ffffff" opacity="0.95" ` +
    `font-family="Arial, Helvetica, sans-serif" font-size="150" font-weight="bold">${initials}</text>` +
    `</svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

function providerColor(name = '') {
  let h = 0;
  for (let i = 0; i < name.length; i += 1) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

const TYPE_LABELS = {
  youtube: 'YouTube',
  course: 'Course',
  certificate: 'Certificate',
  video: 'Video',
  tutorial: 'Tutorial',
  channel: 'Channel',
  playlist: 'Playlist',
};

export default function CourseCard({ resource, openLabel = 'View details' }) {
  const { isSaved, toggle } = useSaved();
  const saved = isSaved(resource.id);
  const providerLabel = resource.platform
    ? `${resource.provider} · ${resource.platform}`
    : resource.provider;

  return (
    <article className="card">
      <div className="card__media">
        <img
          className="card__img"
          src={resource.thumbnail_url}
          alt={resource.title}
          loading="lazy"
          onError={(e) => {
            // A dead CDN link must never leave an empty tile: swap in a local
            // gradient SVG once. (Guard against an error loop on the fallback.)
            const img = e.currentTarget;
            if (img.dataset.fallback === '1') return;
            img.dataset.fallback = '1';
            img.src = fallbackThumb(resource);
          }}
        />
        <span className="card__badge">{resource.is_free ? 'Free' : 'Paid'}</span>
        <button
          className={`card__save ${saved ? 'card__save--saved' : ''}`}
          aria-label={saved ? 'Remove from saved' : 'Save resource'}
          onClick={() => toggle(resource.id)}
        >
          <BookmarkIcon size={18} filled={saved} />
        </button>
      </div>

      <div className="card__body">
        <div className="card__provider">
          <span className="card__provider-dot" style={{ background: providerColor(resource.provider) }} />
          <span>{providerLabel}</span>
          {resource.is_top_creator && (
            <span className="card__provider-top" title="Hand-picked creator">★ top creator</span>
          )}
        </div>

        <h3 className="card__title">{resource.title}</h3>

        <div className="card__meta">
          {resource.duration_text && (
            <span className="card__meta-item">
              <ClockIcon size={15} /> {resource.duration_text}
            </span>
          )}
          {resource.rating != null && (
            <span className="card__meta-item card__meta-item--rating">
              <StarIcon size={15} /> <span className="num">{Number(resource.rating).toFixed(1)}</span>
            </span>
          )}
          {resource.level && <span className="card__meta-item">{resource.level}</span>}
          {resource.language === 'hi' && <span className="card__meta-item">हिंदी</span>}
          {resource.language === 'en' && <span className="card__meta-item">English</span>}
        </div>

        <hr className="card__divider" />

        <div className="card__footer">
          <span className="card__type">{TYPE_LABELS[resource.resource_type] || resource.resource_type}</span>
          <a
            className="card__details"
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {openLabel} <ChevronRight size={16} />
          </a>
        </div>
      </div>
    </article>
  );
}
