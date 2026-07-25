import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import BubbleCloudChart from '../components/research-analytics/charts/BubbleCloudChart'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Overview', 'Department Analysis', 'Faculty Analysis', 'Quality and Indexing', 'Publication Records']

function isPresent(value) {
  return value !== null && value !== undefined && String(value).trim() !== ''
}

function isValidPublication(record) {
  return isPresent(record.title)
}

function isIndexed(record) {
  return isPresent(record.indexing) && !['not specified', 'na', 'n/a', 'none'].includes(String(record.indexing).trim().toLowerCase())
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Not specified'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function finalScore(record) {
  return record.vc_score ?? record.dean_score ?? record.director_score ?? record.hod_score ?? record.score ?? 0
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('indexing') || context.includes('distribution')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department output') || context.includes('score')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('journal') || context.includes('faculty')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function QuadrantChart({ rows }) {
  return (
    <article className="chart-card journal-chart-card">
      <div className="card-title">
        <span>Department positioning</span>
        <h2>Participation vs output quadrant</h2>
      </div>
      <div className="quadrant-chart">
        {rows.map((row) => {
          const x = Math.min(Number(row.participation || 0), 100)
          const y = Math.min(Number(row.papersPerActive || 0) * 25, 100)
          return (
            <span
              className="quadrant-dot"
              key={row.department}
              style={{ left: `${x}%`, bottom: `${y}%` }}
              title={`${row.department}: ${percent(row.participation)}, ${row.papersPerActive.toFixed(2)} papers/faculty`}
            >
              {String(row.department || '?').slice(0, 2).toUpperCase()}
            </span>
          )
        })}
        <div className="quadrant-label q1">High output, broad participation</div>
        <div className="quadrant-label q2">High output, concentrated</div>
        <div className="quadrant-label q3">Broad participation, moderate output</div>
        <div className="quadrant-label q4">Low output, low participation</div>
      </div>
    </article>
  )
}

function PublicationRecordsTable({ records }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('academic_year')
  const [page, setPage] = useState(1)
  const pageSize = 10

  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return records
      .filter((record) => JSON.stringify(record).toLowerCase().includes(query))
      .sort((a, b) => String(b[sortBy] || '').localeCompare(String(a[sortBy] || '')))
  }, [records, search, sortBy])

  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.max(Math.ceil(filtered.length / pageSize), 1)

  return (
    <article className="table-card books-table-card">
      <div className="table-toolbar">
        <div>
          <span>Publication records</span>
          <h2>Journal publication records</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="journal">Sort by journal</option>
            <option value="department">Sort by department</option>
          </select>
          <button type="button">Columns</button>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="journal-table">
        <div className="journal-table-head">
          {['Faculty', 'Department', 'School', 'Title', 'Journal', 'ISSN', 'Indexing', 'Academic year'].map((column) => (
            <span key={column}>{column}</span>
          ))}
        </div>
        {pageItems.map((record, index) => (
          <div className="journal-table-row" key={record.id || `${record.faculty_email}-${index}`}>
            <strong>{record.full_name || record.faculty_name || record.faculty_email || '-'}</strong>
            <span>{departmentLabel(record)}</span>
            <span>{record.school || '-'}</span>
            <span>{record.title || '-'}</span>
            <span>{record.journal || '-'}</span>
            <span>{record.issn || '-'}</span>
            <span>{record.indexing || '-'}</span>
            <span>{record.academic_year || '-'}</span>
          </div>
        ))}
      </div>

      <footer className="pagination">
        <button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
        <span>Page {page} of {totalPages}</span>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
      </footer>
    </article>
  )
}

