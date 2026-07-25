import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import BubbleCloudChart from '../components/research-analytics/charts/BubbleCloudChart'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Overview', 'Department Analysis', 'Publishers and ISBN', 'Authorship and Collaboration', 'Records']

function isPresent(value) {
  return value !== null && value !== undefined && String(value).trim() !== ''
}

function isValidBook(record) {
  return isPresent(record.title) || isPresent(record.book)
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function normalizeFirstAuthor(value) {
  const text = String(value || '').trim().toLowerCase()
  return ['yes', 'true', '1', 'first', 'first author', 'y'].includes(text)
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Not specified'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('first-author') || context.includes('co-authored') || context.includes('both journals')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('publisher')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department output') || context.includes('department book')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('participation') || context.includes('school')) return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function BooksRecordsTable({ records }) {
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
          <h2>Book publication records</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="publisher">Sort by publisher</option>
            <option value="department">Sort by department</option>
          </select>
          <button type="button">Columns</button>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="books-table">
        <div className="books-table-head">
          {['Faculty', 'School', 'Department', 'Title', 'Book', 'ISBN', 'ISSN', 'Publisher', 'Co-author', 'First-author', 'Academic year'].map((column) => (
            <span key={column}>{column}</span>
          ))}
        </div>
        {pageItems.map((record, index) => (
          <div className="books-table-row" key={record.id || `${record.faculty_email}-${index}`}>
            <strong>{record.full_name || record.faculty_name || record.faculty_email || '-'}</strong>
            <span>{record.school || '-'}</span>
            <span>{departmentLabel(record)}</span>
            <span>{record.title || '-'}</span>
            <span>{record.book || '-'}</span>
            <span>{record.isbn || '-'}</span>
            <span>{record.issn || '-'}</span>
            <span>{record.publisher || '-'}</span>
            <span>{record.coauthor || '-'}</span>
            <span>{record.first_author || '-'}</span>
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

function buildMockBookRecords() {
  return mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: faculty.book_publications || 0 }).map((_, index) => ({
      id: `${faculty.faculty_id}-book-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      employee_id: faculty.employee_id,
      school: faculty.school,
      department: faculty.department,
      designation: index % 2 ? 'Associate Professor' : 'Professor',
      title: index % 2 ? 'Research Methods in Analytics' : '',
      book: index % 2 ? '' : 'Applied Faculty Research Handbook',
      isbn: index % 3 ? `978-93-000${faculty.faculty_id}${index}` : '',
      issn: '',
      publisher: ['Springer', 'CRC Press', 'Wiley'][index % 3],
      coauthor: index % 2 ? 'Collaborative chapter' : '',
      first_author: index % 2 ? 'No' : 'Yes',
      academic_year: `202${index + 3}-202${index + 4}`,
      score: 6 + index,
      vc_score: 5 + index,
    })),
  )
}

export default function BooksAnalyticsPage({ sharedData, filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [bookResponse, setBookResponse] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadBooks() {
      setLoading((current) => current)
      setError('')
      try {
        const response = await researchAnalyticsApi.books(filters)
        if (!ignore) setBookResponse(response)
      } catch (requestError) {
        if (!ignore) {
          setBookResponse({ items: buildMockBookRecords(), total: buildMockBookRecords().length })
          setError(`${requestError.message} Showing demo book analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadBooks()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const books = useMemo(() => (bookResponse.items || []).filter(isValidBook), [bookResponse])
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const facultyMap = groupBy(books, (record) => (record.faculty_email || '').toLowerCase().trim())
  const publishingFaculty = Object.keys(facultyMap).filter(Boolean).length
  const withIsbn = books.filter((record) => isPresent(record.isbn)).length
  const firstAuthor = books.filter((record) => normalizeFirstAuthor(record.first_author)).length
  const coauthored = books.filter((record) => isPresent(record.coauthor)).length
  const bookParticipation = activeFaculty ? (publishingFaculty / activeFaculty) * 100 : 0
  const booksPerActive = activeFaculty ? books.length / activeFaculty : 0
  const booksPerPublishing = publishingFaculty ? books.length / publishingFaculty : 0
  const isbnCompletion = books.length ? (withIsbn / books.length) * 100 : 0

  const departmentRows = Object.entries(groupBy(books, (record) => departmentLabel(record))).map(([department, rows]) => {
    const faculty = new Set(rows.map((record) => record.faculty_email).filter(Boolean))
    return {
      label: department,
      department,
      value: rows.length,
      activeFaculty: faculty.size,
      participation: activeFaculty ? (faculty.size / activeFaculty) * 100 : 0,
    }
  }).sort((a, b) => b.value - a.value)

  const yearRows = Object.entries(groupBy(books, (record) => record.academic_year)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const publisherRows = Object.entries(groupBy(books, (record) => record.publisher)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => b.value - a.value)
  const schoolRows = Object.entries(groupBy(books, (record) => record.school)).map(([label, rows]) => {
    const faculty = new Set(rows.map((record) => record.faculty_email).filter(Boolean))
    return { label, value: rows.length, participation: activeFaculty ? (faculty.size / activeFaculty) * 100 : 0 }
  })

  const isbnCounts = Object.entries(groupBy(books.filter((record) => isPresent(record.isbn)), (record) => record.isbn))
  const duplicateIsbn = isbnCounts.filter(([, rows]) => rows.length > 1).length
  const unrelatedIsbn = isbnCounts.filter(([, rows]) => new Set(rows.map((record) => String(record.title || record.book || '').toLowerCase())).size > 1).length
  const multiBookFaculty = Object.values(facultyMap).filter((rows) => rows.length > 1).length
  const journalFaculty = new Set((sharedData.faculty?.items || []).filter((faculty) => (faculty.total_research_papers || 0) > 0).map((faculty) => String(faculty.email || faculty.faculty_id || '').toLowerCase()))
  const bookFaculty = new Set(Object.keys(facultyMap))
  const bothJournalAndBooks = [...bookFaculty].filter((email) => journalFaculty.has(email)).length
  const booksNoJournals = [...bookFaculty].filter((email) => !journalFaculty.has(email)).length

  const primaryKpis = [
    { label: 'Total Book Publication Records', value: formatNumber(books.length), icon: 'BK', subtext: `${booksPerActive.toFixed(2)} books per active faculty` },
    { label: 'Faculty Publishing Books', value: formatNumber(publishingFaculty), icon: 'FP', subtext: `${booksPerPublishing.toFixed(2)} books per publishing faculty` },
    { label: 'Book Participation Rate', value: percent(bookParticipation), icon: 'BR', subtext: `${publishingFaculty} of ${activeFaculty} active faculty` },
    { label: 'Publications with ISBN', value: formatNumber(withIsbn), icon: 'ISBN', subtext: `${percent(isbnCompletion)} completion rate` },
    { label: 'First-Author Contributions', value: formatNumber(firstAuthor), icon: 'FA', subtext: 'Approximate from text field' },
    { label: 'Co-Authored Contributions', value: formatNumber(coauthored), icon: 'CO', subtext: 'Approximate from coauthor text' },
  ]

  return (
    <main className="research-page books-page">
      <PageHeader
        title="Books Analytics"
        description="Book publications, ISBN quality, publisher contribution, and authorship collaboration summary"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      <div className="data-limitation-notice">
        <strong>Data limitation</strong>
        <span>`first_author` and `coauthor` are text fields, so authorship and collaboration analysis is approximate.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading book analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Books per active faculty', value: booksPerActive.toFixed(2) },
            { label: 'Books per publishing faculty', value: booksPerPublishing.toFixed(2) },
            { label: 'Faculty with multiple books', value: multiBookFaculty },
            { label: 'Books but no journal papers', value: booksNoJournals },
            { label: 'Books and journal papers', value: bothJournalAndBooks },
            { label: 'Missing ISBN count', value: books.length - withIsbn },
            { label: 'Duplicate ISBN', value: duplicateIsbn },
            { label: 'Same ISBN unrelated titles', value: unrelatedIsbn },
          ]} />

          <nav className="page-tabs" aria-label="Books analytics tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Overview' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Book publications by department" subtitle="Department output" rows={departmentRows} />
              <MiniBarChart title="Books by academic year" subtitle="Year trend" rows={yearRows} />
              <MiniBarChart title="Top publishers" subtitle="Publisher concentration" rows={publisherRows} />
              <MiniBarChart title="First-author vs co-authored" subtitle="Authorship" rows={[
                { label: 'First author', value: firstAuthor },
                { label: 'Co-authored', value: coauthored },
              ]} />
              <MiniBarChart title="Book participation by department" subtitle="Participation" rows={departmentRows} valueKey="participation" formatter={percent} />
              <MiniBarChart title="Faculty publishing journals and books" subtitle="Cross-category" rows={[
                { label: 'Both journals and books', value: bothJournalAndBooks },
                { label: 'Books only', value: booksNoJournals },
              ]} />
            </section>
          )}

          {activeTab === 'Department Analysis' && (
            <section className="books-analysis-grid">
              <MiniBarChart title="Department book contribution" subtitle="Book analytics" rows={departmentRows} />
              <MiniBarChart title="School-wise book participation" subtitle="School analytics" rows={schoolRows} valueKey="participation" formatter={percent} />
              <article className="chart-card books-chart-card">
                <div className="card-title"><span>Gaps</span><h2>Departments with no book contribution</h2></div>
                <div className="books-chip-list">
                  {(options?.departments || []).filter((department) => !departmentRows.some((row) => row.department === department)).map((department) => <span key={department}>{department}</span>)}
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Publishers and ISBN' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Most frequently used publishers" subtitle="Publishers" rows={publisherRows} />
              <article className="quality-card">
                <h2>ISBN Quality</h2>
                <div className="quality-grid">
                  <span>ISBN completion rate <strong>{percent(isbnCompletion)}</strong></span>
                  <span>Missing ISBN <strong>{books.length - withIsbn}</strong></span>
                  <span>Duplicate ISBN <strong>{duplicateIsbn}</strong></span>
                  <span>Same ISBN for unrelated titles <strong>{unrelatedIsbn}</strong></span>
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Authorship and Collaboration' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="First-author versus co-authored contribution" subtitle="Approximate analysis" rows={[
                { label: 'First author', value: firstAuthor },
                { label: 'Co-authored', value: coauthored },
                { label: 'Unspecified', value: Math.max(books.length - firstAuthor - coauthored, 0) },
              ]} />
              <article className="quality-card">
                <h2>Faculty Publishing Patterns</h2>
                <div className="quality-grid">
                  <span>Faculty with multiple books <strong>{multiBookFaculty}</strong></span>
                  <span>Books but no journal papers <strong>{booksNoJournals}</strong></span>
                  <span>Books and journals <strong>{bothJournalAndBooks}</strong></span>
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Records' && <BooksRecordsTable records={books} />}
        </>
      )}
    </main>
  )
}
