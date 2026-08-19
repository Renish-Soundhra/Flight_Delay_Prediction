import { useEffect, useState } from 'react'
import FeatureImportanceChart from '../components/FeatureImportanceChart.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import MetricsCard from '../components/MetricsCard.jsx'
import { getFeatureImportance } from '../services/api.js'

export default function ModelInsights() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function loadFeatureImportance() {
      setLoading(true)
      setError(null)
      try {
        const response = await getFeatureImportance()
        if (isMounted) setData(response)
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Could not load feature importance data.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadFeatureImportance()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <main className="section">
      <div className="container">
        <div className="section-head">
          <div className="eyebrow">Signal Tower</div>
          <h1 className="section-title">Feature Importance &amp; Delay Analysis</h1>
          <p className="section-sub">
            Top 10 features below are ranked by permutation importance on the held-out
            test sample. Per-flight contributing factors on the Predict page are based on
            how this flight&apos;s inputs differ from typical test-set values.
          </p>
        </div>

        {loading && <Loading label="Computing permutation importance" />}
        {!loading && error && <ErrorMessage message={error} />}
        {!loading && !error && data && (
          <>
            <div className="metrics-grid" style={{ marginBottom: '24px' }}>
              <MetricsCard label="Model" value={data.model_name || 'Not available'} highlight />
              <MetricsCard label="Importance Method" value="Permutation Importance" />
              <MetricsCard label="Scoring Metric" value={data.scoring_metric?.toUpperCase() || 'Not available'} />
              <MetricsCard
                label="Evaluation Samples"
                value={data.evaluation_samples?.toLocaleString() || 'Not available'}
              />
              <MetricsCard label="Permutation Repeats" value={data.n_repeats ?? 'Not available'} />
              <MetricsCard
                label="Total Features"
                value={data.total_features?.toLocaleString() || 'Not available'}
              />
            </div>

            <FeatureImportanceChart
              title="Top 10 Features — Permutation Importance"
              scoringLabel={data.scoring_label || 'Mean decrease in F1 score'}
              data={data.top_features || []}
            />

            <div className="terminal" style={{ marginTop: '24px' }}>
              <div className="terminal-header">
                <span className="terminal-dot" />
                <span>How to Read This</span>
              </div>
              <div style={{ padding: '16px', lineHeight: 1.7, color: 'var(--muted)' }}>
                <p>
                  Permutation importance measures how much the model&apos;s performance
                  decreases when each feature is randomly shuffled. Higher values indicate
                  stronger overall dependence on that feature. Negative values can occur when
                  shuffling a feature slightly improves the score.
                </p>
                <p>
                  These are global model insights computed once and cached. They describe
                  overall feature dependence, not the cause of one specific flight delay.
                  For flight-specific factors, use the Predict page.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
