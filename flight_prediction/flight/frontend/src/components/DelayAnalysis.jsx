export default function DelayAnalysis({ insights, status }) {
  if (!insights) return null

  const delayed = status === 'Delayed'
  const delayPercent = (insights.delay_probability * 100).toFixed(1)
  const onTimePercent = (insights.on_time_probability * 100).toFixed(1)

  return (
    <div className="terminal" style={{ marginTop: '20px' }}>
      <div className="terminal-header">
        <span className="terminal-dot" />
        <span>Delay Analysis</span>
      </div>

      <div className="metrics-grid" style={{ marginTop: '16px' }}>
        <div className="metric-card">
          <div className="metric-card-label">Prediction</div>
          <div className={`metric-card-value${delayed ? '' : ' best'}`}>{status}</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-label">Predicted Delay Probability</div>
          <div className="metric-card-value">{delayPercent}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-label">On-time Probability</div>
          <div className="metric-card-value best">{onTimePercent}%</div>
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <div className="eyebrow">Key Input Factors for This Flight</div>
        {!insights.explanation_available && (
          <div className="error-box" style={{ marginTop: '16px' }}>
            <span>ℹ</span>
            <span>{insights.message || 'Model explanation is currently unavailable.'}</span>
          </div>
        )}
        {insights.explanation_available && insights.contributing_factors?.length > 0 && (
          <ul className="factor-list">
            {insights.contributing_factors.map((factor) => (
              <li key={factor.feature} className="factor-item">
                <strong>{factor.label}</strong>
                <span>{factor.explanation}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
