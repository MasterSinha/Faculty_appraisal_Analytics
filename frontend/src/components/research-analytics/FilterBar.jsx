export default function FilterBar({ filters, options, onChange, onReset }) {
  const schools      = (options?.schools || []).filter((school) => !['engineering', 'non engineering'].includes(String(school).trim().toLowerCase()))
  const departments  = options?.departments          || []
  const years        = options?.academic_years || options?.years || []
  const designations = options?.designations         || []
  const indexingCats = options?.indexing_categories  || []

  function handleChange(field, value) {
    onChange({ [field]: value })
  }

  const activeChips = Object.entries(filters).filter(
    ([key, val]) => val && key !== 'page' && key !== 'page_size' && key !== 'sort_by' && key !== 'sort_order'
  )

  const LABEL_MAP = {
    year: 'Year', school: 'School', department: 'Department',
    designation: 'Designation', category: 'Category',
    indexing: 'Indexing', search: 'Search',
  }

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
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
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
            {schools.map((s) => <option key={s} value={s}>{s}</option>)}
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
            {departments.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>

        {/* Designation */}
        <div className="filter-group">
          <label htmlFor="filter-designation">Designation</label>
          <select
            id="filter-designation"
            value={filters.designation || ''}
            onChange={(e) => handleChange('designation', e.target.value)}
          >
            <option value="">All Designations</option>
            {designations.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>

        {/* Category */}
        <div className="filter-group">
          <label htmlFor="filter-category">Category</label>
          <select
            id="filter-category"
            value={filters.category || ''}
            onChange={(e) => handleChange('category', e.target.value)}
          >
            <option value="">All Categories</option>
            {['Journals', 'Books', 'Patents', 'Projects', 'Proposals', 'Guidance', 'Conferences', 'Awards', 'Products'].map(
              (item) => <option key={item} value={item}>{item}</option>
            )}
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
            {indexingCats.map((idx) => <option key={idx} value={idx}>{idx}</option>)}
          </select>
        </div>

        {/* Search */}
        <div className="filter-group search-group">
          <label htmlFor="filter-search">Search Faculty</label>
          <input
            id="filter-search"
            type="text"
            placeholder="Name or employee ID…"
            value={filters.search || ''}
            onChange={(e) => handleChange('search', e.target.value)}
          />
        </div>

        <button type="button" className="btn-reset" onClick={onReset} title="Clear all filters">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
          Reset
        </button>
      </div>

      {/* Active filter chips */}
      {activeChips.length > 0 && (
        <div className="active-chips">
          <span className="chips-label">Active:</span>
          {activeChips.map(([key, val]) => (
            <span key={key} className="chip">
              <strong>{LABEL_MAP[key] || key}:</strong>&nbsp;{String(val).length > 18 ? String(val).slice(0, 18) + '…' : val}
              <button
                type="button"
                onClick={() => handleChange(key, '')}
                aria-label={`Remove ${key} filter`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
