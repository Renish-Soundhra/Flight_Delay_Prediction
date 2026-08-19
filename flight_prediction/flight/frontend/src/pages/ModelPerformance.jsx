import { useEffect, useState } from 'react'
import ModelPerformanceDashboard from '../components/ModelPerformanceDashboard.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import { getModelMetrics } from '../services/api.js'

export default function ModelPerformance() {
  const [metricsData, setMetricsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function loadMetrics() {
      setLoading(true)
      setError(null)
      try {
        const data = await getModelMetrics()
        if (isMounted) setMetricsData(data)
      } catch (err) {
        if (isMounted) setError(err.message || 'Could not load model performance data.')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadMetrics()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <main className="section">
      <div className="container">
        <div className="section-head">
          <div className="eyebrow">Radar Room</div>
          <h1 className="section-title">Model Performance</h1>
          <p className="section-sub">
            Real evaluation metrics for the current flight delay model, loaded from saved
            test-set results. Only metrics present in the evaluation artifact are shown.
          </p>
        </div>

        {loading && <Loading label="Pulling model metrics" />}
        {!loading && error && <ErrorMessage message={error} />}
        {!loading && !error && !metricsData && (
          <ErrorMessage message="Model metrics unavailable" />
        )}
        {!loading && !error && metricsData && (
          <>
            {metricsData.model_load_error && (
              <div className="error-box" style={{ marginBottom: '24px' }}>
                <span>⚠</span>
                <span>
                  Model artifact not loaded: {metricsData.model_load_error}. Metrics below
                  are from saved evaluation results; predictions will not work until the
                  model file is available.
                </span>
              </div>
            )}
            <ModelPerformanceDashboard metricsData={metricsData} />
          </>
        )}
      </div>
    </main>
  )
}
