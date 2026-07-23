export default function IndexingDistributionChart({ data }) {
  const total = data.reduce((sum, item) => sum + item.total_papers, 0) || 1

  return (
    <article className="chart-card">
      <div className="card-title">
        <span>Publication indexing</span>
        <h2>Distribution by category</h2>
      </div>
      <div className="donut-wrap">
        <div
          className="donut"
          style={{
            background: `conic-gradient(#6d5dfc 0 ${((data[0]?.total_papers || 0) / total) * 100}%, #20a39e 0 ${(((data[0]?.total_papers || 0) + (data[1]?.total_papers || 0)) / total) * 100}%, #f3a712 0 ${(((data[0]?.total_papers || 0) + (data[1]?.total_papers || 0) + (data[2]?.total_papers || 0)) / total) * 100}%, #d8dee9 0)`,
          }}
          title="Publication distribution by indexing"
        />
        <div className="legend-list">
          {data.map((item) => (
            <span key={item.indexing}>
              <i /> {item.indexing}: {item.total_papers}
            </span>
          ))}
        </div>
      </div>
    </article>
  )
}

