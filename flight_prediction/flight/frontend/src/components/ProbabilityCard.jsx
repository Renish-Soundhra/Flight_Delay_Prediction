export default function ProbabilityCard({ probability, delayed }) {
  const delayPercent = (probability * 100).toFixed(1)
  const onTimePercent = ((1 - probability) * 100).toFixed(1)
  const color = delayed ? 'var(--red)' : 'var(--green)'

  return (
    <div className="prob-card">
      <div className="eyebrow">Probability Breakdown</div>
      <div style={{ display: 'grid', gap: '16px', marginTop: '12px' }}>
        <div>
          <div style={{ color: 'var(--text-dim)', fontSize: '13px' }}>Predicted Delay Probability</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '28px', fontWeight: 600, color: 'var(--red)' }}>
              {delayPercent}%
            </span>
          </div>
          <div className="prob-track" style={{ marginTop: '8px' }}>
            <div className="prob-fill" style={{ width: `${delayPercent}%`, background: 'var(--red)' }} />
          </div>
        </div>
        <div>
          <div style={{ color: 'var(--text-dim)', fontSize: '13px' }}>On-time Probability</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '28px', fontWeight: 600, color }}>
              {onTimePercent}%
            </span>
          </div>
          <div className="prob-track" style={{ marginTop: '8px' }}>
            <div className="prob-fill" style={{ width: `${onTimePercent}%`, background: color }} />
          </div>
        </div>
      </div>
    </div>
  )
}
