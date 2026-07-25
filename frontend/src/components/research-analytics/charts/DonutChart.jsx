import { useState } from 'react'

const PALETTE = [
  '#6366f1','#06b6d4','#22c55e','#f59e0b',
  '#a855f7','#ec4899','#14b8a6','#ef4444',
  '#3b82f6','#84cc16',
]

export default function DonutChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No data available',
  centerLabel,
}) {
  const [hovered, setHovered] = useState(null)

  const data = rows.filter((r) => Number(r[valueKey] || 0) > 0)
  const total = data.reduce((s, r) => s + Number(r[valueKey] || 0), 0) || 1

  // Build SVG arcs
  const R = 54   // outer radius
  const r = 32   // inner radius
  const cx = 70
  const cy = 70
  const TAU = 2 * Math.PI

  const arcs = data.map((row, i) => {
    const frac = Number(row[valueKey] || 0) / total
    const prior = data.slice(0, i).reduce((sum, item) => sum + (Number(item[valueKey] || 0) / total) * TAU, 0)
    const start = -Math.PI / 2 + prior
    const end   = start + frac * TAU

    const x1 = cx + R * Math.cos(start)
    const y1 = cy + R * Math.sin(start)
    const x2 = cx + R * Math.cos(end)
    const y2 = cy + R * Math.sin(end)
    const ix1 = cx + r * Math.cos(end)
    const iy1 = cy + r * Math.sin(end)
    const ix2 = cx + r * Math.cos(start)
    const iy2 = cy + r * Math.sin(start)
    const large = frac > 0.5 ? 1 : 0

    const d = `M ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${r} ${r} 0 ${large} 0 ${ix2} ${iy2} Z`

    return { d, color: PALETTE[i % PALETTE.length], row, frac }
  })

  const active = hovered !== null ? arcs[hovered] : null

  return (
    <article className="chart-card donut-chart-card" aria-label={`${title} donut chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      {data.length === 0 ? (
        <div className="chart-empty">{emptyMessage}</div>
      ) : (
        <div className="donut-layout">
          {/* SVG */}
          <svg width="140" height="140" viewBox="0 0 140 140" aria-hidden="true" style={{ flexShrink: 0 }}>
            {arcs.map((arc, i) => (
              <path
                key={i}
                d={arc.d}
                fill={arc.color}
                opacity={hovered === null || hovered === i ? 1 : 0.35}
                style={{ cursor: 'pointer', transition: 'opacity 0.15s' }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              />
            ))}
            {/* Center text */}
            <text x={cx} y={cy - 5} textAnchor="middle" fill="var(--text-1)"
              fontSize="13" fontWeight="800">
              {active ? formatter(Number(active.row[valueKey])) : (centerLabel ?? formatter(total))}
            </text>
            <text x={cx} y={cy + 12} textAnchor="middle" fill="var(--text-3)"
              fontSize="9.5" fontWeight="500">
              {active ? active.row[labelKey] : 'total'}
            </text>
          </svg>

          {/* Legend */}
          <div className="donut-legend">
            {arcs.map((arc, i) => (
              <div
                key={i}
                className={`donut-legend-row${hovered === i ? ' active' : ''}`}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              >
                <span className="donut-dot" style={{ background: arc.color }} />
                <span className="donut-lbl">{arc.row[labelKey]}</span>
                <span className="donut-val">{formatter(Number(arc.row[valueKey]))}</span>
                <span className="donut-pct">{(arc.frac * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  )
}
