const severityConfig = {
  positive: {
    badgeClass: 'badge-positive',
    icon: '↑',
    label: 'Positive',
  },
  warning: {
    badgeClass: 'badge-warning',
    icon: '⚠',
    label: 'Warning',
  },
  risk: {
    badgeClass: 'badge-risk',
    icon: '↓',
    label: 'Risk',
  },
  neutral: {
    badgeClass: 'badge-neutral',
    icon: '◉',
    label: 'Insight',
  },
}

export default function InsightPanel({ insights }) {
  if (!insights || insights.length === 0) return null

  return (
    <section className="insight-section" aria-label="Automated insights">
      <div className="section-title">
        <span>💡 Automated Intelligence</span>
        <h2>Executive Insights &amp; Attention Items</h2>
      </div>

      <div className="insight-grid">
        {insights.slice(0, 5).map((item, index) => {
          const cfg = severityConfig[item.severity] || severityConfig.neutral

          return (
            <div key={index} className={`insight-card ${cfg.badgeClass}`}>
              <div className="insight-header">
                <span className="insight-title">{item.title}</span>
                <span className={`severity-badge ${cfg.badgeClass}`}>
                  {cfg.icon} {item.severity || 'insight'}
                </span>
              </div>

              <p className="insight-explanation">{item.explanation}</p>

              <div className="insight-footer">
                <strong className="supporting-metric">
                  <span style={{ opacity: 0.5, marginRight: 4 }}>▸</span>
                  {item.supporting_metric}
                </strong>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
