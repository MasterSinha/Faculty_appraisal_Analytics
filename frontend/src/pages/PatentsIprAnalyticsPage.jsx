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

const tabs = ['Patent Overview', 'Patent Status', 'IPR Analytics', 'Faculty Participation', 'Records']

function isPresent(value) {
  return value !== null && value !== undefined && String(value).trim() !== ''
}

function isValidPatent(record) {
  return isPresent(record.title)
}

function normalizeStatus(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return 'Unknown'
  if (text.includes('grant')) return 'Granted'
  if (text.includes('publish')) return 'Published'
  if (text.includes('file') || text.includes('submit')) return 'Filed'
  if (text.includes('pend') || text.includes('under')) return 'Pending'
  if (text.includes('reject')) return 'Rejected'
  if (text.includes('expir')) return 'Expired'
  return 'Unknown'
}

function normalizeScope(value) {
  const text = String(value || '').trim().toLowerCase()
  if (text.includes('international') || text.includes('global') || text.includes('pct')) return 'International'
  if (text.includes('domestic') || text.includes('national') || text.includes('india')) return 'Domestic'
  return 'Unknown'
}

function finalScore(record) {
  return record.vc_score ?? record.dean_score ?? record.director_score ?? record.hod_score ?? record.score ?? 0
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Unknown'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend') || context.includes('date')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('scope') || context.includes('share')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department') || context.includes('school output') || context.includes('participation')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('faculty')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('ipr')) return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function StatusDonut({ title, rows }) {
  const total = rows.reduce((sum, row) => sum + Number(row.value || 0), 0) || 1
  const colors = ['#2563eb', '#10b981', '#f59e0b', '#7c3aed', '#ef4444', '#64748b']
  const stops = rows.map((row, index) => {
    const start = rows.slice(0, index).reduce((sum, item) => sum + (Number(item.value || 0) / total) * 100, 0)
    const end = start + (Number(row.value || 0) / total) * 100
    return `${colors[index % colors.length]} ${start}% ${end}%`
  }).join(', ')

  return (
    <article className="chart-card patents-chart-card">
      <div className="card-title">
        <span>Status</span>
        <h2>{title}</h2>
      </div>
      <div className="patent-donut-wrap">
        <div className="patent-donut" style={{ background: `conic-gradient(${stops || '#e2e8f0 0 100%'})` }}>
          <strong>{formatNumber(total)}</strong>
          <span>records</span>
        </div>
        <div className="status-legend">
          {rows.map((row, index) => (
            <span key={row.label}>
              <i style={{ background: colors[index % colors.length] }} />
              {row.label}
              <strong>{row.value}</strong>
            </span>
          ))}
        </div>
      </div>
    </article>
  )
}

function FlagPanel({ flags }) {
  return (
    <article className="quality-card">
      <h2>Data and Risk Flags</h2>
      <div className="quality-grid">
        {flags.map((flag) => (
          <span key={flag.label}>{flag.label}<strong>{flag.value}</strong></span>
        ))}
      </div>
    </article>
  )
}

function RecordsTable({ patents, iprRecords }) {
  const [mode, setMode] = useState('patents')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('academic_year')
  const [page, setPage] = useState(1)
  const records = mode === 'patents' ? patents : iprRecords
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
          <span>{mode === 'patents' ? 'Patent table' : 'IPR table'}</span>
          <h2>{mode === 'patents' ? 'Patent Records' : 'IPR Records'}</h2>
        </div>
        <div className="books-table-controls">
          <select value={mode} onChange={(event) => { setMode(event.target.value); setPage(1) }}>
            <option value="patents">Patents</option>
            <option value="ipr">IPR Records</option>
          </select>
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="patent_date">Sort by patent date</option>
            <option value="ipr_date">Sort by IPR date</option>
          </select>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="patents-table">
        <div className={`patents-table-head ${mode}`}>
          {(mode === 'patents'
            ? ['Faculty', 'Department', 'School', 'Patent title', 'Type', 'Scope', 'Patent date', 'Status', 'File number', 'Academic year', 'Flags']
            : ['Faculty', 'Department', 'Title', 'Scope', 'IPR date', 'Status', 'File number', 'Flags']
          ).map((column) => <span key={column}>{column}</span>)}
        </div>
        {pageItems.map((record, index) => {
          const flags = [
            !isPresent(record.patent_status || record.ipr_status) && 'Missing status',
            record.__duplicateFileNo && 'Duplicate file no.',
            record.__futureDate && 'Future date',
            !isPresent(record.title) && 'Missing title',
            record.__unmatchedFaculty && 'Unmatched faculty',
          ].filter(Boolean)
          return (
            <div className={`patents-table-row ${mode}`} key={record.id || `${mode}-${index}`}>
              <strong>{record.full_name || record.faculty_name || record.faculty_email || '-'}</strong>
              <span>{record.department || '-'}</span>
              {mode === 'patents' && <span>{record.school || '-'}</span>}
              <span>{record.title || '-'}</span>
              {mode === 'patents' && <span>{record.type || '-'}</span>}
              <span>{normalizeScope(record.scope)}</span>
              <span>{record.patent_date || record.ipr_date || '-'}</span>
              <span>{normalizeStatus(record.patent_status || record.ipr_status)}</span>
              <span>{record.file_no || '-'}</span>
              {mode === 'patents' && <span>{record.academic_year || '-'}</span>}
              <span className="flag-cell">{flags.length ? flags.join(', ') : 'Clear'}</span>
            </div>
          )
        })}
      </div>

      <footer className="pagination">
        <button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
        <span>Page {page} of {totalPages}</span>
        <button type="button" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
      </footer>
    </article>
  )
}

