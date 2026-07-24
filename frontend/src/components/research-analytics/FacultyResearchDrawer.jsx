import EmptyState from './EmptyState'

const tabs = [
  ['journal_publications', 'Journal Publications'],
  ['book_publications',    'Book Publications'],
  ['conferences',          'Conferences'],
  ['patents',              'Patents & IPR'],
  ['research_projects',    'Research Projects'],
  ['research_guidance',    'Research Guidance'],
  ['awards',               'Awards'],
]

const fieldLabels = {
  title:           'Title',
  journal:         'Journal',
  book:            'Book',
  publisher:       'Publisher',
  indexing:        'Indexing',
  issn:            'ISSN',
  isbn:            'ISBN',
  agency:          'Agency',
  amount:          'Amount',
  role:            'Role',
  project_status:  'Status',
  patent_status:   'Status',
  type:            'Type',
  scope:           'Scope',
  degree:          'Degree',
  student_name:    'Student',
  thesis:          'Thesis',
  organization:    'Organization',
  level:           'Level',
  score:           'Score',
  hod_score:       'HOD',
  director_score:  'Director',
  dean_score:      'Dean',
  vc_score:        'VC',
  academic_year:   'Academic Year',
}

const primaryFields = [
  'title', 'journal', 'book', 'publisher', 'indexing',
  'agency', 'amount', 'project_status', 'patent_status',
  'degree', 'student_name', 'thesis', 'organization', 'level',
  'score', 'hod_score', 'director_score', 'dean_score', 'vc_score', 'academic_year',
]

function formatValue(key, value) {
  if (value === null || value === undefined || value === '') return '—'
  if (key === 'amount') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number(value) || 0)
  }
  return String(value)
}

function getRecordTitle(record, index) {
  return record.title || record.journal || record.book || record.thesis || record.details || `Record ${index + 1}`
}

function ResearchRecordCard({ record, index }) {
  const visibleFields = primaryFields.filter((field) => field in record)

  return (
    <article className="detail-record-card">
      <div className="detail-record-head">
        <div>
          <span>#{index + 1}</span>
          <h3>{getRecordTitle(record, index)}</h3>
        </div>
        {record.indexing        && <strong className="detail-badge">{record.indexing}</strong>}
        {record.project_status  && <strong className="detail-badge">{record.project_status}</strong>}
        {record.patent_status   && <strong className="detail-badge">{record.patent_status}</strong>}
      </div>

      <div className="detail-field-grid">
        {visibleFields.map((field) => (
          <div className="detail-field" key={field}>
            <span>{fieldLabels[field] || field.replaceAll('_', ' ')}</span>
            <strong>{formatValue(field, record[field])}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

function ScorePanel({ summary }) {
  const entries = Object.entries(summary || {})

  if (!entries.length) {
    return (
      <EmptyState
        title="No score summary"
        message="No reviewer score data was returned for this faculty member."
      />
    )
  }

  return (
    <div className="score-summary-grid">
      {entries.map(([key, value]) => (
        <article key={key}>
          <span>{fieldLabels[key] || key.replaceAll('_', ' ')}</span>
          <strong>{formatValue(key, value)}</strong>
        </article>
      ))}
    </div>
  )
}

export default function FacultyResearchDrawer({ detail, activeTab, onTabChange, onClose }) {
  if (!detail) return null

  const faculty = detail.faculty || {}
  const rows    = detail.records?.[activeTab] || []
  const totalFunding = faculty.total_funding || faculty.project_funding || 0

  const initials = (faculty.faculty_name || faculty.full_name || 'FA')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

  return (
    <aside
      className="drawer-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Faculty research profile"
    >
      <section className="faculty-drawer">
        {/* ── Header ── */}
        <header className="drawer-header">
          <div className="drawer-profile">
            <span className="drawer-avatar" aria-hidden="true">{initials}</span>
            <div>
              <small>{faculty.employee_id || 'Faculty Profile'}</small>
              <h2>{faculty.faculty_name || faculty.full_name || 'Faculty detail'}</h2>
              <p>
                {faculty.email || faculty.faculty_email || '—'}
                &nbsp;|&nbsp;{faculty.school || '—'}
                &nbsp;|&nbsp;{faculty.department || '—'}
              </p>
            </div>
          </div>
          <button className="drawer-close" type="button" onClick={onClose} aria-label="Close drawer">
            ✕ Close
          </button>
        </header>

        {/* ── Metric tiles ── */}
        <div className="drawer-metrics">
          {[
            ['Total Papers',    faculty.total_research_papers || faculty.journal_publications],
            ['Projects',        faculty.research_projects],
            ['Patents',         faculty.patents],
            ['Funding',         totalFunding, 'currency'],
            ['Research Score',  faculty.total_vc_score || faculty.total_research_score],
          ].map(([label, value, type]) => (
            <article key={label}>
              <span>{label}</span>
              <strong>
                {type === 'currency' ? formatValue('amount', value) : (value ?? 0)}
              </strong>
            </article>
          ))}
        </div>

        {/* ── Tab bar ── */}
        <nav className="drawer-tabs" aria-label="Faculty detail sections">
          {tabs.map(([key, label]) => (
            <button
              key={key}
              className={activeTab === key ? 'active' : ''}
              type="button"
              onClick={() => onTabChange(key)}
            >
              {label}
            </button>
          ))}
          <button
            className={activeTab === 'score_analysis' ? 'active' : ''}
            type="button"
            onClick={() => onTabChange('score_analysis')}
          >
            Score Analysis
          </button>
        </nav>

        {/* ── Content ── */}
        <section className="drawer-content">
          {activeTab === 'score_analysis' ? (
            <ScorePanel summary={detail.score_summary} />
          ) : rows.length ? (
            <div className="detail-record-list">
              {rows.map((row, index) => (
                <ResearchRecordCard
                  record={row}
                  index={index}
                  key={row.id || `${activeTab}-${index}`}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No detail records"
              message="No records were returned for this section."
            />
          )}
        </section>
      </section>
    </aside>
  )
}
