import { useState } from 'react'

const ACCENTS = [
  { color: '#6366f1', glow: 'rgba(99,102,241,0.13)' },
  { color: '#06b6d4', glow: 'rgba(6,182,212,0.13)' },
  { color: '#22c55e', glow: 'rgba(34,197,94,0.13)' },
  { color: '#f59e0b', glow: 'rgba(245,158,11,0.13)' },
  { color: '#a855f7', glow: 'rgba(168,85,247,0.13)' },
  { color: '#ec4899', glow: 'rgba(236,72,153,0.13)' },
]

export default function MetricCardGrid({ primaryKpis, secondaryKpis }) {
  const [showDrawer, setShowDrawer] = useState(false)
  const gridSizeClass = `kpi-count-${Math.min(primaryKpis.length, 6)}`

  return (
    <section className="summary-section" aria-label="Key performance indicators">
      <div className="summary-heading">
        <div>
          <span>Executive KPI cards</span>
          <h2>Institutional Research Snapshot</h2>
        </div>
        {secondaryKpis?.length > 0 && (
          <button
            type="button"
            className="btn-toggle-metrics"
            onClick={() => setShowDrawer(true)}
          >
            {secondaryKpis.length} more metrics →
          </button>
        )}
      </div>

      {/* Primary KPI grid */}
      <div className={`kpi-grid primary-grid ${gridSizeClass}`}>
        {primaryKpis.map((kpi, i) => {
          const accent = ACCENTS[i % ACCENTS.length]
          return (
            <article
              key={kpi.label}
              className="kpi-card"
              style={{ '--accent': accent.color, '--accent-glow': accent.glow }}
            >
              <div className="kpi-header">
                <span className="kpi-icon" aria-hidden="true">
                  {kpi.icon}
                </span>
                <span className="kpi-label">{kpi.label}</span>
              </div>
              <strong className="kpi-value">{kpi.value}</strong>
              {kpi.subtext && <span className="kpi-subtext">{kpi.subtext}</span>}
            </article>
          )
        })}
      </div>

      {/* Secondary metrics drawer */}
      {showDrawer && (
        <aside
          className="metrics-drawer-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="More research metrics"
          onClick={(e) => { if (e.target === e.currentTarget) setShowDrawer(false) }}
        >
          <section className="metrics-drawer">
            <header>
              <div>
                <span>Additional indicators</span>
                <h2>More Research Metrics</h2>
              </div>
              <button type="button" onClick={() => setShowDrawer(false)}>
                Close
              </button>
            </header>

            <div className="secondary-metric-list">
              {secondaryKpis.map((kpi, i) => {
                const accent = ACCENTS[(i + 2) % ACCENTS.length]
                return (
                  <article
                    key={kpi.label}
                    style={{ '--accent': accent.color }}
                  >
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
