const cards = [
  ['Total Research Papers', 'total_research_papers'],
  ['Faculty with Publications', 'faculty_with_research'],
  ['Research Projects', 'total_projects'],
  ['Total Research Funding', 'total_funding', 'currency'],
  ['Total Patents', 'total_patents'],
  ['Book Publications', 'total_books'],
  ['Conferences', 'total_conferences'],
  ['Total VC Approved Score', 'total_vc_score'],
]

function formatValue(value, type) {
  if (type === 'currency') {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0)
  }
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

export default function OverviewCards({ overview }) {
  return (
    <section className="overview-grid">
      {cards.map(([title, key, type]) => (
        <article className="metric-card" key={key}>
          <span>{title}</span>
          <strong>{formatValue(overview?.[key], type)}</strong>
          <small>Live API aggregate</small>
        </article>
      ))}
    </section>
  )
}

