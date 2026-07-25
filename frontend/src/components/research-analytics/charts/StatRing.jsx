/**
 * StatRing — animated SVG donut ring for a single percentage / ratio.
 * Props:
 *   value       number   0–100 (percentage)
 *   label       string   text below value
 *   subtext     string   tiny caption
 *   color       string   CSS color
 *   size        number   diameter in px (default 90)
 *   strokeWidth number   ring thickness (default 8)
 *   formatter   fn       (value) => string  — display format
 */
export default function StatRing({
  value = 0,
  label = '',
  subtext = '',
  color = '#6366f1',
  size = 90,
  strokeWidth = 8,
  formatter = (v) => `${Number(v || 0).toFixed(1)}%`,
}) {
  const clampedValue = Math.max(0, Math.min(Number(value) || 0, 100))
  const r = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * r
  const dash = (clampedValue / 100) * circumference
  const gap  = circumference - dash
  const cx   = size / 2
  const cy   = size / 2

  return (
    <div className="stat-ring-wrap" aria-label={`${label}: ${formatter(clampedValue)}`}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden="true"
        style={{ display: 'block', flexShrink: 0 }}
      >
        {/* Track */}
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="var(--surface-3)"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${gap}`}
          strokeDashoffset={circumference / 4}  /* start at top */
          style={{
            transition: 'stroke-dasharray 0.7s cubic-bezier(0.4,0,0.2,1)',
            filter: `drop-shadow(0 0 4px ${color}88)`,
          }}
        />
        {/* Center value */}
        <text
          x={cx} y={cy - 3}
          textAnchor="middle"
          dominantBaseline="middle"
          fill={color}
          fontSize={size * 0.2}
          fontWeight="800"
        >
          {formatter(clampedValue)}
        </text>
      </svg>
      {label && (
        <span className="stat-ring-label">{label}</span>
      )}
      {subtext && (
        <span className="stat-ring-subtext">{subtext}</span>
      )}
    </div>
  )
}
