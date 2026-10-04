/**
 * Loading placeholders — one home for every "the API is still answering" screen.
 *
 * Why skeletons instead of a blank page: a grey card with the *exact* geometry of
 * a real <CourseCard> keeps the layout from jumping when the data lands, and it
 * reads as "your courses are coming", not "the site is broken".
 *
 * Pieces
 * ------
 *   <CardGridSkeleton/>      Discover + Saved grids   (count = cards to draw)
 *   <CategoryGridSkeleton/>  Categories page          (6 tiles by default)
 *   <TextSkeleton/>          inline bars: hero badge, tab count, …
 *   <Spinner/>               small ring, e.g. inside the filter dropdowns
 *   <Loader/> (default)      block-level spinner for any wait that is not a grid
 *
 * Colours come from the design system in index.css (--blue / --blue-soft /
 * #e8eef7 = the same grey the real card images use while they decode), so the
 * placeholders look like part of the page instead of a bolted-on widget.
 */
import { useId } from 'react';

/** The grey shimmer block every placeholder is built from. */
export function Skeleton({ width, height, radius, className = '', style }) {
  return (
    <span
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  );
}

/** Ring spinner — small enough to sit inside a button, honest enough for a page. */
export function Spinner({ size = 18, className = '' }) {
  return (
    <span
      className={`spinner-ring ${className}`}
      style={{ width: size, height: size }}
      role="status"
      aria-label="Loading"
    />
  );
}

/** One placeholder card with the same skeleton as <CourseCard>. */
export function CourseCardSkeleton() {
  return (
    <article className="card card--skeleton" aria-hidden="true">
      <div className="card__media">
        <Skeleton className="skeleton--media" />
      </div>
      <div className="card__body">
        <Skeleton className="skeleton--line" width="52%" />
        <Skeleton className="skeleton--title" />
        <Skeleton className="skeleton--title" width="74%" />
        <Skeleton className="skeleton--meta" />
        <hr className="card__divider" />
        <div className="card__footer">
          <Skeleton className="skeleton--pill" />
          <Skeleton className="skeleton--line" width="96px" style={{ marginBottom: 0 }} />
        </div>
      </div>
    </article>
  );
}

/**
 * The Discover / Saved grid while /api/resources/ is in flight.
 * `count` should match the page size so the page keeps its exact height.
 */
export function CardGridSkeleton({ count = 9, label = 'Loading courses…' }) {
  return (
    <div className="grid-courses" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {Array.from({ length: count }, (_, i) => (
        <CourseCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** One placeholder category tile (mirrors .catcard). */
export function CategoryCardSkeleton() {
  return (
    <div className="catcard catcard--skeleton" aria-hidden="true">
      <Skeleton className="skeleton--icon" />
      <Skeleton className="skeleton--line" width="58%" />
      <Skeleton className="skeleton--line" />
      <Skeleton className="skeleton--line" width="82%" />
      <Skeleton className="skeleton--pill" />
    </div>
  );
}

/** The Categories page while /api/categories/ is in flight. */
export function CategoryGridSkeleton({ count = 6, label = 'Loading categories…' }) {
  return (
    <div className="categories-grid" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {Array.from({ length: count }, (_, i) => (
        <CategoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** Inline bar for text that lives inside a badge / heading / tab label. */
export function TextSkeleton({ width = 64, height = 13, label = 'Loading…' }) {
  const id = useId();
  return (
    <>
      <Skeleton className="skeleton--inline" width={width} height={height} />
      <span className="sr-only" id={id}>
        {label}
      </span>
    </>
  );
}

/** Block-level spinner + caption — for any wait that is not a card grid. */
export default function Loader({ label = 'Loading…' }) {
  return (
    <div className="loading" role="status" aria-live="polite" aria-busy="true">
      <div>
        <div className="spinner" />
        {label}
      </div>
    </div>
  );
}
