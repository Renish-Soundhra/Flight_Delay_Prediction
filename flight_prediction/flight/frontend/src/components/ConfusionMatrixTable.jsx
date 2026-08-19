function formatCount(value) {
  if (value === null || value === undefined) return '—'
  return Number(value).toLocaleString()
}

export default function ConfusionMatrixTable({ confusionMatrix }) {
  if (!confusionMatrix) return null

  const { tn, fp, fn, tp } = confusionMatrix

  return (
    <div className="confusion-matrix-wrap">
      <table className="data-table confusion-matrix-table">
        <thead>
          <tr>
            <th />
            <th>Predicted 0</th>
            <th>Predicted 1</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>Actual 0</th>
            <td className="cm-tn">{formatCount(tn)}</td>
            <td className="cm-fp">{formatCount(fp)}</td>
          </tr>
          <tr>
            <th>Actual 1</th>
            <td className="cm-fn">{formatCount(fn)}</td>
            <td className="cm-tp">{formatCount(tp)}</td>
          </tr>
        </tbody>
      </table>
      <div className="cm-legend">
        <span><strong>TN</strong> = {formatCount(tn)}</span>
        <span><strong>FP</strong> = {formatCount(fp)}</span>
        <span><strong>FN</strong> = {formatCount(fn)}</span>
        <span><strong>TP</strong> = {formatCount(tp)}</span>
      </div>
    </div>
  )
}
