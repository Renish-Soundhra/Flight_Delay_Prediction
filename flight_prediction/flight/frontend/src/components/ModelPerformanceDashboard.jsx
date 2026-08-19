import MetricsCard from './MetricsCard.jsx'
import MetricsChart from './MetricsChart.jsx'
import ConfusionMatrixTable from './ConfusionMatrixTable.jsx'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'

const METRIC_LABELS = {
  accuracy: 'Accuracy',
  precision: 'Precision',
  recall: 'Recall',
  f1_score: 'F1 Score',
  roc_auc: 'ROC-AUC',
  pr_auc: 'PR-AUC'
}

function formatPercent(value) {
  if (value === null || value === undefined) return 'Not available'
  return `${(value * 100).toFixed(2)}%`
}

function formatNumber(value) {
  if (value === null || value === undefined) return 'Not available'
  return value.toLocaleString()
}

function toChartData(metrics) {
  return Object.entries(METRIC_LABELS)
    .filter(([key]) => metrics[key] !== undefined && metrics[key] !== null)
    .map(([key, label]) => ({
      name: label,
      value: metrics[key]
    }))
}

export default function ModelPerformanceDashboard({ metricsData }) {
  if (!metricsData) return null

  const { metrics = {}, confusion_matrix: confusionMatrix } = metricsData
  const chartData = toChartData(metrics)
  const hasConfusionMatrix = confusionMatrix &&
    ['tn', 'fp', 'fn', 'tp'].every((key) => confusionMatrix[key] !== undefined && confusionMatrix[key] !== null)

  const { curves = {}, feature_importance = [] } = metricsData
  
  // Format curve data for Recharts
  const rocData = Array.isArray(curves.roc) ? curves.roc.map(pt => ({ fpr: pt.x, tpr: pt.y })) : []
  const prData = Array.isArray(curves.pr) ? curves.pr.map(pt => ({ recall: pt.x, precision: pt.y })) : []
  
  // Handle feature importance object structure
  const importanceArray = Array.isArray(feature_importance) 
    ? feature_importance 
    : (feature_importance?.all_features || feature_importance?.top_features || [])
  const importanceData = importanceArray.slice(0, 20).map(f => ({ name: f.feature, value: f.importance }))

  return (
    <div>
      <div className="terminal">
        <div className="terminal-header">
          <span className="terminal-dot" />
          <span>Current Model</span>
        </div>

        <div className="metrics-grid" style={{ marginTop: '16px' }}>
          <MetricsCard label="Model" value={metricsData.model_name || 'Not available'} highlight />
          <MetricsCard label="Model Type" value={metricsData.model_type || 'Not available'} />
          <MetricsCard label="Task" value={metricsData.task || 'Not available'} />
          <MetricsCard label="Target" value={metricsData.target || 'Not available'} />
          <MetricsCard label="Evaluation Dataset" value={metricsData.evaluation_dataset || 'Not available'} />
          <MetricsCard label="Evaluation Samples" value={formatNumber(metricsData.evaluation_samples)} />
          <MetricsCard
            label="Threshold"
            value={
              metricsData.threshold !== null && metricsData.threshold !== undefined
                ? metricsData.threshold.toFixed(4)
                : 'Not available'
            }
          />
        </div>
      </div>

      <div style={{ marginTop: '24px' }}>
        <div className="eyebrow">Performance Metrics</div>
        <div className="metrics-grid" style={{ marginTop: '16px' }}>
          {Object.entries(METRIC_LABELS).map(([key, label]) => (
            <MetricsCard
              key={key}
              label={label}
              value={formatPercent(metrics[key])}
              highlight={key === 'roc_auc' && metrics[key] != null}
            />
          ))}
        </div>
      </div>

      <div style={{ marginTop: '24px' }}>
        <div className="eyebrow">Confusion Matrix</div>
        {hasConfusionMatrix ? (
          <div style={{ marginTop: '16px' }}>
            <ConfusionMatrixTable confusionMatrix={confusionMatrix} />
          </div>
        ) : (
          <div className="error-box" style={{ marginTop: '16px' }}>
            <span>ℹ</span>
            <span>Confusion matrix not available in saved evaluation results.</span>
          </div>
        )}
      </div>

      {chartData.length > 0 && (
        <div style={{ marginTop: '24px' }} className="charts-grid">
          <MetricsChart title="Model Performance Metrics" data={chartData} />
        </div>
      )}

      {/* Advanced Curves */}
      <div style={{ marginTop: '32px' }} className="charts-grid">
        {rocData.length > 0 && (
          <div className="card" style={{ padding: '24px' }}>
            <h3 style={{ marginTop: 0, fontFamily: 'var(--font-mono)' }}>ROC Curve</h3>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={rocData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="fpr" type="number" domain={[0, 1]} name="False Positive Rate" />
                  <YAxis dataKey="tpr" type="number" domain={[0, 1]} name="True Positive Rate" />
                  <RechartsTooltip formatter={(value) => value.toFixed(3)} />
                  <Line type="monotone" dataKey="tpr" stroke="#3b82f6" dot={false} name="ROC Curve" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {prData.length > 0 && (
          <div className="card" style={{ padding: '24px' }}>
            <h3 style={{ marginTop: 0, fontFamily: 'var(--font-mono)' }}>Precision-Recall Curve</h3>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={prData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="recall" type="number" domain={[0, 1]} name="Recall" />
                  <YAxis dataKey="precision" type="number" domain={[0, 1]} name="Precision" />
                  <RechartsTooltip formatter={(value) => value.toFixed(3)} />
                  <Line type="monotone" dataKey="precision" stroke="#f59e0b" dot={false} name="PR Curve" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Feature Importance */}
      {importanceData.length > 0 && (
        <div className="card" style={{ marginTop: '24px', padding: '24px' }}>
          <h3 style={{ marginTop: 0, fontFamily: 'var(--font-mono)' }}>Top 20 Feature Importance</h3>
          <div style={{ width: '100%', height: 400 }}>
            <ResponsiveContainer>
              <BarChart data={importanceData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} horizontal={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 10, fill: 'var(--text-dim)' }} />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#8b5cf6" name="Importance Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="terminal" style={{ marginTop: '24px' }}>
        <div className="terminal-header">
          <span className="terminal-dot" />
          <span>Metric Interpretation</span>
        </div>
        <div style={{ padding: '16px', lineHeight: 1.7, color: 'var(--muted)' }}>
          <p>
            <strong>Precision</strong> — among flights predicted as delayed, how many were actually delayed.
          </p>
          <p>
            <strong>Recall</strong> — among flights that were actually delayed, how many the model detected.
          </p>
          <p>
            <strong>F1 Score</strong> — balance between precision and recall.
          </p>
          <p>
            <strong>ROC-AUC</strong> — ranking and discrimination ability across thresholds.
          </p>
          <p>
            <strong>PR-AUC</strong> — especially useful when the positive class is relatively less frequent.
          </p>
        </div>
      </div>
    </div>
  )
}
