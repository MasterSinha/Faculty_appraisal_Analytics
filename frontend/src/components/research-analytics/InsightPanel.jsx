const SEVERITY = {
  positive: { icon: '↑', cls: 'insight-positive' },
  warning:  { icon: '⚠', cls: 'insight-warning'  },
  risk:     { icon: '↓', cls: 'insight-warning'  },
  neutral:  { icon: '◉', cls: 'insight-neutral'  },
}

export default function InsightPanel({ insights }) {
  if (!insights?.length) return null

  return (
    <section aria-label="Automated insights" style={{ marginBottom: '28px' }}>
      <div className="summary-heading">
        <div>
          <span>Automated intelligence</span>
          <h2>Executive Insights</h2>
        </div>
      </div>

      <div className="insight-panel">
        {insights.slice(0, 6).map((item, i) => {
          const cfg = SEVERITY[item.severity] || SEVERITY.neutral
          return (
            <div key={i} className={`insight-card ${cfg.cls}`}>
              <div className="insight-icon" aria-hidden="true">{cfg.icon}</div>
              <div className="insight-body">
                <div className="insight-title">{item.title}</div>
                <p className="insight-explanation">{item.explanation}</p>
                {item.supporting_metric && (
                  <span className="insight-metric">{item.supporting_metric}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
