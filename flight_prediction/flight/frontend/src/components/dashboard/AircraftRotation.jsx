export default function AircraftRotation({ tail, data, loading, onSelect, onLoad }) {
  return (
    <section className="intel-panel">
      <div className="intel-panel-head">
        <div>
          <div className="eyebrow">Rotation</div>
          <h2>Aircraft Rotation</h2>
          <p>Chronological sequence for a TAIL_NUMBER using existing turnaround and propagation features.</p>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault()
            const value = event.target.tail.value
            onLoad(value)
          }}
        >
          <input name="tail" defaultValue={tail} className="intel-search" placeholder="N407AS" />
        </form>
      </div>
      {loading && <div className="empty-block">Loading rotation</div>}
      {!loading && !data?.flights?.length && (
        <div className="empty-block">Select a tail number from a flight row or search above.</div>
      )}
      <ol className="rotation-list">
        {(data?.flights || []).map((flight, index) => (
          <li key={flight.id}>
            <button type="button" onClick={() => onSelect(flight.id)}>
              <strong>
                {flight.airline} {flight.flight_number}
              </strong>
              <span>
                {flight.origin} → {flight.destination}
              </span>
              <span>{flight.scheduled_ts?.replace('T', ' ')}</span>
              <span>P {flight.probability == null ? 'n/a' : Number(flight.probability).toFixed(3)}</span>
            </button>
            {index < (data.flights.length - 1) && (
              <div className="rotation-meta">
                prev delay {flight.previous_flight_departure_delay ?? 'n/a'} · turnaround{' '}
                {flight.scheduled_turnaround_min ?? 'n/a'} · pressure{' '}
                {flight.propagation_pressure ?? 'n/a'}
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
