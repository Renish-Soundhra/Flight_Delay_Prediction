import React, { useEffect, useState } from 'react';
import { useDashboardContext } from './DashboardContext';
import { getAircraftRotation } from '../../services/dashboardApi';

export default function AircraftRotation({ tailNumber, onClose }) {
  const { apiParams } = useDashboardContext();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tailNumber) return;
    setLoading(true);
    getAircraftRotation(tailNumber, apiParams)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [tailNumber, apiParams]);

  if (!tailNumber) return null;

  return (
    <div className="aircraft-rotation-overlay" onClick={onClose}>
      <div className="aircraft-rotation-panel" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>×</button>
        
        <h2>Aircraft Rotation: {tailNumber}</h2>
        
        {loading ? (
          <div className="loading-state">Loading Rotation Data...</div>
        ) : !data || !data.flights || data.flights.length === 0 ? (
          <div className="empty-state">No flight sequence found for this aircraft in the selected time range.</div>
        ) : (
          <div className="timeline">
            {data.flights.map((flight, index) => (
              <div key={flight.id} className="timeline-item">
                <div className={`timeline-marker risk-${flight.risk?.toLowerCase()}`}></div>
                <div className="timeline-content">
                  <h4>{flight.airline} {flight.flight_number}</h4>
                  <div className="timeline-route">
                    {flight.origin} ({flight.scheduled_departure}) → {flight.destination} ({flight.scheduled_arrival})
                  </div>
                  <div className="timeline-stats">
                    <span>Delay Prob: {(flight.probability * 100).toFixed(1)}%</span>
                    {flight.actual_delayed !== null && (
                      <span className={flight.actual_delayed === 1 ? 'danger' : 'success'}>
                        | Actual: {flight.departure_delay}m delay
                      </span>
                    )}
                  </div>
                  
                  {/* Turnaround gap if there is a next flight */}
                  {index < data.flights.length - 1 && (
                    <div className="timeline-turnaround">
                      ↓ Turnaround (Scheduled: {data.flights[index+1].scheduled_turnaround_min}m)
                      {data.flights[index+1].turnaround_stress_min > 0 && (
                        <span className="danger ml-2">Stress: {data.flights[index+1].turnaround_stress_min}m</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
