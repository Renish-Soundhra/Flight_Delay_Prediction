export default function HighRiskTable({ data, loading, page, onPage, onSort, onSelect, search, onSearch }) {
  const items = data?.items || []

  return (
    <section className="intel-panel">
      <div className="intel-panel-head">
        <div>
          <div className="eyebrow">Watchlist</div>
          <h2>High Risk Flights</h2>
          <p>Sorted by existing HistGradientBoosting probability. Actual Departure is not displayed.</p>
        </div>
        <input
          className="intel-search"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search flight / tail"
        />
      </div>
      {loading ? (
        <div className="empty-block">Loading high-risk flights</div>
      ) : items.length === 0 ? (
        <div className="empty-block">No flights match the current filters.</div>
      ) : (
        <div className="intel-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>
                  <button type="button" onClick={() => onSort('flight_number')}>
                    Flight
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => onSort('airline')}>
                    Airline
                  </button>
                </th>
                <th>Aircraft</th>
                <th>
                  <button type="button" onClick={() => onSort('origin')}>
                    Origin
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => onSort('destination')}>
                    Dest
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => onSort('scheduled_ts')}>
                    Scheduled dep
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => onSort('scheduled_time')}>
                    Duration
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => onSort('probability')}>
                    Probability
                  </button>
                </th>
                <th>Prediction</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} onClick={() => onSelect(row.id)} className="click-row">
                  <td>
                    {row.airline} {row.flight_number}
                  </td>
                  <td>{row.airline_name || row.airline}</td>
                  <td>{row.tail_number}</td>
                  <td>{row.origin}</td>
                  <td>{row.destination}</td>
                  <td>
                    {row.scheduled_ts?.replace('T', ' ')} {row.scheduled_departure}
                  </td>
                  <td>{row.scheduled_flight_duration == null ? 'N/A' : `${row.scheduled_flight_duration} min`}</td>
                  <td>{row.probability == null ? 'N/A' : Number(row.probability).toFixed(3)}</td>
                  <td>{row.predicted_class_label}</td>
                  <td>
                    <span className={`risk-pill ${String(row.risk).toLowerCase()}`}>{row.risk}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="intel-pager">
        <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Prev
        </button>
        <span>
          Page {page} · {(data?.total || 0).toLocaleString()} flights
        </span>
        <button
          type="button"
          disabled={page * (data?.page_size || 20) >= (data?.total || 0)}
          onClick={() => onPage(page + 1)}
        >
          Next
        </button>
      </div>
    </section>
  )
}
