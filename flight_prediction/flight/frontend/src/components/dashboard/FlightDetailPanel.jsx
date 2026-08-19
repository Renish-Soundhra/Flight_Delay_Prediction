export default function FlightDetailPanel({ flight, onClose }) {
  if (!flight) return null

  const fields = [
    ['Flight', flight.flight_number],
    ['Airline', flight.airline_name || flight.airline],
    ['TAIL_NUMBER', flight.tail_number],
    ['Origin', flight.origin],
    ['Destination', flight.destination],
    ['Scheduled departure', flight.scheduled_departure],
    ['Scheduled arrival', flight.scheduled_arrival],
    ['Scheduled flight duration', flight.scheduled_flight_duration == null ? 'N/A' : `${flight.scheduled_flight_duration} min`],
    ['Actual arrival', flight.actual_arrival || 'N/A'],
    ['Departure delay', flight.departure_delay == null ? 'N/A' : `${flight.departure_delay} min`],
    ['Prediction probability', flight.probability == null ? 'N/A' : Number(flight.probability).toFixed(4)],
    ['Predicted class', flight.predicted_class_label],
    ['Risk level (viz)', flight.risk],
    ['Previous flight delay', flight.previous_flight_departure_delay == null ? 'N/A' : `${flight.previous_flight_departure_delay} min`],
    ['Previous arrival delay', flight.previous_flight_arrival_delay == null ? 'N/A' : `${flight.previous_flight_arrival_delay} min`],
    ['Time since previous', flight.time_since_previous_flight_min == null ? 'N/A' : `${flight.time_since_previous_flight_min} min`],
    ['Scheduled turnaround', flight.scheduled_turnaround_min == null ? 'N/A' : `${flight.scheduled_turnaround_min} min`],
    ['Remaining turnaround', flight.remaining_turnaround_min == null ? 'N/A' : `${flight.remaining_turnaround_min} min`],
    ['Turnaround stress', flight.turnaround_stress_min == null ? 'N/A' : `${flight.turnaround_stress_min} min`],
    ['Buffer ratio', flight.buffer_ratio == null ? 'N/A' : Number(flight.buffer_ratio).toFixed(4)],
    ['Propagation pressure', flight.propagation_pressure == null ? 'N/A' : Number(flight.propagation_pressure).toFixed(4)],
  ]

  return (
    <aside className="intel-detail">
      <div className="intel-detail-head">
        <div>
          <div className="eyebrow">Selected Flight</div>
          <h3>
            {flight.airline} {flight.flight_number}
          </h3>
        </div>
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          Close
        </button>
      </div>
      <p className="intel-detail-note">
        Probability and class are the existing HistGradientBoosting outputs using the saved
        threshold {flight.ml_threshold?.toFixed(4)}. Risk is a visualization band only. Actual
        Departure is intentionally not shown.
      </p>
      <dl className="intel-detail-grid">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value ?? 'N/A'}</dd>
          </div>
        ))}
      </dl>
    </aside>
  )
}
