import { ChevronLeft, ChevronRight } from './Icons.jsx';

/** Compact numbered pagination — matches the ‹ 1 › pill in the video */
export default function Pagination({ page, count, pageSize, onPage }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;

  // Show a small window of pages around the current one
  let pages = [];
  if (totalPages <= 7) {
    pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  } else {
    const start = Math.max(1, Math.min(page - 2, totalPages - 4));
    const end = Math.min(totalPages, start + 4);
    pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);
    if (start > 1) pages = ['…', ...pages];
    if (end < totalPages) pages = [...pages, '…'];
  }

  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, count);

  return (
    <div className="pagination">
      <span className="pagination__info">
        Showing <strong>{from}–{to}</strong> of <strong>{count.toLocaleString()}</strong> resources
      </span>
      <div className="pagination__pages">
        <button
          className="pagination__btn"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </button>
        {pages.map((p, i) =>
          p === '…' ? (
            <span key={`dots-${i}`} className="pagination__btn">
              …
            </span>
          ) : (
            <button
              key={p}
              className={`pagination__btn ${p === page ? 'pagination__btn--active' : ''}`}
              onClick={() => onPage(p)}
            >
              {p}
            </button>
          )
        )}
        <button
          className="pagination__btn"
          disabled={page >= totalPages}
          onClick={() => onPage(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
