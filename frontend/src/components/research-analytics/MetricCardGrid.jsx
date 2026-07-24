import { useState } from 'react'

export default function MetricCardGrid({ primaryKpis, secondaryKpis }) {
  const [showSecondary, setShowSecondary] = useState(false)

  return (
    <section className="summary-section">
      <div className="kpi-grid primary-grid">
        {primaryKpis.map((kpi) => (
          <div key={kpi.label} className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-icon">{kpi.icon || '📌'}</span>
              <span className="kpi-label">{kpi.label}</span>
            </div>
            <div className="kpi-value">{kpi.value}</div>
            {kpi.subtext && <span className="kpi-subtext">{kpi.subtext}</span>}
          </div>
        ))}
      </div>

      {secondaryKpis && secondaryKpis.length > 0 && (
        <div className="secondary-kpis-container">
          <button
            type="button"
            className="btn-toggle-metrics"
            onClick={() => setShowSecondary(!showSecondary)}
          >
            {showSecondary ? '▲ Hide Secondary Metrics' : '▼ View More Metrics (' + secondaryKpis.length + ')'}
          </button>

          {showSecondary && (
            <div className="kpi-grid secondary-grid">
              {secondaryKpis.map((kpi) => (
                <div key={kpi.label} className="kpi-card secondary-card">
                  <div className="kpi-header">
                    <span className="kpi-icon">{kpi.icon || '📊'}</span>
                    <span className="kpi-label">{kpi.label}</span>
                  </div>
                  <div className="kpi-value">{kpi.value}</div>
                  {kpi.subtext && <span className="kpi-subtext">{kpi.subtext}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
