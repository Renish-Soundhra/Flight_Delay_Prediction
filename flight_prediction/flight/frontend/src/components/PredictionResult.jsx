import ProbabilityCard from './ProbabilityCard.jsx'
import DelayAnalysis from './DelayAnalysis.jsx'

function FlapNumber({ value }) {
  const text = `${value}%`
  return (
    <span className="flap-row">
      {text.split('').map((char, index) => (
        <span key={index} className="flap-char" style={{ animationDelay: `${index * 0.05}s` }}>
          {char}
        </span>
      ))}
    </span>
  )
}

export default function PredictionResult({ result }) {
  if (!result) return null

  const delayed = result.prediction === 1
  const delayPercent = result.insights
    ? (result.insights.delay_probability * 100).toFixed(1)
    : Math.round(result.probability * 100)

  return (
    <div>
      <div className="result-card">
        <div className={`result-badge ${delayed ? 'delayed' : 'on-time'}`}>
          <span className="result-badge-dot" />
          {delayed ? 'Delayed' : 'On Time'}
        </div>

        <div className={`result-flap ${delayed ? 'delayed' : 'on-time'}`}>
          <FlapNumber value={delayPercent} />
        </div>
        <div className="result-label">Predicted Delay Probability</div>

        <div className="result-model">
          Model used: <strong>{result.model}</strong>
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <ProbabilityCard probability={result.probability} delayed={delayed} />
      </div>

      <DelayAnalysis insights={result.insights} status={result.status} />
    </div>
  )
}
