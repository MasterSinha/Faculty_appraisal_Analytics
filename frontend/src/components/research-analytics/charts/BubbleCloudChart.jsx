const PALETTE = [
  '#6366f1', '#06b6d4', '#22c55e', '#f59e0b',
  '#a855f7', '#ec4899', '#14b8a6', '#3b82f6',
]

function initials(label) {
  const words = String(label || 'NA').replace(/[^a-zA-Z0-9 ]/g, ' ').split(/\s+/).filter(Boolean)
  if (!words.length) return 'NA'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return words.slice(0, 3).map((word) => word[0]).join('').toUpperCase()
}

export default function BubbleCloudChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (value) => new Intl.NumberFormat('en-IN').format(value || 0),
  emptyMessage = 'No data available',
  maxItems = 20,
}) {
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

  const max = Math.max(...data.map((row) => Number(row[valueKey] || 0)), 1)

  return (
    <article className="chart-card bubble-chart-card" aria-label={`${title} bubble chart`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="bubble-panel">
        <div className="bubble-wrap">
          <div className="bubble-cloud bubble-cloud-modern">
            {data.map((row, index) => {
              const value = Number(row[valueKey] || 0)
              const color = PALETTE[index % PALETTE.length]
              const size = 76 + (value / max) * 76
              const label = String(row[labelKey] || 'Not specified')

              return (
                <button
                  type="button"
                  className="bubble-cloud-node"
                  key={`${label}-${index}`}
                  style={{ '--bubble-color': color, width: size, height: size }}
                  title={`${label}: ${formatter(value)}`}
                >
                  <span className="bubble-rank">{index + 1}</span>
                  <strong>{formatter(value)}</strong>
                  <span className="bubble-short">{initials(label)}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="bubble-legend-list">
          {data.map((row, index) => {
            const value = Number(row[valueKey] || 0)
            const color = PALETTE[index % PALETTE.length]
            const label = String(row[labelKey] || 'Not specified')
            return (
              <div className="bubble-legend-item" key={`${label}-legend-${index}`} style={{ '--bubble-color': color }}>
                <span className="bubble-legend-dot" />
                <span className="bubble-legend-label">{label}</span>
                <strong>{formatter(value)}</strong>
                {row.count !== undefined && <em>{formatter(row.count)} records</em>}
              </div>
            )
          })}
        </div>
      </div>
    </article>
  )
}
