const PALETTE = ['#6366f1', '#06b6d4', '#22c55e', '#f59e0b', '#a855f7', '#ec4899']
const MEDALS = ['\uD83E\uDD47', '\uD83E\uDD48', '\uD83E\uDD49']

export default function RankingList({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  badgeKey,
  formatter = (value) => new Intl.NumberFormat('en-IN').format(value || 0),
  badgeFormatter,
  maxItems = 10,
  emptyMessage = 'No ranking data available',
}) {
  const data = [...rows]
    .sort((a, b) => Number(b[valueKey] || 0) - Number(a[valueKey] || 0))
    .slice(0, maxItems)

  if (!data.length) {
    return (
      <article className="chart-card ranking-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  const max = Math.max(...data.map((row) => Number(row[valueKey] || 0)), 1)
  const formatBadge = badgeFormatter || formatter

  return (
    <article className="chart-card ranking-card" aria-label={`${title} ranking`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <ol className="ranking-list" aria-label={title}>
        {data.map((row, index) => {
          const value = Number(row[valueKey] || 0)
          const width = (value / max) * 100
          const color = PALETTE[index % PALETTE.length]
          const badgeValue = badgeKey ? row[badgeKey] : null

          return (
            <li className="ranking-row" key={`${row[labelKey] || 'rank'}-${index}`}>
              <span className="rank-num" aria-label={`Rank ${index + 1}`}>
                {index < 3 ? MEDALS[index] : <span className="rank-digit">{index + 1}</span>}
              </span>
              <div className="rank-body">
                <div className="rank-label-row">
                  <span className="rank-label">{row[labelKey] || 'Not specified'}</span>
                  <span className="rank-value" style={{ color }}>{formatter(value)}</span>
                </div>
                <div className="rank-bar-track">
                  <span
                    className="rank-bar-fill"
                    style={{
                      width: `${Math.max(width, value > 0 ? 3 : 0)}%`,
                      background: `linear-gradient(90deg, ${color}, ${color}99)`,
                    }}
                  />
                </div>
              </div>
              {badgeValue !== null && badgeValue !== undefined && (
                <span className="rank-badge" style={{ borderColor: `${color}55`, color }}>
                  {formatBadge(badgeValue)}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </article>
  )
}
