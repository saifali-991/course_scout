import { AlertIcon, RefreshIcon } from './Icons.jsx';

/**
 * Shared "request failed" panel with a retry button — used by Discover,
 * Categories and Saved so every page behaves the same when the Django
 * server is down or returns an error.
 */
export default function ErrorBox({
  title = 'Something went wrong',
  detail = '',
  onRetry = null,
  retrying = false,
  children = null,
}) {
  return (
    <div className="error-box">
      <span className="error-box__icon">
        <AlertIcon size={26} />
      </span>
      <strong>{title}</strong>
      {detail && <p className="error-box__detail">{detail}</p>}
      {children}
      {onRetry && (
        <button
          type="button"
          className="btn btn--primary btn--sm"
          onClick={onRetry}
          disabled={retrying}
        >
          <RefreshIcon size={16} />
          {retrying ? 'Retrying…' : 'Retry'}
        </button>
      )}
    </div>
  );
}
