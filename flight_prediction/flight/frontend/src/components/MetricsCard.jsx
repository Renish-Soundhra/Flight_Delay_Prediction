export default function MetricsCard({ label, value, highlight }) {
  return (
    <div className="card metric-card">
      <div className="metric-card-label">{label}</div>
      <div className={`metric-card-value${highlight ? ' best' : ''}`}>{value}</div>
    </div>
  )
}