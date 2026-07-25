import { useState } from 'react'

const PALETTE = ['#6366f1', '#06b6d4', '#22c55e', '#f59e0b', '#a855f7', '#ec4899']

/**
 * RadarChart — polygon-based spider/radar chart
 * axes: [{ key, label, max? }]
 * rows: [{ label, ...axisKeys }]   — up to 3 series compared
 */
export default function RadarChart({
  title,
  subtitle,
  axes = [],
  rows = [],
  emptyMessage = 'No data available',
}) {
  const [hovered, setHovered] = useState(null)

  if (!axes.length || !rows.length) {
    return (
      <article className="chart-card radar-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const N     = axes.length
  const CX    = 110
  const CY    = 110
  const R     = 80
  const RINGS = 4

  // Angles: start at top (-π/2), go clockwise
  const angle = (i) => (i / N) * 2 * Math.PI - Math.PI / 2

  // Point on ring at fraction f (0–1) for axis i
  const pt = (i, f) => ({
    x: CX + R * f * Math.cos(angle(i)),
    y: CY + R * f * Math.sin(angle(i)),
  })

  // Normalise value for an axis
  const norm = (axisIndex, val) => {
    const ax = axes[axisIndex]
    const max = ax.max ?? Math.max(...rows.map((r) => Number(r[ax.key] || 0)), 1)
    return Math.min(Number(val || 0) / max, 1)
  }

  // Build polygon points for one series row
  const polygon = (row) =>
    axes.map((ax, i) => {
      const { x, y } = pt(i, norm(i, row[ax.key]))
      return `${x},${y}`
    }).join(' ')

  // Axis label positions (slightly outside the ring)
  const labelPt = (i) => ({
    x: CX + (R + 18) * Math.cos(angle(i)),
    y: CY + (R + 18) * Math.sin(angle(i)),
  })

  return (
    <article className="chart-card radar-card" aria-label={`${title} radar chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="radar-layout">
        <svg width="220" height="220" viewBox="0 0 220 220" aria-hidden="true" style={{ flexShrink: 0 }}>
          {/* Concentric rings */}
          {Array.from({ length: RINGS }, (_, ri) => {
            const f = (ri + 1) / RINGS
            const pts = axes.map((_, i) => {
              const p = pt(i, f)
              return `${p.x},${p.y}`
            }).join(' ')
            return (
              <polygon key={ri} points={pts}
                fill="none" stroke="var(--border)" strokeWidth="1" />
            )
          })}

          {/* Axis spokes */}
          {axes.map((_, i) => {
            const outer = pt(i, 1)
            return (
              <line key={i} x1={CX} y1={CY} x2={outer.x} y2={outer.y}
                stroke="var(--border)" strokeWidth="1" />
            )
          })}

          {/* Data polygons */}
          {rows.slice(0, 3).map((row, ri) => (
            <polygon
              key={ri}
              points={polygon(row)}
              fill={PALETTE[ri % PALETTE.length]}
              fillOpacity={hovered === null || hovered === ri ? 0.18 : 0.05}
              stroke={PALETTE[ri % PALETTE.length]}
              strokeWidth={hovered === ri ? 2.5 : 1.5}
              strokeOpacity={hovered === null || hovered === ri ? 1 : 0.3}
              style={{ cursor: 'pointer', transition: 'fill-opacity 0.18s, stroke-width 0.18s' }}
              onMouseEnter={() => setHovered(ri)}
              onMouseLeave={() => setHovered(null)}
            />
          ))}

          {/* Axis labels */}
          {axes.map((ax, i) => {
            const { x, y } = labelPt(i)
            return (
              <text key={i} x={x} y={y}
                textAnchor="middle" dominantBaseline="middle"
                fill="var(--text-2)" fontSize="9" fontWeight="600">
                {ax.label.length > 8 ? ax.label.slice(0, 7) + '…' : ax.label}
              </text>
            )
          })}
        </svg>

        {/* Legend */}
        <div className="radar-legend">
          {rows.slice(0, 3).map((row, ri) => (
            <div
              key={ri}
              className={`radar-legend-row${hovered === ri ? ' active' : ''}`}
              onMouseEnter={() => setHovered(ri)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="radar-dot" style={{ background: PALETTE[ri % PALETTE.length] }} />
              <span className="radar-lbl">{row.label}</span>
            </div>
          ))}

          {/* Axis values for hovered series */}
          {hovered !== null && rows[hovered] && (
            <div className="radar-readout">
              {axes.map((ax) => (
                <div key={ax.key} className="radar-readout-row">
                  <span>{ax.label}</span>
                  <strong>{Number(rows[hovered][ax.key] || 0).toLocaleString('en-IN')}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}
