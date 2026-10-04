/** Pill toggle group — [All | Free | Paid] & [All | Courses | Videos] */
export default function ToggleGroup({ options, value, onChange }) {
  return (
    <div className="toggle" role="tablist">
      {options.map((opt) => (
        <button
          key={opt.value}
          role="tab"
          aria-selected={value === opt.value}
          className={`toggle__btn ${value === opt.value ? 'toggle__btn--active' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
