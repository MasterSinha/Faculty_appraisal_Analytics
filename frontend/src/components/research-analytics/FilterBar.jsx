export default function FilterBar({ filters, options, onChange, onReset }) {
  const schools       = options?.schools              || []
  const departments   = options?.departments           || []
  const years         = options?.years                 || []
  const indexingCats  = options?.indexing_categories   || []

  function handleChange(field, value) {
    onChange({ [field]: value })
  }

  const activeChips = Object.entries(filters).filter(
    ([key, val]) => val && key !== 'page' && key !== 'page_size' && key !== 'sort_by' && key !== 'sort_order'
  )

  return (
    <section className="filter-section" aria-label="Dashboard filters">
      <div className="filter-bar">

        {/* Academic Year */}
        <div className="filter-group">
          <label htmlFor="filter-year">Academic Year</label>
          <select
            id="filter-year"
            value={filters.year || ''}
            onChange={(e) => handleChange('year', e.target.value)}
          >
            <option value="">All Years</option>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        {/* School */}
        <div className="filter-group">
          <label htmlFor="filter-school">School</label>
          <select
            id="filter-school"
            value={filters.school || ''}
            onChange={(e) => handleChange('school', e.target.value)}
          >
            <option value="">All Schools</option>
            {schools.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Department */}
        <div className="filter-group">
          <label htmlFor="filter-dept">Department</label>
          <select
            id="filter-dept"
            value={filters.department || ''}
            onChange={(e) => handleChange('department', e.target.value)}
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Indexing */}
        <div className="filter-group">
          <label htmlFor="filter-indexing">Indexing</label>
          <select
            id="filter-indexing"
            value={filters.indexing || ''}
            onChange={(e) => handleChange('indexing', e.target.value)}
          >
            <option value="">All Indexing</option>
            {indexingCats.map((idx) => (
              <option key={idx} value={idx}>{idx}</option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div className="filter-group search-group">
          <label htmlFor="filter-search">Search Faculty</label>
          <input
            id="filter-search"
            type="text"
            placeholder="Search by name or ID…"
            value={filters.search || ''}
            onChange={(e) => handleChange('search', e.target.value)}
          />
        </div>

        <button type="button" className="btn-reset" onClick={onReset} title="Reset all filters">
          ✕ Reset
        </button>
      </div>

      {/* Active filter chips */}
      {activeChips.length > 0 && (
        <div className="active-chips">
          <span className="chips-label">Active Filters:</span>
          {activeChips.map(([key, val]) => (
            <span key={key} className="chip">
              <strong>{key}:</strong>&nbsp;{val}
              <button type="button" onClick={() => handleChange(key, '')} aria-label={`Remove ${key} filter`}>×</button>
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
