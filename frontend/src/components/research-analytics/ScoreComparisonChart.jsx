export default function ScoreComparisonChart({ scores }) {
  const values = [
    ['Self', scores?.self_score || 0],
    ['Director', scores?.director_score || 0],
    ['Dean', scores?.dean_score || 0],
    ['VC', scores?.vc_score || 0],
  ]
  const max = Math.max(...values.map(([, value]) => value), 1)

  return (
    <article className="chart-card">
      <div className="card-title">
        <span>Reviewer scores</span>
        <h2>Self vs approvals</h2>
      </div>
      <div className="horizontal-chart">
        {values.map(([label, value]) => (
          <div className="hbar-row" key={label}>
            <span>{label}</span>
            <div><i style={{ width: `${(value / max) * 100}%` }} /></div>
            <strong>{value.toFixed(0)}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

