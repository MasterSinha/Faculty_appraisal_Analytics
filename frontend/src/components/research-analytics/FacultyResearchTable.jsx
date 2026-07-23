import EmptyState from './EmptyState'

export default function FacultyResearchTable({ data, filters, onFilterChange, onViewDetails }) {
  const items = data?.items || []

  return (
    <article className="table-card">
      <div className="table-toolbar">
        <div>
          <span>Faculty analytics</span>
          <h2>One row per faculty member</h2>
        </div>
        <select value={filters.sort_by} onChange={(event) => onFilterChange({ sort_by: event.target.value })}>
          <option value="total_research_papers">Sort by papers</option>
          <option value="research_projects">Sort by projects</option>
          <option value="total_funding">Sort by funding</option>
          <option value="total_vc_score">Sort by VC score</option>
        </select>
      </div>

      {!items.length ? (
        <EmptyState />
      ) : (
        <div className="research-table">
          <div className="research-table-head">
            {['SN', 'Faculty Name', 'Employee ID', 'School', 'Department', 'Total Papers', 'SCI', 'Scopus', 'UGC', 'Books', 'Conferences', 'Patents', 'Projects', 'Funding', 'VC Score', 'Action'].map((head) => (
              <span key={head}>{head}</span>
            ))}
          </div>
          {items.map((item, index) => (
            <div className="research-table-row" key={item.faculty_id}>
              <span>{(data.page - 1) * data.page_size + index + 1}</span>
              <strong>{item.faculty_name}</strong>
              <span>{item.employee_id || '-'}</span>
              <span>{item.school || '-'}</span>
              <span>{item.department || '-'}</span>
              <span>{item.total_research_papers}</span>
              <span>{item.sci_papers}</span>
              <span>{item.scopus_papers}</span>
              <span>{item.ugc_papers}</span>
              <span>{item.book_publications}</span>
              <span>{item.conference_publications}</span>
              <span>{item.patents}</span>
              <span>{item.research_projects}</span>
              <span>{new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(item.total_funding || 0)}</span>
              <span>{item.total_vc_score}</span>
              <button type="button" onClick={() => onViewDetails(item.faculty_id)}>View Details</button>
            </div>
          ))}
        </div>
      )}

      <footer className="pagination">
        <button type="button" disabled={data.page <= 1} onClick={() => onFilterChange({ page: data.page - 1 })}>Previous</button>
        <span>Page {data.page} of {data.total_pages || 1}</span>
        <button type="button" disabled={data.page >= data.total_pages} onClick={() => onFilterChange({ page: data.page + 1 })}>Next</button>
      </footer>
    </article>
  )
}

