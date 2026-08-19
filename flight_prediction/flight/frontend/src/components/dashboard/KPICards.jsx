import React, { useEffect, useState } from 'react';
import { useDashboardContext } from './DashboardContext';
import { getDashboardSummary } from '../../services/dashboardApi';

export default function KPICards() {
  const { apiParams } = useDashboardContext();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDashboardSummary(apiParams)
      .then(setSummary)
      .catch((err) => {
        console.error("Dashboard Summary Error:", err);
        setError(err.message || "Failed to load KPIs");
      })
      .finally(() => setLoading(false));
  }, [apiParams]);

  if (error) {
    return <div className="kpi-grid loading-skeleton" style={{color: 'red', fontWeight: 'bold'}}>Error: {error}</div>;
  }

  if (loading || !summary) {
    return <div className="kpi-grid loading-skeleton">Loading KPIs...</div>;
  }

  const { actual, model } = summary;

  return (
    <div className="kpi-grid">
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">Total Flights</div>
        <div className="kpi-value">{actual.total_flights.toLocaleString()}</div>
      </div>
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">Delayed Flights</div>
        <div className="kpi-value warning">{actual.delayed_flights.toLocaleString()}</div>
      </div>
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">Delay Rate</div>
        <div className="kpi-value">{(actual.delay_rate * 100).toFixed(1)}%</div>
      </div>
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">Avg Departure Delay</div>
        <div className="kpi-value">
          {actual.avg_departure_delay ? `${actual.avg_departure_delay.toFixed(1)} min` : 'N/A'}
        </div>
      </div>
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">High Risk Flights</div>
        <div className="kpi-value danger">{model.high_risk_flights.toLocaleString()}</div>
      </div>
      <div className="card card-interactive kpi-card">
        <div className="kpi-title">Avg Prediction Prob</div>
        <div className="kpi-value">
          {model.avg_prediction_probability ? (model.avg_prediction_probability * 100).toFixed(1) : 0}%
        </div>
      </div>
    </div>
  );
}
