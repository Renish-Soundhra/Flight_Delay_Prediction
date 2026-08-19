export default function KpiGrid({ summary, loading }) {
  if (loading || !summary) {
    return (
      <div className="intel-kpi-grid">
        {Array.from({ length: 6 }).map((_, index) => (
          <div className="intel-kpi skeleton" key={index} />
        ))}
      </div>
    )
  }

  const actual = summary.actual || {}
  const model = summary.model || {}

  const cards = [
    {
      label: 'Total Flights',
      value: (actual.total_flights || 0).toLocaleString(),
      hint: 'Historical dataset rows in view',
      tone: 'actual',
    },
    {
      label: 'Delayed Flights',
      value: (actual.delayed_flights || 0).toLocaleString(),
      hint: 'Actual target = 1 (arrival delay ≥ 15 min)',
      tone: 'actual',
    },
    {
      label: 'Delay Rate',
      value: `${((actual.delay_rate || 0) * 100).toFixed(1)}%`,
      hint: 'Actual delayed / total',
      tone: 'actual',
    },
    {
      label: 'Avg Departure Delay',
      value:
        actual.avg_departure_delay == null
          ? 'N/A'
          : `${Number(actual.avg_departure_delay).toFixed(1)} min`,
      hint: 'From raw DEPARTURE_DELAY',
      tone: 'actual',
    },
    {
      label: 'High Risk Flights',
      value: (model.high_risk_flights || 0).toLocaleString(),
      hint: 'Model P(delay) ≥ 0.90 (viz only)',
      tone: 'model',
    },
    {
      label: 'Avg Prediction Probability',
      value:
        model.avg_prediction_probability == null
          ? 'N/A'
          : Number(model.avg_prediction_probability).toFixed(3),
      hint: 'Existing HistGradientBoosting P(delay)',
      tone: 'model',
    },
  ]

  return (
    <div className="intel-kpi-grid">
      {cards.map((card) => (
        <article className={`intel-kpi ${card.tone}`} key={card.label}>
          <div className="intel-kpi-kicker">{card.tone === 'model' ? 'MODEL' : 'ACTUAL'}</div>
          <div className="intel-kpi-label">{card.label}</div>
          <div className="intel-kpi-value">{card.value}</div>
          <div className="intel-kpi-hint">{card.hint}</div>
        </article>
      ))}
    </div>
  )
}
