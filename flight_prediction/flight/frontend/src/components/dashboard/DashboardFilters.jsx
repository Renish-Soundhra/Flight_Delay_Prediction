import React, { useEffect, useState } from 'react';
import { useDashboardContext } from './DashboardContext';
import { getDashboardFilters } from '../../services/dashboardApi';

export default function DashboardFilters() {
  const {
    filters,
    updateFilter,
    resetFilters,
    simulationMode,
    setSimulationMode,
    simulationTime,
    simulationSpeed,
    setSimulationSpeed,
    isPlaying,
    togglePlay,
    resetSimulation,
    timelineBounds,
    timelineLoading,
    dashboardError
  } = useDashboardContext();

  const [filterOptions, setFilterOptions] = useState({
    airlines: [],
    origins: [],
    destinations: [],
  });

  useEffect(() => {
    getDashboardFilters()
      .then((data) => setFilterOptions(data))
      .catch(console.error);
  }, []);

  const formatDisplayDate = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusDisplay = () => {
    if (dashboardError) return <span style={{ color: 'red' }}>Error: {dashboardError}</span>;
    if (timelineLoading) return <span>Loading...</span>;
    if (simulationTime) return <strong>{formatDisplayDate(simulationTime)}</strong>;
    return <span>Not Started</span>;
  };

  return (
    <div className="dashboard-filters-container card">
      <div className="filter-group">
        <label>Simulation Mode</label>
        <div className="toggle-switch">
          <input
            type="checkbox"
            id="simulationToggle"
            checked={simulationMode}
            onChange={(e) => setSimulationMode(e.target.checked)}
          />
          <label htmlFor="simulationToggle">2026 Simulation</label>
        </div>
      </div>

      {simulationMode && (
        <div className="filter-group simulation-controls">
          <label>Simulation Controls</label>
          <div className="control-buttons">
            <button onClick={togglePlay}>{isPlaying ? 'PAUSE' : 'START'}</button>
            <button onClick={resetSimulation}>RESET</button>
            <select
              value={simulationSpeed}
              onChange={(e) => setSimulationSpeed(Number(e.target.value))}
            >
              <option value={1}>1x Speed</option>
              <option value={5}>5x Speed</option>
              <option value={10}>10x Speed</option>
              <option value={50}>50x Speed</option>
            </select>
          </div>
          <div className="simulation-time">
            Current Time: {getStatusDisplay()}
          </div>
        </div>
      )}

      <div className="filter-group">
        <label>Airline</label>
        <select
          value={filters.airline}
          onChange={(e) => updateFilter('airline', e.target.value)}
        >
          <option value="">All Airlines</option>
          {filterOptions.airlines.map((a) => (
            <option key={a.code} value={a.code}>
              {a.name || a.code}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Origin</label>
        <select
          value={filters.origin}
          onChange={(e) => updateFilter('origin', e.target.value)}
        >
          <option value="">All Airports</option>
          {filterOptions.origins.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Destination</label>
        <select
          value={filters.destination}
          onChange={(e) => updateFilter('destination', e.target.value)}
        >
          <option value="">All Airports</option>
          {filterOptions.destinations.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Risk Level</label>
        <select
          value={filters.risk}
          onChange={(e) => updateFilter('risk', e.target.value)}
        >
          <option value="">All</option>
          <option value="HIGH">High (P ≥ 0.90)</option>
          <option value="MEDIUM">Medium (0.70 ≤ P &lt; 0.90)</option>
          <option value="LOW">Low (P &lt; 0.70)</option>
        </select>
      </div>

      <div className="filter-group filter-actions">
        <button className="reset-btn" onClick={resetFilters}>
          Clear Filters
        </button>
      </div>
    </div>
  );
}
