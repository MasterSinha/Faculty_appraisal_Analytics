import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import BubbleCloudChart from '../components/research-analytics/charts/BubbleCloudChart'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import ScatterChart from '../components/research-analytics/charts/ScatterChart'
import StatRing from '../components/research-analytics/charts/StatRing'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'

const tabs = ['Overview', 'Degree Analysis', 'Department Analysis', 'Faculty Supervisors', 'Guidance and Publications']

function normalizeDegree(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return 'Unknown'
  if (text.includes('ph.d') || text.includes('phd') || text.includes('doctorate') || text.includes('doctor of philosophy')) return 'PhD'
  if (text.includes('pg') || text.includes('post graduate') || text.includes('postgraduate') || text.includes('m.tech') || text.includes('m.e') || text.includes('mba') || text.includes('m.sc')) return 'PG'
  if (text.includes('ug') || text.includes('under graduate') || text.includes('undergraduate') || text.includes('b.tech') || text.includes('b.e') || text.includes('b.sc')) return 'UG'
  if (text.includes('diploma')) return 'Diploma'
  return 'Other'
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
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0), x: Number(row[valueKey] || 0), y: Number(row.participation ?? row.phdParticipation ?? row.avgScholars ?? 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('degree')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('versus') || context.includes('cross')) return <ScatterChart title={title} subtitle={subtitle} rows={chartRows} xLabel="Count" yLabel="Participation" xFormatter={formatter} yFormatter={percent} />
  if (context.includes('participation') || context.includes('average') || context.includes('department')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function GuidanceTable({ records }) {
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
    <article className="table-card guidance-table-card">
      <div className="table-toolbar">
        <div>
          <span>Guidance records</span>
          <h2>Research guidance and scholar supervision</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search guidance records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="degree">Sort by degree</option>
            <option value="department">Sort by department</option>
          </select>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="guidance-table">
        <div className="guidance-table-head">
          {['Faculty', 'Department', 'School', 'Degree', 'Student name', 'Thesis title', 'Academic year'].map((column) => (
            <span key={column}>{column}</span>
          ))}
        </div>
        {pageItems.map((record, index) => (
          <div className="guidance-table-row" key={record.id || `${record.faculty_email}-${index}`}>
            <strong>{record.full_name || record.faculty_name || record.faculty_email || '-'}</strong>
            <span>{record.department || '-'}</span>
            <span>{record.school || '-'}</span>
            <span>{normalizeDegree(record.degree)}</span>
            <span>{record.student_name || '-'}</span>
            <span>{record.thesis || '-'}</span>
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

function buildMockGuidanceRecords() {
  return mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: Math.max(1, Math.floor((faculty.mentoring || faculty.total_research_papers || 1) / 8)) }).map((_, index) => ({
      id: `${faculty.faculty_id}-guidance-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      school: faculty.school,
      department: faculty.department,
      degree: ['Ph.D.', 'M.Tech', 'B.Tech', 'Doctor of Philosophy'][index % 4],
      student_name: ['Aarav Sharma', 'Meera Kulkarni', 'Riya Patil', 'Kabir Joshi'][index % 4],
      thesis: ['Adaptive research analytics model', 'AI-driven institutional quality mining', 'Outcome based appraisal intelligence'][index % 3],
      academic_year: `202${index + 3}-202${index + 4}`,
      score: 8 + index,
      vc_score: 7 + index,
    })),
  )
}

export default function ResearchGuidanceAnalyticsPage({ sharedData, filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [guidanceResponse, setGuidanceResponse] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadGuidance() {
      setLoading(true)
      setError('')
      try {
        const response = await researchAnalyticsApi.guidance(filters)
        if (!ignore) setGuidanceResponse(response)
      } catch (requestError) {
        if (!ignore) {
          const mockRows = buildMockGuidanceRecords()
          setGuidanceResponse({ items: mockRows, total: mockRows.length })
          setError(`${requestError.message} Showing demo research guidance analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadGuidance()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const records = guidanceResponse.items || []
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const facultyGroups = groupBy(records, (record) => String(record.faculty_email || '').toLowerCase())
  const guidingFaculty = Object.keys(facultyGroups).filter(Boolean).length
  const guidanceRate = activeFaculty ? (guidingFaculty / activeFaculty) * 100 : 0
  const phdScholars = records.filter((record) => normalizeDegree(record.degree) === 'PhD').length
  const pgStudents = records.filter((record) => normalizeDegree(record.degree) === 'PG').length
  const avgScholarsGuiding = guidingFaculty ? records.length / guidingFaculty : 0

  const degreeRows = Object.entries(groupBy(records, (record) => normalizeDegree(record.degree))).map(([label, rows]) => ({ label, value: rows.length }))
  const departmentRows = Object.entries(groupBy(records, (record) => record.department)).map(([label, rows]) => {
    const faculty = new Set(rows.map((record) => record.faculty_email).filter(Boolean))
    const phdFaculty = new Set(rows.filter((record) => normalizeDegree(record.degree) === 'PhD').map((record) => record.faculty_email).filter(Boolean))
    return {
      label,
      value: rows.length,
      participation: activeFaculty ? (faculty.size / activeFaculty) * 100 : 0,
      avgScholars: faculty.size ? rows.length / faculty.size : 0,
      phdParticipation: activeFaculty ? (phdFaculty.size / activeFaculty) * 100 : 0,
    }
  }).sort((a, b) => b.value - a.value)
  const schoolRows = Object.entries(groupBy(records, (record) => record.school)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => b.value - a.value)
  const yearRows = Object.entries(groupBy(records, (record) => record.academic_year)).map(([label, rows]) => ({ label, value: rows.length })).sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const supervisorRows = Object.entries(facultyGroups).map(([email, rows]) => ({ label: rows[0]?.full_name || email, value: rows.length, years: new Set(rows.map((record) => record.academic_year)).size })).sort((a, b) => b.value - a.value)
  const publicationFaculty = new Set((sharedData.faculty?.items || []).filter((faculty) => (faculty.total_research_papers || 0) > 0).map((faculty) => String(faculty.email || faculty.faculty_id || '').toLowerCase()))
  const guidanceFaculty = new Set(Object.keys(facultyGroups))
  const publishingNotGuiding = [...publicationFaculty].filter((email) => !guidanceFaculty.has(email)).length
  const guidingNotPublishing = [...guidanceFaculty].filter((email) => !publicationFaculty.has(email)).length
  const multipleScholars = Object.values(facultyGroups).filter((rows) => rows.length > 1).length
  const lowGuidanceDepartments = departmentRows.filter((row) => row.participation < 20).length
  const consistentSupervisors = supervisorRows.filter((row) => row.years > 1).length
  const newSupervisors = supervisorRows.filter((row) => row.years === 1).length

  const primaryKpis = [
    { label: 'Total Students Guided', value: formatNumber(records.length), icon: 'SG', subtext: 'All guidance records' },
    { label: 'Guiding Faculty', value: formatNumber(guidingFaculty), icon: 'GF', subtext: 'Unique supervisors' },
    { label: 'Guidance Participation Rate', value: percent(guidanceRate), icon: 'GR', subtext: `${guidingFaculty} of ${activeFaculty} active faculty` },
    { label: 'PhD Scholars', value: formatNumber(phdScholars), icon: 'PHD', subtext: 'Normalized degree' },
    { label: 'PG Students', value: formatNumber(pgStudents), icon: 'PG', subtext: 'Normalized degree' },
    { label: 'Avg Scholars per Guiding Faculty', value: avgScholarsGuiding.toFixed(2), icon: 'AVG', subtext: 'Students / guiding faculty' },
  ]

  return (
    <main className="research-page guidance-page">
      <PageHeader
        title="Research Guidance Analytics"
        description="Student guidance, supervisor participation, degree mix, and publication-guidance comparison"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      <div className="data-limitation-notice">
        <strong>Classification note</strong>
        <span>Thesis discipline is not inferred because no documented thesis classification method was provided.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading research guidance analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Faculty with multiple scholars', value: multipleScholars },
            { label: 'Publishing but not guiding', value: publishingNotGuiding },
            { label: 'Guiding but not publishing', value: guidingNotPublishing },
            { label: 'Low guidance departments', value: lowGuidanceDepartments },
            { label: 'Average scholars per department', value: departmentRows.length ? (records.length / departmentRows.length).toFixed(2) : '0.00' },
            { label: 'Consistent supervisors across years', value: consistentSupervisors },
            { label: 'New supervisors in selected year', value: newSupervisors },
          ]} />

          <nav className="page-tabs" aria-label="Research guidance tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Overview' && (
            <>
              <div className="stat-rings-row">
                <StatRing value={guidanceRate} label="Guidance Participation" color="#22c55e" />
              </div>
              <section className="executive-chart-row two-col">
                <MiniBarChart title="Students guided by degree" subtitle="Degree mix" rows={degreeRows} />
                <MiniBarChart title="Guidance by department" subtitle="Department guidance" rows={departmentRows} />
                <MiniBarChart title="Guidance by school" subtitle="School guidance" rows={schoolRows} />
                <MiniBarChart title="Guidance trend by academic year" subtitle="Academic year trend" rows={yearRows} />
                <RankingList title="Top research supervisors" subtitle="Faculty supervisors" rows={supervisorRows} />
                <MiniBarChart title="Publication count versus guided students" subtitle="Cross analysis" rows={[
                  { label: 'Publishing not guiding', value: publishingNotGuiding },
                  { label: 'Guiding not publishing', value: guidingNotPublishing },
                  { label: 'Guiding faculty', value: guidingFaculty },
                ]} />
              </section>
            </>
          )}

          {activeTab === 'Degree Analysis' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Students guided by degree" subtitle="Normalized degrees" rows={degreeRows} />
              <MiniBarChart title="PhD guidance participation by department" subtitle="PhD participation" rows={departmentRows} valueKey="phdParticipation" formatter={percent} />
            </section>
          )}

          {activeTab === 'Department Analysis' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Guidance by department" subtitle="Department output" rows={departmentRows} />
              <MiniBarChart title="Guidance participation by department" subtitle="Participation" rows={departmentRows} valueKey="participation" formatter={percent} />
              <MiniBarChart title="Average scholars per department" subtitle="Average" rows={departmentRows} valueKey="avgScholars" formatter={(value) => value.toFixed(2)} />
              <article className="quality-card">
                <h2>Departments with low guidance participation</h2>
                <div className="books-chip-list">
                  {departmentRows.filter((row) => row.participation < 20).map((row) => <span key={row.label}>{row.label}</span>)}
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Faculty Supervisors' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Top research supervisors" subtitle="Supervisor leaderboard" rows={supervisorRows} />
              <article className="quality-card">
                <h2>Supervisor patterns</h2>
                <div className="quality-grid">
                  <span>Faculty with multiple scholars <strong>{multipleScholars}</strong></span>
                  <span>Consistent supervisors across years <strong>{consistentSupervisors}</strong></span>
                  <span>New supervisors in selected year <strong>{newSupervisors}</strong></span>
                </div>
              </article>
            </section>
          )}

          {activeTab === 'Guidance and Publications' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Publication count versus guided students" subtitle="Cross comparison" rows={[
                { label: 'Publishing but not guiding', value: publishingNotGuiding },
                { label: 'Guiding but not publishing', value: guidingNotPublishing },
                { label: 'Guiding faculty', value: guidingFaculty },
                { label: 'Publishing faculty', value: publicationFaculty.size },
              ]} />
              <RatioPanel items={[
                { label: 'Faculty publishing but not guiding', value: publishingNotGuiding },
                { label: 'Faculty guiding but not publishing', value: guidingNotPublishing },
                { label: 'Guidance participation rate', value: percent(guidanceRate) },
              ]} />
            </section>
          )}

          <GuidanceTable records={records} />
        </>
      )}
    </main>
  )
}

function RatioPanel({ items }) {
  return (
    <article className="quality-card">
      <h2>Guidance and publication relationship</h2>
      <div className="quality-grid">
        {items.map((item) => (
          <span key={item.label}>{item.label}<strong>{item.value}</strong></span>
        ))}
      </div>
    </article>
  )
}
