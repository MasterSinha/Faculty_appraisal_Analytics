export default function AnalyticsFilters({ filters, options, onChange }) {
  const update = (key, value) => onChange({ [key]: value })

  return (
    <section className="analytics-filters" aria-label="Research analytics filters">
      <label>
        Search
        <input
          value={filters.search}
          onChange={(event) => update('search', event.target.value)}
          placeholder="Faculty name or employee ID"
          type="search"
        />
      </label>
      <label>
        School
        <select value={filters.school} onChange={(event) => update('school', event.target.value)}>
          <option value="">All schools</option>
          {(options?.schools || []).map((item) => <option key={item}>{item}</option>)}
        </select>
      </label>
      <label>
        Department
        <select value={filters.department} onChange={(event) => update('department', event.target.value)}>
          <option value="">All departments</option>
          {(options?.departments || []).map((item) => <option key={item}>{item}</option>)}
        </select>
      </label>
      <label>
        Year
        <select value={filters.year} onChange={(event) => update('year', event.target.value)}>
          <option value="">All years</option>
          {(options?.years || []).map((item) => <option key={item}>{item}</option>)}
        </select>
      </label>
      <label>
        Indexing
        <select value={filters.indexing} onChange={(event) => update('indexing', event.target.value)}>
          <option value="">All indexing</option>
          {(options?.indexing_categories || []).map((item) => <option key={item}>{item}</option>)}
        </select>
      </label>
    </section>
  )
}

