export default function GlobalFilters({ filters, options, onChange, onReset }) {
  const airlines = options?.airlines || []
  const origins = options?.origins || []
  const destinations = options?.destinations || []

  return (
    <section className="intel-filters">
      <div className="intel-filters-head">
        <div>
          <div className="eyebrow">Ops Filters</div>
          <p>Server-side filters. The browser never receives the full flight table.</p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={onReset}>
          Clear
        </button>
      </div>
      <div className="intel-filter-grid">
        <label>
          Date from
          <input
            type="datetime-local"
            value={filters.date_from}
            onChange={(event) => onChange('date_from', event.target.value)}
          />
        </label>
        <label>
          Date to
          <input
            type="datetime-local"
            value={filters.date_to}
            onChange={(event) => onChange('date_to', event.target.value)}
          />
        </label>
        <label>
          Airline
          <select value={filters.airline} onChange={(event) => onChange('airline', event.target.value)}>
            <option value="">All airlines</option>
            {airlines.map((item) => (
              <option key={item.code} value={item.code}>
                {item.code} {item.name ? `· ${item.name}` : ''}
              </option>
            ))}
          </select>
        </label>
        <label>
          Origin
          <select value={filters.origin} onChange={(event) => onChange('origin', event.target.value)}>
            <option value="">All origins</option>
            {origins.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Destination
          <select
            value={filters.destination}
            onChange={(event) => onChange('destination', event.target.value)}
          >
            <option value="">All destinations</option>
            {destinations.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Flight number
          <input
            value={filters.flight_number}
            onChange={(event) => onChange('flight_number', event.target.value)}
            placeholder="154"
          />
        </label>
        <label>
          Tail number
          <input
            value={filters.tail_number}
            onChange={(event) => onChange('tail_number', event.target.value.toUpperCase())}
            placeholder="N407AS"
          />
        </label>
        <label>
          Risk (viz)
          <select value={filters.risk} onChange={(event) => onChange('risk', event.target.value)}>
            <option value="">All</option>
            <option value="LOW">Low &lt; 0.70</option>
            <option value="MEDIUM">Medium 0.70–0.90</option>
            <option value="HIGH">High ≥ 0.90</option>
          </select>
        </label>
        <label>
          Prediction
          <select
            value={filters.prediction}
            onChange={(event) => onChange('prediction', event.target.value)}
          >
            <option value="">All</option>
            <option value="1">Delayed</option>
            <option value="0">On Time</option>
          </select>
        </label>
        <label>
          Probability min
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={filters.prob_min}
            onChange={(event) => onChange('prob_min', event.target.value)}
          />
        </label>
        <label>
          Probability max
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={filters.prob_max}
            onChange={(event) => onChange('prob_max', event.target.value)}
          />
        </label>
      </div>
    </section>
  )
}
