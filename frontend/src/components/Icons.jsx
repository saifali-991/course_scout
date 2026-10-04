/* Central icon set — small inline SVGs so we ship zero icon dependencies. */

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export const SearchIcon = ({ size = 20, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.5" y2="16.5" />
  </svg>
);

export const ClockIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <circle cx="12" cy="12" r="9" />
    <polyline points="12 7 12 12 15.5 13.5" />
  </svg>
);

export const StarIcon = ({ size = 16, filled = true, ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={2}
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12 2.5l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.3l-5.8 3.1 1.1-6.5L2.6 9.3l6.5-.9L12 2.5z" />
  </svg>
);

export const BookmarkIcon = ({ size = 18, filled = false, ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth={2}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M6 3.5h12a1 1 0 0 1 1 1V21l-7-4.2L5 21V4.5a1 1 0 0 1 1-1z" />
  </svg>
);

export const ChevronDown = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

export const ChevronRight = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <polyline points="9 6 15 12 9 18" />
  </svg>
);

export const ChevronLeft = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <polyline points="15 6 9 12 15 18" />
  </svg>
);

export const ArrowRight = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <line x1="4" y1="12" x2="20" y2="12" />
    <polyline points="14 6 20 12 14 18" />
  </svg>
);

export const FilterIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <line x1="4" y1="7" x2="20" y2="7" />
    <line x1="7" y1="12" x2="17" y2="12" />
    <line x1="10" y1="17" x2="14" y2="17" />
  </svg>
);

export const PlayIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" stroke="none" {...props}>
    <path d="M8 5.5v13l11-6.5-11-6.5z" />
  </svg>
);

export const SparkleIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" stroke="none" {...props}>
    <path d="M12 2l2.2 6.6L21 11l-6.8 2.4L12 20l-2.2-6.6L3 11l6.8-2.4L12 2z" />
    <path d="M19.5 2.5l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9.9-2.6z" opacity=".7" />
  </svg>
);

export const TrashIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <polyline points="4 7 20 7" />
    <path d="M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" />
    <path d="M9 7V4.5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1V7" />
  </svg>
);

export const GlobeIcon = ({ size = 18, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3c2.5 2.6 3.8 5.7 3.8 9S14.5 18.4 12 21c-2.5-2.6-3.8-5.7-3.8-9S9.5 5.6 12 3z" />
  </svg>
);

/* ---- Feedback icons (ErrorBox) ---- */

export const AlertIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <circle cx="12" cy="12" r="9" />
    <line x1="12" y1="7.5" x2="12" y2="13" />
    <line x1="12" y1="16.5" x2="12" y2="16.51" />
  </svg>
);

export const RefreshIcon = ({ size = 16, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M20.5 12a8.5 8.5 0 1 1-2.5-6.1" />
    <polyline points="20.5 3.5 20.5 9 15 9" />
  </svg>
);

/* ---- Category icons (Categories page) ---- */

export const CodeIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <polyline points="8 6 3 12 8 18" />
    <polyline points="16 6 21 12 16 18" />
    <line x1="13.5" y1="5" x2="10.5" y2="19" />
  </svg>
);

export const DataIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <line x1="4" y1="20" x2="20" y2="20" />
    <rect x="5.5" y="11" width="3.5" height="6" rx="0.8" />
    <rect x="10.8" y="7" width="3.5" height="10" rx="0.8" />
    <rect x="16" y="4" width="3.5" height="13" rx="0.8" />
  </svg>
);

export const BotIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <rect x="4" y="8" width="16" height="11" rx="3" />
    <circle cx="9" cy="13" r="1.2" fill="currentColor" stroke="none" />
    <circle cx="15" cy="13" r="1.2" fill="currentColor" stroke="none" />
    <path d="M12 8V4.5M9.5 4.5h5" />
  </svg>
);

export const PenIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M12 19l7-7a2.4 2.4 0 0 0-3.4-3.4l-7 7L7 20l5-1z" />
    <path d="M14.5 9.5l3.4 3.4" />
  </svg>
);

export const MegaphoneIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...props}>
    <path d="M3 10v4a1 1 0 0 0 1 1h3l7 4V5L7 9H4a1 1 0 0 0-1 1z" />
    <path d="M17.5 9.5a4 4 0 0 1 0 5" />
  </svg>
);

export const PythonIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" stroke="none" {...props}>
    <path d="M11.9 2c-2.6 0-4.4 1.1-4.4 3v2.3h4.6v.8H5.6C3.7 8.1 2 9.4 2 12c0 2.6 1.5 4 3.4 4h1.9v-2.5c0-1.9 1.7-3.4 3.7-3.4h4.5c1.7 0 3-1.3 3-3V5c0-1.9-1.8-3-4.5-3h-2.1zm-1.6 1.8a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8z" />
    <path d="M12.1 22c2.6 0 4.4-1.1 4.4-3v-2.3h-4.6v-.8h6.5c1.9 0 3.6-1.3 3.6-3.9 0-2.6-1.5-4-3.4-4h-1.9v2.5c0 1.9-1.7 3.4-3.7 3.4H8.5c-1.7 0-3 1.3-3 3V19c0 1.9 1.8 3 4.5 3h2.1zm1.6-1.8a.9.9 0 1 1 0-1.8.9.9 0 0 1 0 1.8z" opacity=".55" />
  </svg>
);
