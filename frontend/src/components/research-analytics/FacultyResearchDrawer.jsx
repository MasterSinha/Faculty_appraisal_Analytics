import EmptyState from './EmptyState'

const tabs = [
  ['journal_publications', 'Journal Publications'],
  ['book_publications', 'Book Publications'],
  ['conferences', 'Conferences'],
  ['patents', 'Patents and IPR'],
  ['research_projects', 'Research Projects'],
  ['research_guidance', 'Research Guidance'],
  ['awards', 'Awards'],
]

export default function FacultyResearchDrawer({ detail, activeTab, onTabChange, onClose }) {
  if (!detail) return null
  const faculty = detail.faculty || {}
  const rows = detail.records?.[activeTab] || []

  return (
    <aside className="drawer-backdrop">
      <section className="faculty-drawer">
        <header>
          <div>
            <span>{faculty.employee_id || 'Faculty profile'}</span>
            <h2>{faculty.faculty_name || 'Faculty detail'}</h2>
            <p>{faculty.email || '-'} · {faculty.school || '-'} · {faculty.department || '-'}</p>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </header>

        <div className="drawer-metrics">
          {[
            ['Total papers', faculty.total_research_papers],
            ['Projects', faculty.research_projects],
            ['Patents', faculty.patents],
            ['Funding', faculty.total_funding],
            ['VC Score', faculty.total_vc_score],
          ].map(([label, value]) => (
            <article key={label}>
              <span>{label}</span>
              <strong>{value || 0}</strong>
            </article>
          ))}
        </div>

        <nav className="drawer-tabs">
          {tabs.map(([key, label]) => (
            <button className={activeTab === key ? 'active' : ''} type="button" key={key} onClick={() => onTabChange(key)}>
              {label}
            </button>
          ))}
          <button className={activeTab === 'score_analysis' ? 'active' : ''} type="button" onClick={() => onTabChange('score_analysis')}>
            Score Analysis
          </button>
        </nav>

        {activeTab === 'score_analysis' ? (
          <pre className="record-json">{JSON.stringify(detail.score_summary, null, 2)}</pre>
        ) : rows.length ? (
          <div className="record-list">
            {rows.map((row, index) => (
              <pre className="record-json" key={row.id || index}>{JSON.stringify(row, null, 2)}</pre>
            ))}
          </div>
        ) : (
          <EmptyState title="No detail records" message="No records were returned for this section." />
        )}
      </section>
    </aside>
  )
}
