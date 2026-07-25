/**
 * TileGrid — proportional contribution grid
 * rows: [{ label, value }]
 * Each tile's area is proportional to its value.
 * Rendered as flex-wrap tiles with font-size scaling.
 */
export default function TileGrid({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No data available',
  maxItems = 24,
}) {
  const data = [...rows]
    .filter((r) => Number(r[valueKey] || 0) > 0)
    .sort((a, b) => Number(b[valueKey] || 0) - Number(a[valueKey] || 0))
    .slice(0, maxItems)

  if (!data.length) {
    return (
      <article className="chart-card tilegrid-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const total = data.reduce((s, r) => s + Number(r[valueKey] || 0), 0) || 1

  const PALETTE = [
    '#6366f1','#06b6d4','#22c55e','#f59e0b',
    '#a855f7','#ec4899','#14b8a6','#3b82f6',
    '#84cc16','#f97316',
  ]

  return (
    <article className="chart-card tilegrid-card" aria-label={`${title} tile grid`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="tilegrid-wrap">
        {data.map((row, i) => {
          const val  = Number(row[valueKey] || 0)
          const frac = val / total
          // flex-basis proportional to share, min 80px
          const basis = Math.max(frac * 100, 8)
          const color = PALETTE[i % PALETTE.length]

          return (
            <div
              key={i}
              className="tilegrid-tile"
              style={{
                flexBasis: `${basis}%`,
                flexGrow: frac * 10,
                background: `${color}22`,
                borderColor: `${color}55`,
              }}
              title={`${row[labelKey]}: ${formatter(val)} (${(frac * 100).toFixed(1)}%)`}
            >
              <span
                className="tile-label"
                style={{ color }}
              >
                {String(row[labelKey] || '').length > 18
                  ? String(row[labelKey]).slice(0, 17) + '…'
                  : String(row[labelKey] || '')}
              </span>
              <strong className="tile-value" style={{ color }}>
                {formatter(val)}
              </strong>
              <span className="tile-pct" style={{ color: `${color}bb` }}>
                {(frac * 100).toFixed(1)}%
              </span>
            </div>
          )
        })}
      </div>
    </article>
  )
}
