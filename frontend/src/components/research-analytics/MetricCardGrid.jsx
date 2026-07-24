import { useState } from 'react'

// Icon accent colours cycling per card position
const accentColors = [
  { color: '#3b82f6', glow: 'rgba(59,130,246,0.15)' },
  { color: '#06b6d4', glow: 'rgba(6,182,212,0.15)' },
  { color: '#f59e0b', glow: 'rgba(245,158,11,0.15)' },
  { color: '#10b981', glow: 'rgba(16,185,129,0.15)' },
  { color: '#8b5cf6', glow: 'rgba(139,92,246,0.15)' },
]

export default function MetricCardGrid({ primaryKpis, secondaryKpis }) {
  const [showSecondary, setShowSecondary] = useState(false)

  return (
    <section className="summary-section" aria-label="Key performance indicators">
      {/* Primary KPIs */}
      <div className="kpi-grid primary-grid">
        {primaryKpis.map((kpi, i) => {
          const accent = accentColors[i % accentColors.length]
          return (
            <div
              key={kpi.label}
              className="kpi-card"
              style={{
                '--accent': accent.color,
                '--accent-glow': accent.glow,
              }}
            >
              {/* top accent line */}
              <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0,
                height: '2px',
                background: `linear-gradient(90deg, transparent, ${accent.color}, transparent)`,
                borderRadius: '12px 12px 0 0',
              }} />

              <div className="kpi-header">
                <span className="kpi-icon" style={{ color: accent.color }}>{kpi.icon || '📌'}</span>
                <span className="kpi-label">{kpi.label}</span>
              </div>

              <div className="kpi-value" style={{ color: '#f0f4ff' }}>
                {kpi.value}
              </div>

              {kpi.subtext && (
                <span className="kpi-subtext">{kpi.subtext}</span>
              )}

              {/* subtle bg glow */}
              <div style={{
                position: 'absolute',
                bottom: '-20px',
                right: '-20px',
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: accent.glow,
                filter: 'blur(20px)',
                pointerEvents: 'none',
              }} />
            </div>
          )
        })}
      </div>

      {/* Secondary KPIs toggle */}
      {secondaryKpis && secondaryKpis.length > 0 && (
        <div className="secondary-kpis-container">
          <button
            type="button"
            className="btn-toggle-metrics"
            onClick={() => setShowSecondary(!showSecondary)}
          >
            {showSecondary
              ? '▲ Hide Secondary Metrics'
              : `▼ View More Metrics (${secondaryKpis.length})`}
          </button>

          {showSecondary && (
            <div className="kpi-grid secondary-grid">
              {secondaryKpis.map((kpi, i) => {
                const accent = accentColors[(i + 2) % accentColors.length]
                return (
                  <div
                    key={kpi.label}
                    className="kpi-card secondary-card"
                    style={{ '--accent': accent.color }}
                  >
                    <div className="kpi-header">
                      <span className="kpi-icon" style={{ color: accent.color }}>{kpi.icon || '📊'}</span>
                      <span className="kpi-label">{kpi.label}</span>
                    </div>
                    <div className="kpi-value">{kpi.value}</div>
                    {kpi.subtext && <span className="kpi-subtext">{kpi.subtext}</span>}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
