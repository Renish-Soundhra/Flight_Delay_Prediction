export default function MetricsChart({ title, data }) {
  const maxValue = Math.max(...data.map((item) => item.value), 1)

  return (
    <div className="chart-block">
      <div className="chart-title">{title}</div>
      <div className="chart-bars">
        {data.map((item) => (
          <div className="chart-bar-col" key={item.name}>
            <span className="chart-bar-value">{Math.round(item.value * 100)}%</span>
            <div
              className="chart-bar"
              style={{ height: `${(item.value / maxValue) * 100}%` }}
            />
            <span className="chart-bar-name">{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}