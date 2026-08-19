import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const RISK_COLOR = {
  LOW: '#35d68a',
  MEDIUM: '#f5b301',
  HIGH: '#ff5c4d',
}

export default function FlightMap({
  payload,
  loading,
  showRoutes,
  showAirports,
  onSelectFlight,
  onSelectAirport,
}) {
  if (loading) {
    return <div className="intel-map skeleton-block">Loading map</div>
  }
  if (!payload) {
    return <div className="intel-map empty-block">Map data is not available.</div>
  }

  const routes = showRoutes ? payload.routes || [] : []
  const airports = showAirports ? payload.airports || [] : []

  return (
    <div className="intel-map">
      <MapContainer center={[39.8, -98.5]} zoom={4} minZoom={3} maxZoom={10} scrollWheelZoom>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {routes.map((route) => {
          if (
            route.origin_lat == null ||
            route.origin_lon == null ||
            route.dest_lat == null ||
            route.dest_lon == null
          ) {
            return null
          }
          const color = RISK_COLOR[route.risk] || '#5b8dff'
          return (
            <Polyline
              key={`${route.origin}-${route.destination}`}
              positions={[
                [route.origin_lat, route.origin_lon],
                [route.dest_lat, route.dest_lon],
              ]}
              pathOptions={{ color, weight: Math.min(1 + Math.log10(route.flight_count + 1), 4), opacity: 0.7 }}
              eventHandlers={{
                click: () => {
                  if (route.sample_flight_id) onSelectFlight(route.sample_flight_id)
                },
              }}
            >
              <Popup>
                <strong>
                  {route.origin} → {route.destination}
                </strong>
                <div>Flights: {route.flight_count}</div>
                <div>Max P(delay): {Number(route.max_probability).toFixed(3)}</div>
                <div>Avg P(delay): {Number(route.avg_probability).toFixed(3)}</div>
                <div>Risk band: {route.risk}</div>
              </Popup>
            </Polyline>
          )
        })}
        {airports.map((airport) => {
          if (airport.lat == null || airport.lon == null) return null
          const radius = Math.max(4, Math.min(16, Math.sqrt(airport.flight_count)))
          return (
            <CircleMarker
              key={airport.airport}
              center={[airport.lat, airport.lon]}
              radius={radius}
              pathOptions={{ color: '#edf1f9', fillColor: '#5b8dff', fillOpacity: 0.85, weight: 1 }}
              eventHandlers={{ click: () => onSelectAirport?.(airport) }}
            >
              <Tooltip>
                {airport.airport} · {airport.flight_count} flights · avg P{' '}
                {Number(airport.avg_probability || 0).toFixed(3)}
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="intel-map-legend">
        <span className="risk-low">Low &lt; 0.70</span>
        <span className="risk-med">Medium</span>
        <span className="risk-high">High ≥ 0.90</span>
      </div>
    </div>
  )
}
