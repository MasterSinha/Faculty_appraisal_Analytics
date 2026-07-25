import { useState } from 'react'

/**
 * ScatterChart — two-variable comparison
 * rows: [{ label, x, y, size? }]
 * xLabel, yLabel: axis labels
 */
export default function ScatterChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  xKey = 'x',
  yKey = 'y',
  sizeKey = null,
  xLabel = 'X',
  yLabel = 'Y',
  xFormatter = (v) => Number(v).toFixed(1),
  yFormatter = (v) => Number(v).toFixed(1),
  emptyMessage = 'No data available',
  color = '#6366f1',
}) {
  const [hovered, setHovered] = useState(null)

  const data = rows.filter((r) => r[xKey] != null && r[yKey] != null)

  if (!data.length) {
    return (
      <article className="chart-card scatter-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const W = 300; const H = 200
  const PL = 36; const PR = 12; const PT = 12; const PB = 36

  const xs = data.map((r) => Number(r[xKey] || 0))
  const ys = data.map((r) => Number(r[yKey] || 0))
  const sizes = sizeKey ? data.map((r) => Number(r[sizeKey] || 0)) : []

  const xMin = Math.min(...xs) * 0.9
  const xMax = Math.max(...xs) * 1.1 || 1
  const yMin = Math.min(...ys) * 0.9
  const yMax = Math.max(...ys) * 1.1 || 1
  const sMax = sizes.length ? Math.max(...sizes, 1) : 1

  const toSvgX = (v) => PL + ((v - xMin) / (xMax - xMin || 1)) * (W - PL - PR)
  const toSvgY = (v) => PT + (1 - (v - yMin) / (yMax - yMin || 1)) * (H - PT - PB)
  const dotR   = (v) => sizeKey ? 5 + (v / sMax) * 12 : 6

  // Midlines for quadrant
  const midX = toSvgX((xMin + xMax) / 2)
  const midY = toSvgY((yMin + yMax) / 2)

  const hov = hovered !== null ? data[hovered] : null

  return (
    <article className="chart-card scatter-card" aria-label={`${title} scatter chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div style={{ position: 'relative' }}>
        {hov && (
          <div className="scatter-tooltip">
            <strong>{hov[labelKey]}</strong>
            <span>{xLabel}: {xFormatter(hov[xKey])}</span>
            <span>{yLabel}: {yFormatter(hov[yKey])}</span>
          </div>
        )}

        <svg viewBox={`0 0 ${W} ${H}`} width="100%"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true" style={{ display: 'block' }}>

          {/* Quadrant lines */}
          <line x1={midX} y1={PT} x2={midX} y2={H - PB}
            stroke="var(--border-2)" strokeWidth="1" strokeDasharray="4 3" />
          <line x1={PL} y1={midY} x2={W - PR} y2={midY}
            stroke="var(--border-2)" strokeWidth="1" strokeDasharray="4 3" />

          {/* Axes */}
          <line x1={PL} y1={H - PB} x2={W - PR} y2={H - PB}
            stroke="var(--border)" strokeWidth="1" />
          <line x1={PL} y1={PT} x2={PL} y2={H - PB}
            stroke="var(--border)" strokeWidth="1" />

          {/* Axis labels */}
          <text x={(PL + W - PR) / 2} y={H - 2}
            textAnchor="middle" fill="var(--text-3)" fontSize="9">{xLabel}</text>
          <text x={8} y={(PT + H - PB) / 2}
            textAnchor="middle" fill="var(--text-3)" fontSize="9"
            transform={`rotate(-90, 8, ${(PT + H - PB) / 2})`}>{yLabel}</text>

          {/* Dots */}
          {data.map((row, i) => {
            const cx = toSvgX(Number(row[xKey] || 0))
            const cy = toSvgY(Number(row[yKey] || 0))
            const rv = dotR(sizes[i] || 0)
            return (
              <g key={i} style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}>
                <circle cx={cx} cy={cy} r={rv}
                  fill={color}
                  opacity={hovered === null || hovered === i ? 0.8 : 0.2}
                  stroke={hovered === i ? '#fff' : 'none'}
                  strokeWidth="1.5"
                  style={{ transition: 'opacity 0.15s' }} />
                {rv > 10 && (
                  <text x={cx} y={cy + 1} textAnchor="middle"
                    dominantBaseline="middle" fill="#fff"
                    fontSize="7" style={{ pointerEvents: 'none' }}>
                    {String(row[labelKey] || '').slice(0, 3).toUpperCase()}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>
    </article>
  )
}
