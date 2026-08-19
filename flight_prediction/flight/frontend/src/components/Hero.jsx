import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getModelMetrics } from '../services/api.js'

function FlapWord({ text, delayOffset = 0 }) {
  return (
    <span className="flap-row">
      {text.split('').map((char, index) => (
        <span
          key={index}
          className={`flap-char${char === ' ' ? ' is-space' : ''}`}
          style={{ animationDelay: `${(delayOffset + index) * 0.035}s` }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </span>
  )
}

function formatPercent(value) {
  if (value === null || value === undefined) return 'N/A'
  return `${(value * 100).toFixed(2)}%`
}

export default function Hero() {
  const lineOne = 'WILL YOUR'
  const lineTwo = 'FLIGHT BE'
  const lineThree = 'ON TIME?'

  const [metrics, setMetrics] = useState(null)
  const [metricsError, setMetricsError] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function loadMetrics() {
      try {
        const data = await getModelMetrics()
        if (isMounted) setMetrics(data)
      } catch (err) {
        if (isMounted) setMetricsError(err.message || 'Model metrics unavailable')
      }
    }

    loadMetrics()

    return () => {
      isMounted = false
    }
  }, [])

  const testMetrics = metrics?.metrics || {}

  return (
    <section className="hero">
      <div className="container">
        <div className="eyebrow">GATE 12 · NOW BOARDING · MACHINE LEARNING</div>
        <h1 className="hero-title flap-board" style={{ flexDirection: 'column', display: 'flex' }}>
          <FlapWord text={lineOne} delayOffset={0} />
          <FlapWord text={lineTwo} delayOffset={lineOne.length} />
          <FlapWord text={lineThree} delayOffset={lineOne.length + lineTwo.length} />
        </h1>
        <p className="hero-sub">
          Enter a flight's schedule and route, and our model reads the pattern before the
          departure board does. Trained on real airline data, tuned for the moments that
          matter most: your gate, your day, your delay.
        </p>
        <div className="hero-actions">
          <Link to="/predict" className="btn btn-primary">
            Predict Flight →
          </Link>
          <Link to="/performance" className="btn btn-ghost">
            View Model Performance
          </Link>
        </div>

        <div className="board-panel">
          <div className="board-header">
            <span>Model Performance</span>
            <span>Live from /api/model/metrics</span>
          </div>
          {metricsError && (
            <div className="error-box" style={{ margin: '16px' }}>
              <span>⚠</span>
              <span>{metricsError}</span>
            </div>
          )}
          {!metricsError && !metrics && (
            <div style={{ padding: '24px', color: 'var(--muted)' }}>Loading model metrics…</div>
          )}
          {!metricsError && metrics && (
            <div className="board-grid">
              <div className="board-cell">
                <div className="board-cell-label">Accuracy</div>
                <div className="board-cell-value">{formatPercent(testMetrics.accuracy)}</div>
              </div>
              <div className="board-cell">
                <div className="board-cell-label">Precision</div>
                <div className="board-cell-value">{formatPercent(testMetrics.precision)}</div>
              </div>
              <div className="board-cell">
                <div className="board-cell-label">Recall</div>
                <div className="board-cell-value">{formatPercent(testMetrics.recall)}</div>
              </div>
              <div className="board-cell">
                <div className="board-cell-label">ROC-AUC</div>
                <div className="board-cell-value green">{formatPercent(testMetrics.roc_auc)}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
