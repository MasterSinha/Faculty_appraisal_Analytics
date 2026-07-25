import { useState } from 'react'

const accentColors = [
  { color: '#2563eb', glow: 'rgba(37, 99, 235, 0.14)' },
  { color: '#0891b2', glow: 'rgba(8, 145, 178, 0.14)' },
  { color: '#f59e0b', glow: 'rgba(245, 158, 11, 0.14)' },
  { color: '#10b981', glow: 'rgba(16, 185, 129, 0.14)' },
  { color: '#7c3aed', glow: 'rgba(124, 58, 237, 0.14)' },
  { color: '#db2777', glow: 'rgba(219, 39, 119, 0.14)' },
]

export default function MetricCardGrid({ primaryKpis, secondaryKpis }) {
  const [showSecondary, setShowSecondary] = useState(false)

  return (
    <section className="summary-section" aria-label="Executive KPI cards">
      <div className="summary-heading">
        <div>
          <span>Executive KPI cards</span>
          <h2>Institutional research snapshot</h2>
        </div>
        {secondaryKpis?.length > 0 && (
          <button type="button" className="btn-toggle-metrics" onClick={() => setShowSecondary(true)}>
            View More Metrics
          </button>
        )}
      </div>

      <div className="kpi-grid primary-grid">
        {primaryKpis.map((kpi, index) => {
          const accent = accentColors[index % accentColors.length]
          return (
            <article
              key={kpi.label}
              className="kpi-card"
              style={{
                '--accent': accent.color,
                '--accent-glow': accent.glow,
              }}
            >
              <div className="kpi-header">
                <span className="kpi-icon">{kpi.icon || 'KPI'}</span>
                <span className="kpi-label">{kpi.label}</span>
              </div>
              <strong className="kpi-value">{kpi.value}</strong>
              {kpi.subtext && <span className="kpi-subtext">{kpi.subtext}</span>}
            </article>
          )
        })}
      </div>

      {showSecondary && (
        <aside className="metrics-drawer-backdrop" role="dialog" aria-modal="true" aria-label="More research metrics">
          <section className="metrics-drawer">
            <header>
              <div>
                <span>Expanded KPI set</span>
                <h2>More Research Metrics</h2>
              </div>
              <button type="button" onClick={() => setShowSecondary(false)}>Close</button>
            </header>
            <div className="secondary-metric-list">
              {secondaryKpis.map((kpi, index) => {
                const accent = accentColors[(index + 2) % accentColors.length]
                return (
                  <article key={kpi.label} style={{ '--accent': accent.color }}>
                    <span>{kpi.label}</span>
                    <strong>{kpi.value}</strong>
                    {kpi.subtext && <small>{kpi.subtext}</small>}
                  </article>
                )
              })}
            </div>
          </section>
        </aside>
      )}
    </section>
  )
}
