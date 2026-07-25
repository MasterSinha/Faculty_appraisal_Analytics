import { useState } from 'react'

const PALETTE = [
  '#6366f1','#06b6d4','#22c55e','#f59e0b',
  '#a855f7','#ec4899','#14b8a6','#3b82f6',
]

export default function BubbleCloudChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No data available',
  maxItems = 20,
}) {
  const [hovered, setHovered] = useState(null)

  const data = [...rows]
    .sort((a, b) => Number(b[valueKey] || 0) - Number(a[valueKey] || 0))
    .slice(0, maxItems)

  if (!data.length) {
    return (
      <article className="chart-card bubble-chart-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const max = Number(data[0][valueKey] || 1)
  // Min bubble radius 18, max 52
  const radius = (v) => 18 + (Number(v || 0) / max) * 34

  // Simple packed layout: place bubbles in rows
  const W = 340
  const H = 180
  let placed = []
  let cx = 0
  let cy = 0
  let rowH = 0

  data.forEach((row, i) => {
    const rv = radius(Number(row[valueKey] || 0))
    if (cx + rv * 2 > W && cx > 0) {
      cy += rowH + 6
      cx = 0
      rowH = 0
    }
    placed.push({ row, i, x: cx + rv, y: cy + rv, r: rv })
    cx += rv * 2 + 4
    rowH = Math.max(rowH, rv * 2)
  })

  const totalH = cy + rowH + 10
  const scale  = totalH > 0 ? Math.min(1, H / totalH) : 1

  return (
    <article className="chart-card bubble-chart-card" aria-label={`${title} bubble chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="bubble-wrap" style={{ position: 'relative' }}>
        {hovered !== null && (
          <div className="bubble-tooltip">
            <strong>{String(placed[hovered]?.row[labelKey] || '')}</strong>
            <span>{formatter(Number(placed[hovered]?.row[valueKey] || 0))}</span>
          </div>
        )}

        <svg
          viewBox={`0 0 ${W} ${Math.max(H, totalH * scale + 10)}`}
          width="100%"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
          style={{ display: 'block' }}
        >
          {placed.map((item, i) => {
            const x = item.x
            const y = item.y * scale
            const r = item.r * scale
            const color = PALETTE[i % PALETTE.length]
            const label = String(item.row[labelKey] || '')
            const shortLabel = label.length > 10 ? label.slice(0, 9) + '…' : label

            return (
              <g
                key={i}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              >
                <circle
                  cx={x} cy={y} r={r}
                  fill={color}
                  opacity={hovered === null || hovered === i ? 0.85 : 0.3}
                  style={{ transition: 'opacity 0.15s' }}
                />
                {r > 20 && (
                  <text x={x} y={y} textAnchor="middle" dominantBaseline="middle"
                    fill="#fff" fontSize={Math.min(r * 0.38, 11)} fontWeight="600"
                    style={{ pointerEvents: 'none' }}>
                    {shortLabel}
                  </text>
                )}
                {r > 26 && (
                  <text x={x} y={y + r * 0.38} textAnchor="middle"
                    fill="rgba(255,255,255,0.75)" fontSize={Math.min(r * 0.28, 9)}
                    style={{ pointerEvents: 'none' }}>
                    {formatter(Number(item.row[valueKey] || 0))}
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
