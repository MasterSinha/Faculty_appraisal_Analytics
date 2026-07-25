export default function HorizontalBarChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  valueKey = 'value',
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No data available',
}) {
  const data = rows.filter((row) => row[labelKey] != null)
  const max = Math.max(...data.map((row) => Number(row[valueKey] || 0)), 1)

  return (
    <article className="chart-card hbar-chart-card">
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>
      {data.length ? (
        <div className="horizontal-chart">
          {data.slice(0, 10).map((row) => {
            const value = Number(row[valueKey] || 0)
            return (
              <div className="hbar-row" key={`${title}-${row[labelKey]}`}>
                <span title={String(row[labelKey])}>{row[labelKey]}</span>
                <div><i style={{ width: `${(value / max) * 100}%` }} /></div>
                <strong>{formatter(value)}</strong>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="chart-empty">{emptyMessage}</div>
      )}
    </article>
  )
}
