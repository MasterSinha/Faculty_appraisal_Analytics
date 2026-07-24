export default function FilterBar({ filters, options, onChange, onReset }) {
  const schools = options?.schools || []
  const departments = options?.departments || []
  const years = options?.years || []
  const indexingCats = options?.indexing_categories || []

  function handleChange(field, value) {
    onChange({ [field]: value })
  }

  const activeChips = Object.entries(filters).filter(([key, val]) => val && key !== 'page' && key !== 'page_size' && key !== 'sort_by' && key !== 'sort_order')

  return (
    <section className="filter-section">
      <div className="filter-bar">
        <div className="filter-group">
          <label>Academic Year</label>
          <select value={filters.year || ''} onChange={(e) => handleChange('year', e.target.value)}>
            <option value="">All Years</option>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>School</label>
          <select value={filters.school || ''} onChange={(e) => handleChange('school', e.target.value)}>
            <option value="">All Schools</option>
            {schools.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Department</label>
          <select value={filters.department || ''} onChange={(e) => handleChange('department', e.target.value)}>
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Indexing</label>
          <select value={filters.indexing || ''} onChange={(e) => handleChange('indexing', e.target.value)}>
            <option value="">All Indexing</option>
            {indexingCats.map((idx) => (
              <option key={idx} value={idx}>{idx}</option>
            ))}
          </select>
        </div>

        <div className="filter-group search-group">
          <label>Search Faculty</label>
          <input
            type="text"
            placeholder="Search by name or ID..."
            value={filters.search || ''}
            onChange={(e) => handleChange('search', e.target.value)}
          />
        </div>

        <button type="button" className="btn-reset" onClick={onReset} title="Reset all filters">
          Reset All
        </button>
      </div>

      {activeChips.length > 0 && (
        <div className="active-chips">
          <span className="chips-label">Active Filters:</span>
          {activeChips.map(([key, val]) => (
            <span key={key} className="chip">
              <strong>{key}:</strong> {val}
              <button type="button" onClick={() => handleChange(key, '')}>×</button>
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