function buildMockPublicationRecords() {
  return mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: faculty.total_research_papers || 0 }).map((_, index) => ({
      id: `${faculty.faculty_id}-journal-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      employee_id: faculty.employee_id,
      school: faculty.school,
      department: faculty.department,
      designation: index % 2 ? 'Associate Professor' : 'Professor',
      title: ['Adaptive Learning Analytics', 'AI-Enabled Forecasting Models', 'Institutional Research Mining'][index % 3],
      journal: ['IEEE Access', 'Springer LNNS', 'Elsevier Materials Today'][index % 3],
      issn: index % 4 ? `21${index}9-35${index}6` : '',
      indexing: ['Scopus', 'SCI / Web of Science', 'UGC', ''][index % 4],
      academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
      score: 8 + index,
      hod_score: 7 + index,
      director_score: 7 + index,
      dean_score: 6 + index,
      vc_score: 6 + index,
    })),
  )
}

export default function JournalPublicationsAnalyticsPage({ sharedData, filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [publicationResponse, setPublicationResponse] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadPublications() {
      setLoading((current) => current)
      setError('')
      try {
        const response = await researchAnalyticsApi.publications(filters)
        if (!ignore) setPublicationResponse(response)
      } catch (requestError) {
        if (!ignore) {
          const mockRows = buildMockPublicationRecords()
          setPublicationResponse({ items: mockRows, total: mockRows.length })
          setError(`${requestError.message} Showing demo journal analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadPublications()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const publications = useMemo(() => (publicationResponse.items || []).filter(isValidPublication), [publicationResponse])
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const facultyGroups = groupBy(publications, (record) => (record.faculty_email || '').toLowerCase().trim())
  const publishingFaculty = Object.keys(facultyGroups).filter(Boolean).length
  const indexedPublications = publications.filter(isIndexed).length
  const participationRate = activeFaculty ? (publishingFaculty / activeFaculty) * 100 : 0
  const papersPerActive = activeFaculty ? publications.length / activeFaculty : 0
  const papersPerPublishing = publishingFaculty ? publications.length / publishingFaculty : 0
  const indexedPercentage = publications.length ? (indexedPublications / publications.length) * 100 : 0

  const departmentRows = Object.entries(groupBy(publications, (record) => departmentLabel(record))).map(([department, rows]) => {
    const faculty = new Set(rows.map((record) => record.faculty_email).filter(Boolean))
    const topThree = Object.values(groupBy(rows, (record) => record.faculty_email)).map((items) => items.length).sort((a, b) => b - a).slice(0, 3).reduce((sum, value) => sum + value, 0)
    return {
      label: department,
      department,
      value: rows.length,
      activeFaculty: faculty.size,
      publishingFaculty: faculty.size,
      participation: activeFaculty ? (faculty.size / activeFaculty) * 100 : 0,
      papersPerActive: activeFaculty ? rows.length / activeFaculty : 0,
      papersPerPublishing: faculty.size ? rows.length / faculty.size : 0,
      topThreeShare: rows.length ? (topThree / rows.length) * 100 : 0,
      yoyGrowth: 0,
    }
  }).sort((a, b) => b.value - a.value)

  const schoolRows = Object.entries(groupBy(publications, (record) => record.school || record.school_name || 'School not specified')).map(([school, rows]) => ({
    label: school,
    school,
    value: rows.length,
  })).sort((a, b) => b.value - a.value)

  const yearRows = Object.entries(groupBy(publications, (record) => record.academic_year)).map(([label, rows]) => ({ label, year: label, total_papers: rows.length, value: rows.length })).sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const indexingRows = Object.entries(groupBy(publications, (record) => record.indexing)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => b.value - a.value)
  const journalRows = Object.entries(groupBy(publications, (record) => record.journal)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => b.value - a.value)
  const facultyRows = Object.entries(facultyGroups).map(([email, rows]) => {
    const first = rows[0] || {}
    return {
      email,
      faculty_name: first.full_name || first.faculty_name || email,
      employee_id: first.employee_id,
      department: first.department,
      school: first.school,
      designation: first.designation,
      total: rows.length,
      indexed: rows.filter(isIndexed).length,
      years: new Set(rows.map((record) => record.academic_year).filter(Boolean)).size,
      score: rows.reduce((sum, record) => sum + Number(record.score || 0), 0),
      latest: Math.max(...rows.map(finalScore), 0),
    }
  }).sort((a, b) => b.total - a.total)

  const missingIndexing = publications.filter((record) => !isIndexed(record)).length
  const missingIssn = publications.filter((record) => !isPresent(record.issn)).length
  const uniqueJournalCount = new Set(publications.map((record) => String(record.journal || '').trim().toLowerCase()).filter(Boolean)).size
  const duplicateTitles = Object.values(groupBy(publications, (record) => `${record.faculty_email}-${String(record.title).toLowerCase()}`)).filter((rows) => rows.length > 1).length
  const multiFacultySameTitle = Object.values(groupBy(publications, (record) => String(record.title || '').toLowerCase())).filter((rows) => new Set(rows.map((record) => record.faculty_email)).size > 1).length

  const primaryKpis = [
    { label: 'Total Valid Journal Publications', value: formatNumber(publications.length), icon: 'JP', subtext: 'Valid title records only' },
    { label: 'Publishing Faculty', value: formatNumber(publishingFaculty), icon: 'PF', subtext: `${publishingFaculty} unique active faculty` },
    { label: 'Publication Participation Rate', value: percent(participationRate), icon: 'PR', subtext: `${publishingFaculty} of ${activeFaculty} active faculty` },
    { label: 'Papers per Active Faculty', value: papersPerActive.toFixed(2), icon: 'PA', subtext: 'Total papers / active faculty' },
    { label: 'Papers per Publishing Faculty', value: papersPerPublishing.toFixed(2), icon: 'PP', subtext: 'Total papers / publishing faculty' },
    { label: 'Indexed Publication Percentage', value: percent(indexedPercentage), icon: 'IX', subtext: `${indexedPublications} indexed publications` },
  ]

  return (
    <main className="research-page journal-page">
      <PageHeader
        title="Journal Publications Analytics"
        description="Publication productivity, participation, indexing quality, and reviewer score overview"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading journal analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Missing indexing', value: missingIndexing },
            { label: 'Missing ISSN', value: missingIssn },
            { label: 'Unique journal count', value: uniqueJournalCount },
            { label: 'Duplicate titles', value: duplicateTitles },
            { label: 'Same title by multiple faculty', value: multiFacultySameTitle },
          ]} />

          <nav className="page-tabs" aria-label="Journal analytics tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Overview' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Publications by school" subtitle="School output" rows={schoolRows} />
              <MiniBarChart title="Publications by academic year" subtitle="Year trend" rows={yearRows} />
              <MiniBarChart title="Indexing distribution" subtitle="Quality and indexing" rows={indexingRows} />
              <MiniBarChart title="Top journals by paper count" subtitle="Journal concentration" rows={journalRows} />
            </section>
          )}

          {activeTab === 'Department Analysis' && (
            <section className="executive-chart-row two-col">
              <QuadrantChart rows={departmentRows} />
              <article className="table-card">
                <div className="card-title"><span>Department table</span><h2>Department publication analytics</h2></div>
                <div className="department-mini-table">
                  {departmentRows.map((row) => (
                    <div key={row.department}>
                      <strong>{row.department}</strong>
                      <span>Faculty {row.activeFaculty}</span>
                      <span>Papers {row.value}</span>
                      <span>Participation {percent(row.participation)}</span>
                      <span>Papers / active {row.papersPerActive.toFixed(2)}</span>
                      <span>Top 3 share {percent(row.topThreeShare)}</span>
                    </div>
                  ))}
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Faculty Analysis' && (
            <section className="books-analysis-grid">
              <MiniBarChart title="Top publishing faculty" subtitle="Faculty output" rows={facultyRows.map((row) => ({ label: row.faculty_name, value: row.total }))} />
              <article className="quality-card">
                <h2>Faculty publication segments</h2>
                <div className="quality-grid">
                  <span>Zero publications <strong>{Math.max(activeFaculty - publishingFaculty, 0)}</strong></span>
                  <span>Exactly one publication <strong>{facultyRows.filter((row) => row.total === 1).length}</strong></span>
                  <span>Consecutive academic years <strong>{facultyRows.filter((row) => row.years > 1).length}</strong></span>
                  <span>Newly active publishers <strong>{facultyRows.filter((row) => row.years === 1).length}</strong></span>
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Quality and Indexing' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Indexing category distribution" subtitle="Indexing" rows={indexingRows} />
              <article className="quality-card">
                <h2>Quality checks</h2>
                <div className="quality-grid">
                  <span>Missing indexing <strong>{missingIndexing}</strong></span>
                  <span>Missing ISSN <strong>{missingIssn}</strong></span>
                  <span>Unique journals <strong>{uniqueJournalCount}</strong></span>
                  <span>Duplicate titles <strong>{duplicateTitles}</strong></span>
                  <span>Same title by multiple faculty <strong>{multiFacultySameTitle}</strong></span>
                  <span>Indexed percentage <strong>{percent(indexedPercentage)}</strong></span>
                </div>
              </article>
              <MiniBarChart title="Most common journals" subtitle="Journals" rows={journalRows} />
              <MiniBarChart title="Average score by indexing type" subtitle="Reviewer score" rows={Object.entries(groupBy(publications, (record) => record.indexing)).map(([label, rows]) => ({ label, value: rows.reduce((sum, record) => sum + Number(record.score || 0), 0) / rows.length }))} formatter={(value) => value.toFixed(1)} />
            </section>
          )}

          {activeTab === 'Publication Records' && <PublicationRecordsTable records={publications} />}
        </>
      )}
    </main>
  )
}
