import React, { useEffect, useState } from 'react';
import { getDashboardFlight } from '../../services/dashboardApi';

export default function FlightDetail({ flightId, onClose }) {
  const [flight, setFlight] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!flightId) return;
    setLoading(true);
    getDashboardFlight(flightId)
      .then(setFlight)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [flightId]);

  if (!flightId) return null;

  return (
    <div className="flight-detail-overlay" onClick={onClose}>
      <div className="flight-detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>×</button>
        
        {loading && <div className="loading-state">Loading Flight Details...</div>}
        {error && <div className="error-state">{error}</div>}
        
        {flight && (
          <div className="flight-detail-content">
            <h2>{flight.airline} {flight.flight_number}</h2>
            <div className="route-header">
              <span>{flight.origin}</span>
              <span className="arrow">→</span>
              <span>{flight.destination}</span>
            </div>

            <div className={`risk-badge risk-${flight.risk?.toLowerCase()}`}>
              Risk: {flight.risk}
            </div>

            <div className="detail-grid">
              <div className="detail-item">
                <label>Airline</label>
                <div>{flight.airline_name || flight.airline}</div>
              </div>
              <div className="detail-item">
                <label>Aircraft (Tail)</label>
                <div>{flight.tail_number}</div>
              </div>
              <div className="detail-item">
                <label>Scheduled Departure</label>
                <div>{flight.scheduled_departure}</div>
              </div>
              <div className="detail-item">
                <label>Scheduled Arrival</label>
                <div>{flight.scheduled_arrival}</div>
              </div>
              <div className="detail-item">
                <label>Actual Departure</label>
                <div>{flight.actual_delayed !== null ? `${flight.departure_delay} min delay` : 'Pending'}</div>
              </div>
              <div className="detail-item">
                <label>Actual Arrival</label>
                <div>{flight.actual_arrival || 'Pending'}</div>
              </div>
              <div className="detail-item">
                <label>Delay Probability</label>
                <div>{flight.probability !== null ? `${(flight.probability * 100).toFixed(1)}%` : 'N/A'}</div>
              </div>
              <div className="detail-item">
                <label>Predicted Class</label>
                <div className={flight.prediction === 1 ? 'danger' : 'success'}>
                  {flight.predicted_class_label}
                </div>
              </div>
            </div>

            {flight.previous_flight_departure_delay !== undefined && (
              <>
                <hr />
                <h3>Aircraft Rotation Context</h3>
                <div className="detail-grid rotation-context">
                  <div className="detail-item">
                    <label>Prev Flight Delay</label>
                    <div>{flight.previous_flight_departure_delay} min</div>
                  </div>
                  <div className="detail-item">
                    <label>Scheduled Turnaround</label>
                    <div>{flight.scheduled_turnaround_min} min</div>
                  </div>
                  <div className="detail-item">
                    <label>Remaining Turnaround</label>
                    <div>{flight.remaining_turnaround_min} min</div>
                  </div>
                  <div className="detail-item">
                    <label>Turnaround Stress</label>
                    <div>{flight.turnaround_stress_min} min</div>
                  </div>
                  <div className="detail-item">
                    <label>Propagation Pressure</label>
                    <div>{flight.propagation_pressure !== null ? flight.propagation_pressure.toFixed(2) : 'N/A'}</div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
