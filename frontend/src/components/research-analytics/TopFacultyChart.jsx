export default function TopFacultyChart({ data }) {
  const max = Math.max(...data.map((item) => item.total_research_papers), 1)

  return (
    <article className="chart-card">
      <div className="card-title">
        <span>Top faculty</span>
        <h2>By research paper count</h2>
      </div>
      <div className="horizontal-chart">
        {data.map((item) => (
          <div className="hbar-row" key={item.faculty_id}>
            <span>{item.faculty_name}</span>
            <div><i style={{ width: `${(item.total_research_papers / max) * 100}%` }} /></div>
            <strong>{item.total_research_papers}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

