import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useDashboardContext } from './DashboardContext';
import { getDashboardMap } from '../../services/dashboardApi';

// A simple utility to map risk to color
const getRiskColor = (risk) => {
  switch (risk) {
    case 'HIGH': return '#ef4444'; // red-500
    case 'MEDIUM': return '#f59e0b'; // amber-500
    case 'LOW': return '#10b981'; // emerald-500
    default: return '#6b7280'; // gray-500
  }
};

export default function FlightMap({ onFlightClick }) {
  const { apiParams } = useDashboardContext();
  const [mapData, setMapData] = useState({ routes: [], airports: [] });
  const [loading, setLoading] = useState(true);

  // Map toggles
  const [showRoutes, setShowRoutes] = useState(true);
  const [showAirports, setShowAirports] = useState(true);

  useEffect(() => {
    setLoading(true);
    getDashboardMap(apiParams)
      .then(setMapData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [apiParams]);

  return (
    <div className="flight-map-container card">
      <div className="map-controls">
        <h3>Live Interactive Map</h3>
        <div className="map-toggles">
          <label>
            <input type="checkbox" checked={showRoutes} onChange={(e) => setShowRoutes(e.target.checked)} />
            Show Routes
          </label>
          <label>
            <input type="checkbox" checked={showAirports} onChange={(e) => setShowAirports(e.target.checked)} />
            Show Airports
          </label>
        </div>
      </div>
      
      <div className="map-wrapper" style={{ height: '400px', width: '100%' }}>
        {loading && <div className="map-loading">Loading Map Data...</div>}
        <MapContainer center={[39.8283, -98.5795]} zoom={4} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          
          {/* Render Routes */}
          {showRoutes && mapData.routes?.map((route, i) => (
            <Polyline
              key={`route-${i}`}
              positions={[
                [route.origin_lat, route.origin_lon],
                [route.dest_lat, route.dest_lon]
              ]}
              pathOptions={{
                color: getRiskColor(route.risk),
                weight: route.risk === 'HIGH' ? 3 : 1,
                opacity: 0.6
              }}
              eventHandlers={{
                click: () => onFlightClick && onFlightClick(route.sample_flight_id)
              }}
            >
              <Tooltip>
                {route.origin} → {route.destination}<br/>
                Flights: {route.flight_count}<br/>
                Max Risk: {route.risk} ({(route.max_probability * 100).toFixed(1)}%)
              </Tooltip>
            </Polyline>
          ))}

          {/* Render Airports */}
          {showAirports && mapData.airports?.map((airport, i) => {
            // Scale radius by flight volume, min 3, max 15
            const radius = Math.max(3, Math.min(15, Math.sqrt(airport.flight_count) * 1.5));
            // Risk level for airport based on avg prob
            const avgProb = airport.avg_probability;
            const risk = avgProb >= 0.90 ? 'HIGH' : avgProb >= 0.70 ? 'MEDIUM' : 'LOW';

            return (
              <CircleMarker
                key={`apt-${i}`}
                center={[airport.lat, airport.lon]}
                radius={radius}
                pathOptions={{
                  color: getRiskColor(risk),
                  fillColor: getRiskColor(risk),
                  fillOpacity: 0.7,
                  weight: 1
                }}
              >
                <Tooltip>
                  <strong>{airport.airport}</strong><br/>
                  Flights: {airport.flight_count}<br/>
                  Avg Prob: {(avgProb * 100).toFixed(1)}%
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
