/**
 * SparklineRow — a compact inline sparkline (area + line) for embedding
 *   inside metric cards or table rows.
 * Props:
 *   values   number[]   raw values in order
 *   color    string     CSS color
 *   width    number     px
 *   height   number     px
 *   label    string     optional overlay label
 */
export default function SparklineRow({
  values = [],
  color = '#6366f1',
  width = 80,
  height = 28,
  label = '',
}) {
  if (!values.length) return null

  const max  = Math.max(...values, 1)
  const min  = Math.min(...values, 0)
  const range = max - min || 1
  const n    = values.length
  const PAD  = 2

  const toX = (i) => PAD + (i / Math.max(n - 1, 1)) * (width - PAD * 2)
  const toY = (v) => PAD + (1 - (v - min) / range) * (height - PAD * 2)

  const pts  = values.map((v, i) => ({ x: toX(i), y: toY(v) }))
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const area = `${line} L${pts[pts.length - 1].x},${height - PAD} L${pts[0].x},${height - PAD} Z`

  const last = pts[pts.length - 1]
  const prev = pts[pts.length - 2]
  const trend = prev ? (values[n - 1] > values[n - 2] ? 'up' : values[n - 1] < values[n - 2] ? 'down' : 'flat') : 'flat'

  return (
    <div className="sparkline-row" aria-label={label || 'Trend sparkline'}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
        <defs>
          <linearGradient id={`sg-${color.replace(/[^a-z0-9]/gi, '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {/* Area */}
        <path d={area} fill={`url(#sg-${color.replace(/[^a-z0-9]/gi, '')})`} />
        {/* Line */}
        <path d={line} fill="none" stroke={color} strokeWidth="1.5"
          strokeLinecap="round" strokeLinejoin="round" />
        {/* Last point dot */}
        <circle cx={last.x} cy={last.y} r="2.5"
          fill={color} stroke="var(--surface)" strokeWidth="1" />
      </svg>

      {/* Trend arrow */}
      <span
        className={`sparkline-trend sparkline-${trend}`}
        aria-label={`Trend: ${trend}`}
      >
        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
      </span>
    </div>
  )
}
