import { useState } from 'react'

const PALETTE = ['#6366f1','#06b6d4','#22c55e','#f59e0b','#a855f7','#ec4899']

/**
 * FunnelChart — pipeline stage drop-off
 * rows: [{ label, value }]  sorted biggest → smallest (auto-sorted internally)
 */
export default function FunnelChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No pipeline data available',
}) {
  const [hovered, setHovered] = useState(null)

  const data = [...rows]
    .filter((r) => Number(r[valueKey] || 0) >= 0)
    .sort((a, b) => Number(b[valueKey] || 0) - Number(a[valueKey] || 0))

  if (!data.length) {
    return (
      <article className="chart-card funnel-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const max = Number(data[0][valueKey] || 1)

  return (
    <article className="chart-card funnel-card" aria-label={`${title} funnel chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="funnel-body">
        {data.map((row, i) => {
          const val   = Number(row[valueKey] || 0)
          const pct   = (val / max) * 100
          const dropPct = i > 0 ? ((Number(data[i - 1][valueKey] || 0) - val) / Number(data[i - 1][valueKey] || 1)) * 100 : 0
          const color = PALETTE[i % PALETTE.length]

          return (
            <div
              key={i}
              className={`funnel-stage${hovered === i ? ' hov' : ''}`}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
            >
              {/* Label column */}
              <div className="funnel-label">
                <span className="funnel-step">{i + 1}</span>
                <span className="funnel-name">{row[labelKey]}</span>
              </div>

              {/* Bar */}
              <div className="funnel-bar-track">
                <div
                  className="funnel-bar-fill"
                  style={{ width: `${Math.max(pct, 2)}%`, background: color }}
                />
              </div>

              {/* Value + drop */}
              <div className="funnel-meta">
                <strong style={{ color }}>{formatter(val)}</strong>
                {i > 0 && dropPct > 0 && (
                  <span className="funnel-drop">−{dropPct.toFixed(0)}%</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </article>
  )
}
