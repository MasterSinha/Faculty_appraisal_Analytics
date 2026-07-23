export default function ProjectFundingChart({ data }) {
  const agencyRows = data.filter((item) => item.group === 'funding_agency').slice(0, 8)
  const max = Math.max(...agencyRows.map((item) => item.amount), 1)

  return (
    <article className="chart-card">
      <div className="card-title">
        <span>Project funding</span>
        <h2>Agency-wise sanctioned amount</h2>
      </div>
      <div className="horizontal-chart">
        {agencyRows.map((item) => (
          <div className="hbar-row" key={item.name}>
            <span>{item.name}</span>
            <div><i style={{ width: `${(item.amount / max) * 100}%` }} /></div>
            <strong>{new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(item.amount)}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

