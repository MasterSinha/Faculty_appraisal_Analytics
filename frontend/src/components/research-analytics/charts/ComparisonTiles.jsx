/**
 * ComparisonTiles — side-by-side big-number comparison cards.
 * items: [{ label, value, subtext?, color? }]
 */
export default function ComparisonTiles({
  title,
  subtitle,
  items = [],
  emptyMessage = 'No comparison data',
}) {
  if (!items.length) {
    return (
      <article className="chart-card comparison-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const DEFAULTS = ['#6366f1','#22c55e','#f59e0b','#ef4444','#06b6d4','#a855f7']

  return (
    <article className="chart-card comparison-card" aria-label={`${title} comparison`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="comparison-tiles">
        {items.map((item, i) => {
          const color = item.color || DEFAULTS[i % DEFAULTS.length]
          return (
            <div
              key={i}
              className="comparison-tile"
              style={{
                borderColor: `${color}44`,
                background: `${color}0d`,
              }}
            >
              <div className="ct-top-bar" style={{ background: color }} />
              <span className="ct-label">{item.label}</span>
              <strong className="ct-value" style={{ color }}>{item.value}</strong>
              {item.subtext && (
                <span className="ct-subtext">{item.subtext}</span>
              )}
              {item.badge && (
                <span className="ct-badge" style={{ background: `${color}22`, color }}>
                  {item.badge}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </article>
  )
}
