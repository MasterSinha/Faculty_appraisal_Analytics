import { useState } from 'react'

export default function AreaTrendChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  color = 'var(--indigo)',
  emptyMessage = 'No trend data available',
}) {
  const [hovered, setHovered] = useState(null)

  const data = rows.filter((r) => r[labelKey] != null)
  if (!data.length) {
    return (
      <article className="chart-card area-chart-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const vals   = data.map((r) => Number(r[valueKey] || 0))
  const maxVal = Math.max(...vals, 1)
  const minVal = Math.min(...vals, 0)
  const range  = maxVal - minVal || 1

  const W = 340
  const H = 120
  const PAD_L = 8
  const PAD_R = 8
  const PAD_T = 14
  const PAD_B = 24

  const innerW = W - PAD_L - PAD_R
  const innerH = H - PAD_T - PAD_B
  const n = data.length

  const px = (i) => PAD_L + (i / Math.max(n - 1, 1)) * innerW
  const py = (v) => PAD_T + innerH - ((v - minVal) / range) * innerH

  const points = data.map((r, i) => ({ x: px(i), y: py(Number(r[valueKey] || 0)), r, i }))

  // polyline path
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  // area fill path (close to bottom)
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${PAD_T + innerH} L ${points[0].x} ${PAD_T + innerH} Z`

  const hov = hovered !== null ? points[hovered] : null

  return (
    <article className="chart-card area-chart-card" aria-label={`${title} area chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="area-chart-wrap">
        {/* Tooltip */}
        {hov && (
          <div className="area-tooltip" style={{
            left: Math.min(hov.x + 10, W - 90),
            top: Math.max(hov.y - 36, 4),
          }}>
            <strong>{String(hov.r[labelKey])}</strong>
            <span>{formatter(Number(hov.r[valueKey] || 0))}</span>
          </div>
        )}

        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
          style={{ display: 'block', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id={`ag-${title.replace(/\s+/g,'-')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.35" />
              <stop offset="100%" stopColor={color} stopOpacity="0.03" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
            const gy = PAD_T + innerH * (1 - frac)
            return (
              <line key={frac} x1={PAD_L} y1={gy} x2={PAD_L + innerW} y2={gy}
                stroke="var(--border)" strokeWidth="1" />
            )
          })}

          {/* Area fill */}
          <path d={areaPath} fill={`url(#ag-${title.replace(/\s+/g,'-')})`} />

          {/* Line */}
          <path d={linePath} fill="none" stroke={color}
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

          {/* Hover capture rects */}
          {points.map((p, i) => (
            <rect
              key={i}
              x={p.x - innerW / (2 * Math.max(n - 1, 1))}
              y={PAD_T}
              width={innerW / Math.max(n - 1, 1)}
              height={innerH}
              fill="transparent"
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'crosshair' }}
            />
          ))}

          {/* Points */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r={hovered === i ? 5 : 3}
              fill={color} stroke="var(--surface)" strokeWidth="2"
              style={{ transition: 'r 0.12s' }} />
          ))}

          {/* Hover vertical line */}
          {hov && (
            <line x1={hov.x} y1={PAD_T} x2={hov.x} y2={PAD_T + innerH}
              stroke={color} strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
          )}

          {/* X-axis labels */}
          {points.map((p, i) => {
            // Show every Nth label to avoid crowding
            const step = Math.max(1, Math.ceil(n / 6))
            if (i % step !== 0 && i !== n - 1) return null
            return (
              <text key={i} x={p.x} y={H - 4} textAnchor="middle"
                fill="var(--text-3)" fontSize="9">
                {String(p.r[labelKey]).slice(-7)}
              </text>
            )
          })}
        </svg>
      </div>
    </article>
  )
}
