import { useState } from 'react'

/**
 * HeatmapChart
 * rows: array of { label, ...categoryKeys }
 * categories: string[]  — keys to display as columns
 * formatter: optional
 */
export default function HeatmapChart({
  title,
  subtitle,
  rows = [],
  labelKey = 'label',
  categories = [],
  formatter = (v) => new Intl.NumberFormat('en-IN').format(v),
  emptyMessage = 'No data available',
}) {
  const [hovered, setHovered] = useState(null) // { row, col }

  if (!rows.length || !categories.length) {
    return (
      <article className="chart-card heatmap-card">
        <div className="card-title">
          {subtitle && <span>{subtitle}</span>}
          <h2>{title}</h2>
        </div>
        <div className="chart-empty">{emptyMessage}</div>
      </article>
    )
  }

  // Compute global max for colour scaling
  const allVals = rows.flatMap((row) => categories.map((c) => Number(row[c] || 0)))
  const max = Math.max(...allVals, 1)

  const intensity = (v) => Number(v || 0) / max  // 0–1

  const isHov = (ri, ci) => hovered && hovered.row === ri && hovered.col === ci

  return (
    <article className="chart-card heatmap-card" aria-label={`${title} heatmap`}>
      <div className="card-title">
        {subtitle && <span>{subtitle}</span>}
        <h2>{title}</h2>
      </div>

      <div className="heatmap-wrap" style={{ overflowX: 'auto' }}>
        <table className="heatmap-table" role="grid">
          <thead>
            <tr>
              <th scope="col" className="heatmap-corner" />
              {categories.map((c) => (
                <th key={c} scope="col" className="heatmap-col-head">
                  {c.length > 12 ? c.slice(0, 11) + '…' : c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri}>
                <td className="heatmap-row-head">
                  {String(row[labelKey] || '').length > 16
                    ? String(row[labelKey]).slice(0, 15) + '…'
                    : String(row[labelKey] || '')}
                </td>
                {categories.map((c, ci) => {
                  const val = Number(row[c] || 0)
                  const alpha = intensity(val)
                  return (
                    <td
                      key={c}
                      className={`heatmap-cell${isHov(ri, ci) ? ' hov' : ''}`}
                      style={{ background: `rgba(99,102,241,${alpha * 0.75 + 0.04})` }}
                      onMouseEnter={() => setHovered({ row: ri, col: ci })}
                      onMouseLeave={() => setHovered(null)}
                      title={`${row[labelKey]} / ${c}: ${formatter(val)}`}
                      aria-label={`${row[labelKey]} ${c}: ${formatter(val)}`}
                    >
                      <span>{val > 0 ? formatter(val) : ''}</span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>

        {hovered && (
          <div className="heatmap-readout">
            <strong>{rows[hovered.row]?.[labelKey]}</strong>
            <span>{categories[hovered.col]}</span>
            <strong>{formatter(Number(rows[hovered.row]?.[categories[hovered.col]] || 0))}</strong>
          </div>
        )}
      </div>
    </article>
  )
}
