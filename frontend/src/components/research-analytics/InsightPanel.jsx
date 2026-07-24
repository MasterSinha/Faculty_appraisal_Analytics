export default function InsightPanel({ insights }) {
  if (!insights || insights.length === 0) return null

  return (
    <section className="insight-section">
      <div className="section-title">
        <span>💡 Automated Intelligence</span>
        <h2>Executive Insights & Attention Items</h2>
      </div>
      <div className="insight-grid">
        {insights.slice(0, 5).map((item, index) => {
          const badgeClass = item.severity === 'positive'
            ? 'badge-positive'
            : item.severity === 'warning'
            ? 'badge-warning'
            : item.severity === 'risk'
            ? 'badge-risk'
            : 'badge-neutral'

          return (
            <div key={index} className={`insight-card ${badgeClass}`}>
              <div className="insight-header">
                <span className="insight-title">{item.title}</span>
                <span className={`severity-badge ${badgeClass}`}>{item.severity || 'insight'}</span>
              </div>
              <p className="insight-explanation">{item.explanation}</p>
              <div className="insight-footer">
                <strong className="supporting-metric">{item.supporting_metric}</strong>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
