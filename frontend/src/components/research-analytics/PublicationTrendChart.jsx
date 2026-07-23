export default function PublicationTrendChart({ data }) {
  const max = Math.max(...data.map((item) => item.total_papers), 1)

  return (
    <article className="chart-card">
      <div className="card-title">
        <span>Year-wise trend</span>
        <h2>Research paper count</h2>
      </div>
      <div className="bar-chart">
        {data.map((item) => (
          <div className="vertical-bar" key={item.year} title={`${item.year}: ${item.total_papers}`}>
            <span style={{ height: `${(item.total_papers / max) * 100}%` }} />
            <small>{item.year}</small>
          </div>
        ))}
      </div>
    </article>
  )
}

