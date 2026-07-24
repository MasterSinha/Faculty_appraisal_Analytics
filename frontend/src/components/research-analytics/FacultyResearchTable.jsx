import EmptyState from './EmptyState'

const HEADS = [
  'SN', 'Faculty Name', 'Employee ID', 'School', 'Department',
  'Papers', 'SCI', 'Scopus', 'UGC', 'Books',
  'Conf.', 'Patents', 'Projects', 'Funding', 'VC Score', 'Action',
]

export default function FacultyResearchTable({ data, filters, onFilterChange, onViewDetails }) {
  const items = data?.items || []

  return (
    <article className="table-card" aria-label="Faculty research table">
      {/* Toolbar */}
      <div className="table-toolbar">
        <div>
          <span>Faculty Analytics</span>
          <h2>One row per faculty member</h2>
        </div>
        <select
          value={filters.sort_by}
          onChange={(e) => onFilterChange({ sort_by: e.target.value })}
          aria-label="Sort by"
        >
          <option value="total_research_papers">Sort: Papers</option>
          <option value="research_projects">Sort: Projects</option>
          <option value="total_funding">Sort: Funding</option>
          <option value="total_vc_score">Sort: VC Score</option>
        </select>
      </div>

      {!items.length ? (
        <EmptyState />
      ) : (
        <div className="research-table" role="table" aria-label="Faculty list">
          {/* Header row */}
          <div className="research-table-head" role="row">
            {HEADS.map((h) => (
              <span key={h} role="columnheader">{h}</span>
            ))}
          </div>

          {/* Data rows */}
          {items.map((item, index) => (
            <div
              className="research-table-row"
              key={item.faculty_id}
              role="row"
            >
              <span>{(data.page - 1) * data.page_size + index + 1}</span>
              <strong title={item.faculty_name}>{item.faculty_name}</strong>
              <span>{item.employee_id || '—'}</span>
              <span title={item.school}>{item.school || '—'}</span>
              <span title={item.department}>{item.department || '—'}</span>
              <span>{item.total_research_papers}</span>
              <span>{item.sci_papers}</span>
              <span>{item.scopus_papers}</span>
              <span>{item.ugc_papers}</span>
              <span>{item.book_publications}</span>
              <span>{item.conference_publications}</span>
              <span>{item.patents}</span>
              <span>{item.research_projects}</span>
              <span>
                {new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(item.total_funding || 0)}
              </span>
              <span>{item.total_vc_score}</span>
              <button
                type="button"
                onClick={() => onViewDetails(item.faculty_id)}
                aria-label={`View details for ${item.faculty_name}`}
              >
                View →
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <footer className="pagination">
        <button
          type="button"
          disabled={data.page <= 1}
          onClick={() => onFilterChange({ page: data.page - 1 })}
        >
          ← Previous
        </button>
        <span>Page {data.page} of {data.total_pages || 1}</span>
        <button
          type="button"
          disabled={data.page >= data.total_pages}
          onClick={() => onFilterChange({ page: data.page + 1 })}
        >
          Next →
        </button>
      </footer>
    </article>
  )
}
