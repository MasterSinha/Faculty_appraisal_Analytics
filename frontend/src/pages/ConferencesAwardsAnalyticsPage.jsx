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
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Overview', 'Conferences', 'Awards', 'Department Comparison', 'Faculty Details']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function finalScore(record) {
  return record.vc_score ?? record.dean_score ?? record.director_score ?? record.hod_score ?? record.score ?? 0
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Unknown'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function isInternational(record) {
  const text = `${record.level || ''} ${record.type || ''} ${record.scope || ''}`.toLowerCase()
  return text.includes('international') || text.includes('global') || text.includes('foreign')
}

function averageScore(records) {
  return records.length ? records.reduce((sum, record) => sum + Number(finalScore(record) || 0), 0) / records.length : 0
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0), x: Number(row.value || 0), y: Number(row.publications || row.value || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('level') || context.includes('national versus')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('versus') || context.includes('association')) return <ScatterChart title={title} subtitle={subtitle} rows={chartRows} xLabel="Conference activity" yLabel="Publication output" xFormatter={formatter} yFormatter={formatter} />
  if (context.includes('department') || context.includes('school')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('faculty') || context.includes('institution') || context.includes('agency') || context.includes('organis')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function InsightCard({ title, items }) {
  return (
    <article className="quality-card">
      <h2>{title}</h2>
      <div className="quality-grid">
        {items.map((item) => (
          <span key={item.label}>{item.label}<strong>{item.value}</strong></span>
        ))}
      </div>
    </article>
  )
}

function RecordsTable({ title, mode, records }) {
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
  const columns = mode === 'conference'
    ? ['Faculty', 'Department', 'Title', 'Type', 'Organisation', 'Level', 'Academic year']
    : ['Faculty', 'Department', 'Award title', 'Award date', 'Agency', 'Level', 'Academic year']

  return (
    <article className="table-card conference-table-card">
      <div className="table-toolbar">
        <div>
          <span>{mode === 'conference' ? 'Conference table' : 'Award table'}</span>
          <h2>{title}</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="department">Sort by department</option>
            <option value="level">Sort by level</option>
          </select>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="conference-table">
        <div className="conference-table-head">
          {columns.map((column) => <span key={column}>{column}</span>)}
        </div>
        {pageItems.map((record, index) => (
          <div className="conference-table-row" key={record.id || `${mode}-${index}`}>
            <strong>{record.full_name || record.faculty_name || record.faculty_email || '-'}</strong>
            <span>{departmentLabel(record)}</span>
            <span>{record.title || record.award_title || '-'}</span>
            {mode === 'conference' ? (
              <>
                <span>{record.type || record.conference_type || '-'}</span>
                <span>{record.organisation || record.organization || record.institution || '-'}</span>
              </>
            ) : (
              <>
                <span>{record.award_date || record.date || '-'}</span>
                <span>{record.agency || record.awarding_agency || '-'}</span>
              </>
            )}
            <span>{record.level || '-'}</span>
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

function buildMockRows() {
  const conferences = mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: Math.max(1, Math.floor((faculty.conference_publications || 1) / 8)) }).map((_, index) => ({
      id: `${faculty.faculty_id}-conference-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      school: faculty.school,
      department: faculty.department,
      title: ['Research impact modelling', 'AI in higher education', 'Smart appraisal analytics'][index % 3],
      type: ['Paper Presentation', 'Workshop', 'Keynote'][index % 3],
      organisation: ['IEEE ICACDS', 'Springer ICET', 'DYPIU Research Forum'][index % 3],
      level: ['International', 'National', 'University'][index % 3],
      academic_year: `202${index + 3}-202${index + 4}`,
      score: 5 + index,
      journal_publications: faculty.total_research_papers || 0,
    })),
  )
  const awards = mockResearchAnalytics.faculty.items.slice(0, 8).map((faculty, index) => ({
    id: `${faculty.faculty_id}-award-${index}`,
    faculty_email: faculty.email,
    full_name: faculty.faculty_name,
    school: faculty.school,
    department: faculty.department,
    title: ['Best Research Paper', 'Research Excellence Award', 'Innovation Mentor Award'][index % 3],
    award_date: `202${index % 3 + 3}-11-20`,
    agency: ['AICTE', 'Institutional Research Cell', 'IEEE Chapter'][index % 3],
    level: ['International', 'National', 'University'][index % 3],
    academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
    score: 7 + index,
    journal_publications: faculty.total_research_papers || 0,
  }))
  return { conferences, awards }
}

export default function ConferencesAwardsAnalyticsPage({ sharedData, filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [response, setResponse] = useState({ conferences: [], awards: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadData() {
      setLoading((current) => current)
      setError('')
      try {
        const data = await researchAnalyticsApi.conferencesAwards(filters)
        if (!ignore) setResponse({ conferences: data.conferences || data.items?.conferences || [], awards: data.awards || data.items?.awards || [] })
      } catch (requestError) {
        if (!ignore) {
          setResponse(buildMockRows())
          setError(`${requestError.message} Showing demo conferences and awards analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadData()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const conferences = response.conferences || []
  const awards = response.awards || []
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const conferenceFaculty = new Set(conferences.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const awardFaculty = new Set(awards.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const publicationMap = new Map((sharedData.faculty?.items || []).map((faculty) => [String(faculty.email || faculty.faculty_id || '').toLowerCase(), faculty.total_research_papers || 0]))
  const internationalActivities = conferences.filter(isInternational).length + awards.filter(isInternational).length

  const byCount = (records, keyGetter) => Object.entries(groupBy(records, keyGetter))
    .map(([label, rows]) => ({ label, value: rows.length }))
    .sort((a, b) => b.value - a.value)

  const conferenceDepartmentRows = byCount(conferences, (record) => departmentLabel(record))
  const conferenceSchoolRows = byCount(conferences, (record) => record.school)
  const conferenceYearRows = byCount(conferences, (record) => record.academic_year).sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const conferenceTypeRows = byCount(conferences, (record) => record.type || record.conference_type)
  const conferenceLevelRows = byCount(conferences, (record) => record.level)
  const organisationRows = byCount(conferences, (record) => record.organisation || record.organization || record.institution)
  const awardDepartmentRows = byCount(awards, (record) => departmentLabel(record))
  const awardSchoolRows = byCount(awards, (record) => record.school)
  const awardLevelRows = byCount(awards, (record) => record.level)
  const awardAgencyRows = byCount(awards, (record) => record.agency || record.awarding_agency)
  const awardYearRows = byCount(awards, (record) => record.academic_year).sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const conferenceFacultyRows = byCount(conferences, (record) => record.full_name || record.faculty_name || record.faculty_email)
  const awardFacultyRows = byCount(awards, (record) => record.full_name || record.faculty_name || record.faculty_email)
  const multiConferenceFaculty = conferenceFacultyRows.filter((row) => row.value > 1).length
  const awardAfterResearch = awards.filter((record) => Number(record.journal_publications ?? publicationMap.get(String(record.faculty_email || '').toLowerCase()) ?? 0) > 0).length
  const highConferenceLowPublication = conferenceDepartmentRows.filter((row) => {
    const rows = conferences.filter((record) => departmentLabel(record) === row.label)
    const averagePapers = rows.reduce((sum, record) => sum + Number(record.journal_publications ?? publicationMap.get(String(record.faculty_email || '').toLowerCase()) ?? 0), 0) / Math.max(rows.length, 1)
    return row.value >= 2 && averagePapers < 2
  }).length
  const associationRows = conferenceDepartmentRows.map((row) => {
    const rows = conferences.filter((record) => departmentLabel(record) === row.label)
    const publications = rows.reduce((sum, record) => sum + Number(record.journal_publications ?? publicationMap.get(String(record.faculty_email || '').toLowerCase()) ?? 0), 0)
    return { label: row.label, value: row.value, publications }
  })

  const primaryKpis = [
    { label: 'Total Conferences', value: formatNumber(conferences.length), icon: 'CF', subtext: 'Conference activities' },
    { label: 'Conference-Participating Faculty', value: formatNumber(conferenceFaculty.size), icon: 'CP', subtext: 'Unique faculty' },
    { label: 'Conference Participation Rate', value: percent(activeFaculty ? (conferenceFaculty.size / activeFaculty) * 100 : 0), icon: 'CR', subtext: `${conferenceFaculty.size} of ${activeFaculty} active faculty` },
    { label: 'Total Awards', value: formatNumber(awards.length), icon: 'AW', subtext: 'Award records' },
    { label: 'Award-Receiving Faculty', value: formatNumber(awardFaculty.size), icon: 'AR', subtext: 'Unique recipients' },
    { label: 'International-Level Activities', value: formatNumber(internationalActivities), icon: 'IA', subtext: 'Conference + award records' },
  ]

  return (
    <main className="research-page conferences-page">
      <PageHeader
        title="Conferences and Awards Analytics"
        description="Conference participation, recognition patterns, faculty reach, and department-level associations"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}
      <div className="data-limitation-notice">
        <strong>Association note</strong>
        <span>Conference participation, publications, and awards are shown as associations only. The dashboard does not imply that one caused another.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading conferences and awards analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Faculty with multiple conference activities', value: multiConferenceFaculty },
            { label: 'Average conference score', value: averageScore(conferences).toFixed(2) },
            { label: 'Average award score', value: averageScore(awards).toFixed(2) },
            { label: 'Awards after recorded research contributions', value: awardAfterResearch },
            { label: 'High conference, low publication departments', value: highConferenceLowPublication },
          ]} />

          <nav className="page-tabs" aria-label="Conferences and awards tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Overview' && (
            <>
              <div className="stat-rings-row">
                <StatRing value={conferences.length ? (conferences.filter(isInternational).length / conferences.length) * 100 : 0} label="International Conference Rate" color="#6366f1" />
                <StatRing value={activeFaculty ? (awardFaculty.size / activeFaculty) * 100 : 0} label="Award Participation" color="#f59e0b" />
              </div>
              <section className="executive-chart-row two-col">
                <MiniBarChart title="Conference trend" subtitle="Academic year" rows={conferenceYearRows} />
                <MiniBarChart title="Conference level distribution" subtitle="Level mix" rows={conferenceLevelRows} />
                <RankingList title="Top conference departments" subtitle="Department participation" rows={conferenceDepartmentRows} />
                <MiniBarChart title="Awards by department" subtitle="Department recognition" rows={awardDepartmentRows} />
                <MiniBarChart title="Awards by level" subtitle="Recognition level" rows={awardLevelRows} />
                <MiniBarChart title="Conference participation versus publication output" subtitle="Department association" rows={associationRows} formatter={(value) => `${value} conf`} />
                <MiniBarChart title="Top organising institutions or awarding agencies" subtitle="External bodies" rows={[...organisationRows.slice(0, 5), ...awardAgencyRows.slice(0, 5)]} />
              </section>
            </>
          )}

          {activeTab === 'Conferences' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Conferences by department" subtitle="Department" rows={conferenceDepartmentRows} />
              <MiniBarChart title="Conferences by school" subtitle="School" rows={conferenceSchoolRows} />
              <MiniBarChart title="Conferences by academic year" subtitle="Year" rows={conferenceYearRows} />
              <MiniBarChart title="Conferences by type" subtitle="Type" rows={conferenceTypeRows} />
              <MiniBarChart title="National versus international participation" subtitle="Level" rows={conferenceLevelRows} />
              <MiniBarChart title="Top organising institutions" subtitle="Organisers" rows={organisationRows} />
            </section>
          )}

          {activeTab === 'Awards' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Awards by department" subtitle="Department" rows={awardDepartmentRows} />
              <MiniBarChart title="Awards by school" subtitle="School" rows={awardSchoolRows} />
              <MiniBarChart title="Awards by level" subtitle="Level" rows={awardLevelRows} />
              <MiniBarChart title="Awards by agency" subtitle="Agency" rows={awardAgencyRows} />
              <MiniBarChart title="Awards by academic year" subtitle="Year" rows={awardYearRows} />
              <MiniBarChart title="Top award-receiving faculty" subtitle="Faculty" rows={awardFacultyRows} />
            </section>
          )}

          {activeTab === 'Department Comparison' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Conferences by department" subtitle="Conference comparison" rows={conferenceDepartmentRows} />
              <MiniBarChart title="Awards by department" subtitle="Award comparison" rows={awardDepartmentRows} />
              <MiniBarChart title="Conference participation versus publication output" subtitle="Association only" rows={associationRows} formatter={(value) => `${value} conf`} />
              <InsightCard title="Department observations" items={[
                { label: 'High conference, low publication departments', value: highConferenceLowPublication },
                { label: 'Conference departments represented', value: conferenceDepartmentRows.length },
                { label: 'Award departments represented', value: awardDepartmentRows.length },
              ]} />
            </section>
          )}

          {activeTab === 'Faculty Details' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Faculty with conference activities" subtitle="Top faculty" rows={conferenceFacultyRows} />
              <MiniBarChart title="Top award-receiving faculty" subtitle="Recognition" rows={awardFacultyRows} />
              <InsightCard title="Faculty analytics" items={[
                { label: 'Faculty with multiple conference activities', value: multiConferenceFaculty },
                { label: 'Award receiving faculty', value: awardFaculty.size },
                { label: 'Awards after recorded research contributions', value: awardAfterResearch },
              ]} />
            </section>
          )}

          <RecordsTable title="Conference Records" mode="conference" records={conferences} />
          <RecordsTable title="Award Records" mode="award" records={awards} />
        </>
      )}
    </main>
  )
}