function buildMockPatents() {
  return mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: faculty.patents || 0 }).map((_, index) => ({
      id: `${faculty.faculty_id}-patent-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      school: faculty.school,
      department: faculty.department,
      title: ['Smart appraisal workflow system', 'AI enabled research quality monitor'][index % 2],
      type: index % 2 ? 'Design' : 'Utility',
      scope: index % 2 ? 'International' : 'Domestic',
      patent_date: `202${index + 4}-08-12`,
      patent_status: ['Granted', 'Published', 'Pending'][index % 3],
      file_no: `PAT-${faculty.faculty_id}-${index}`,
      academic_year: `202${index + 4}-202${index + 5}`,
      score: 10 + index,
      vc_score: 9 + index,
    })),
  )
}

function buildMockIpr(patents) {
  return patents.slice(0, Math.max(1, patents.length)).map((record, index) => ({
    ...record,
    id: `${record.id}-ipr`,
    title: `${record.title} IPR`,
    ipr_date: record.patent_date,
    ipr_status: index % 2 ? 'Filed' : 'Granted',
  }))
}

export default function PatentsIprAnalyticsPage({ sharedData, filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Patent Overview')
  const [patentResponse, setPatentResponse] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadPatents() {
      setLoading(true)
      setError('')
      try {
        const response = await researchAnalyticsApi.patents(filters)
        if (!ignore) setPatentResponse(response)
      } catch (requestError) {
        if (!ignore) {
          const mockRows = buildMockPatents()
          setPatentResponse({ items: mockRows, total: mockRows.length })
          setError(`${requestError.message} Showing demo patent/IPR analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadPatents()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const patents = useMemo(() => (patentResponse.items || []).filter(isValidPatent), [patentResponse])
  const iprRecords = useMemo(() => buildMockIpr(patents), [patents])
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const patentFaculty = new Set(patents.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const granted = patents.filter((record) => normalizeStatus(record.patent_status) === 'Granted').length
  const pending = patents.filter((record) => normalizeStatus(record.patent_status) === 'Pending').length
  const grantRate = patents.length ? (granted / patents.length) * 100 : 0
  const patentParticipation = activeFaculty ? (patentFaculty.size / activeFaculty) * 100 : 0
  const avgPatentScore = patents.length ? patents.reduce((sum, record) => sum + Number(record.score || 0), 0) / patents.length : 0
  const avgValidatedScore = patents.length ? patents.reduce((sum, record) => sum + Number(finalScore(record) || 0), 0) / patents.length : 0

  const fileNoGroups = groupBy([...patents, ...iprRecords].filter((record) => isPresent(record.file_no)), (record) => record.file_no)
  const duplicateFileNos = Object.values(fileNoGroups).filter((rows) => rows.length > 1).length
  const today = new Date()
  const futureDates = patents.filter((record) => record.patent_date && new Date(record.patent_date) > today).length
  const missingStatus = patents.filter((record) => !isPresent(record.patent_status)).length + iprRecords.filter((record) => !isPresent(record.ipr_status)).length

  const statusRows = Object.entries(groupBy(patents, (record) => normalizeStatus(record.patent_status))).map(([label, rows]) => ({ label, value: rows.length }))
  const iprStatusRows = Object.entries(groupBy(iprRecords, (record) => normalizeStatus(record.ipr_status))).map(([label, rows]) => ({ label, value: rows.length }))
  const scopeRows = Object.entries(groupBy(patents, (record) => normalizeScope(record.scope))).map(([label, rows]) => ({ label, value: rows.length }))
  const departmentRows = Object.entries(groupBy(patents, (record) => record.department)).map(([label, rows]) => ({ label, value: rows.length, participation: activeFaculty ? (new Set(rows.map((record) => record.faculty_email)).size / activeFaculty) * 100 : 0 }))
  const schoolRows = Object.entries(groupBy(patents, (record) => record.school)).map(([label, rows]) => ({ label, value: rows.length, grantedShare: rows.length ? (rows.filter((record) => normalizeStatus(record.patent_status) === 'Granted').length / rows.length) * 100 : 0 }))
  const yearRows = Object.entries(groupBy(patents, (record) => String(record.patent_date || record.academic_year || '').slice(0, 4))).map(([label, rows]) => ({ label, value: rows.length }))
  const facultyRows = Object.entries(groupBy(patents, (record) => record.faculty_email)).map(([email, rows]) => ({ label: rows[0]?.full_name || email, value: rows.length })).sort((a, b) => b.value - a.value)
  const journalFaculty = new Set((sharedData.faculty?.items || []).filter((faculty) => (faculty.total_research_papers || 0) > 0).map((faculty) => String(faculty.email || faculty.faculty_id || '').toLowerCase()))
  const journalNoPatents = [...journalFaculty].filter((email) => !patentFaculty.has(email)).length
  const multiPatentFaculty = Object.values(groupBy(patents, (record) => record.faculty_email)).filter((rows) => rows.length > 1).length
  const noPatentDepartments = (options?.departments || []).filter((department) => !departmentRows.some((row) => row.label === department))
  const iprDepartments = new Set(iprRecords.map((record) => record.department).filter(Boolean))
  const noIprDepartments = (options?.departments || []).filter((department) => !iprDepartments.has(department))

  const primaryKpis = [
    { label: 'Total Valid Patents', value: formatNumber(patents.length), icon: 'PT', subtext: `${(activeFaculty ? patents.length / activeFaculty : 0).toFixed(2)} patents per active faculty` },
    { label: 'Patent-Filing Faculty', value: formatNumber(patentFaculty.size), icon: 'PF', subtext: `${percent(patentParticipation)} participation` },
    { label: 'Patents Granted', value: formatNumber(granted), icon: 'GR', subtext: 'Normalized status' },
    { label: 'Patents Pending', value: formatNumber(pending), icon: 'PN', subtext: 'Pending or under process' },
    { label: 'Patent Grant Rate', value: percent(grantRate), icon: 'GT', subtext: 'Granted / valid patents' },
    { label: 'Total IPR Records', value: formatNumber(iprRecords.length), icon: 'IPR', subtext: 'IPR activity records' },
  ]

  return (
    <main className="research-page patents-page">
      <PageHeader
        title="Patents and IPR Analytics"
        description="Patent filings, grants, scope, IPR activity, participation, and data-quality flags"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading patents analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Faculty with multiple patents', value: multiPatentFaculty },
            { label: 'Journal faculty with no patents', value: journalNoPatents },
            { label: 'Departments with no patents', value: noPatentDepartments.length },
            { label: 'Departments with no IPR', value: noIprDepartments.length },
            { label: 'Average patent score', value: avgPatentScore.toFixed(1) },
            { label: 'Average validated patent score', value: avgValidatedScore.toFixed(1) },
            { label: 'Patent participation rate', value: percent(patentParticipation) },
          ]} />

          <nav className="page-tabs" aria-label="Patents and IPR tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Patent Overview' && (
            <section className="executive-chart-row two-col">
              <StatusDonut title="Patent status distribution" rows={statusRows} />
              <MiniBarChart title="Patent trend by patent date" subtitle="Year trend" rows={yearRows} />
              <MiniBarChart title="Patents by department" subtitle="Department output" rows={departmentRows} />
              <MiniBarChart title="Patents by school" subtitle="School output" rows={schoolRows} />
              <MiniBarChart title="Domestic versus international patents" subtitle="Scope" rows={scopeRows} />
              <MiniBarChart title="Top patent-contributing faculty" subtitle="Faculty contribution" rows={facultyRows} />
            </section>
          )}

          {activeTab === 'Patent Status' && (
            <section className="executive-chart-row two-col">
              <StatusDonut title="Patent status distribution" rows={statusRows} />
              <MiniBarChart title="Granted patent share by school" subtitle="Grant share" rows={schoolRows} valueKey="grantedShare" formatter={percent} />
              <FlagPanel flags={[
                { label: 'Missing status', value: missingStatus },
                { label: 'Duplicate file number', value: duplicateFileNos },
                { label: 'Future patent date', value: futureDates },
                { label: 'Missing title', value: patentResponse.items.filter((record) => !isPresent(record.title)).length },
              ]} />
            </section>
          )}

          {activeTab === 'IPR Analytics' && (
            <section className="executive-chart-row two-col">
              <StatusDonut title="IPR status distribution" rows={iprStatusRows} />
              <MiniBarChart title="IPR records by department" subtitle="IPR contribution" rows={Object.entries(groupBy(iprRecords, (record) => record.department)).map(([label, rows]) => ({ label, value: rows.length }))} />
              <article className="quality-card">
                <h2>Departments with no IPR contribution</h2>
                <div className="books-chip-list">{noIprDepartments.map((department) => <span key={department}>{department}</span>)}</div>
              </article>
            </section>
          )}

          {activeTab === 'Faculty Participation' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Patent participation by department" subtitle="Participation" rows={departmentRows} valueKey="participation" formatter={percent} />
              <MiniBarChart title="Top patent-contributing faculty" subtitle="Faculty leaderboard" rows={facultyRows} />
              <article className="quality-card">
                <h2>Participation analytics</h2>
                <div className="quality-grid">
                  <span>Faculty with multiple patents <strong>{multiPatentFaculty}</strong></span>
                  <span>Journal papers but no patents <strong>{journalNoPatents}</strong></span>
                  <span>Departments with no patent contribution <strong>{noPatentDepartments.length}</strong></span>
                  <span>Patent-filing participation <strong>{percent(patentParticipation)}</strong></span>
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Records' && <RecordsTable patents={patents} iprRecords={iprRecords} />}
        </>
      )}
    </main>
  )
}
