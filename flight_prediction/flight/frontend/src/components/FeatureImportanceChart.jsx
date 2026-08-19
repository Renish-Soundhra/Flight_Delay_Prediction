export default function FeatureImportanceChart({ title, data, scoringLabel }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-block">
        <div className="chart-title">{title}</div>
        <div style={{ padding: '16px', color: 'var(--text-dim)' }}>
          Feature importance data is not available.
        </div>
      </div>
    )
  }

  const values = data.map((item) => item.importance ?? item.value ?? 0)
  const maxAbs = Math.max(...values.map((value) => Math.abs(value)), 0.0001)

  return (
    <div className="chart-block">
      <div className="chart-title">{title}</div>
      {scoringLabel && (
        <div className="chart-subtitle">{scoringLabel}</div>
      )}
      <div className="hbar-list">
        {data.map((item, index) => {
          const label = item.label || item.name
          const value = item.importance ?? item.value ?? 0
          const width = `${(Math.abs(value) / maxAbs) * 100}%`
          const isNegative = value < 0

          return (
            <div className="hbar-row" key={item.feature || item.name || index}>
              <div className="hbar-rank">{index + 1}</div>
              <div className="hbar-content">
                <div className="hbar-head">
                  <span className="hbar-label">{label}</span>
                  <span className="hbar-value">
                    {value.toFixed(4)}
                    {item.std !== undefined && (
                      <span className="hbar-std"> ± {item.std.toFixed(4)}</span>
                    )}
                  </span>
                </div>
                <div className="hbar-track">
                  <div
                    className={`hbar-fill${isNegative ? ' negative' : ''}`}
                    style={{ width }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
