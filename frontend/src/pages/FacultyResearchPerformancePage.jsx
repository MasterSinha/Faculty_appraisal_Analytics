import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import BubbleCloudChart from '../components/research-analytics/charts/BubbleCloudChart'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import RadarChart from '../components/research-analytics/charts/RadarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import SparklineRow from '../components/research-analytics/charts/SparklineRow'
import StatRing from '../components/research-analytics/charts/StatRing'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const drawerTabs = ['Overview', 'Publications', 'Books', 'Patents and IPR', 'Projects and Funding', 'Research Guidance', 'Conferences and Awards', 'Teaching Balance', 'Documents']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0))
}

function totalOutput(faculty) {
  return Number(faculty.journal_papers || faculty.total_research_papers || 0)
    + Number(faculty.books || faculty.book_publications || 0)
    + Number(faculty.patents || 0)
    + Number(faculty.projects || faculty.research_projects || 0)
    + Number(faculty.guidance || faculty.research_guidance || 0)
    + Number(faculty.conferences || faculty.conference_publications || 0)
    + Number(faculty.awards || 0)
}

function diversityScore(faculty) {
  return [
    faculty.journal_papers || faculty.total_research_papers,
    faculty.books || faculty.book_publications,
    faculty.patents,
    faculty.projects || faculty.research_projects,
    faculty.guidance || faculty.research_guidance,
    faculty.conferences || faculty.conference_publications,
    faculty.awards,
  ].filter((value) => Number(value || 0) > 0).length
}

function validatedScore(faculty) {
  return Number(faculty.validated_research_score ?? faculty.total_vc_score ?? faculty.vc_score ?? 0)
}

function segmentFaculty(faculty, selectedYear) {
  const output = totalOutput(faculty)
  const diversity = faculty.diversity_score ?? diversityScore(faculty)
  const score = validatedScore(faculty)
  const currentYearOutput = Number(faculty.current_year_output ?? output)
  const previousYearOutput = Number(faculty.previous_year_output ?? 0)
  const firstYear = String(faculty.first_activity_year || '')

  if (output === 0) return 'Inactive Researchers'
  if (selectedYear && firstYear.includes(String(selectedYear))) return 'Emerging Researchers'
  if (currentYearOutput < previousYearOutput) return 'Declining Contributors'
  if (output >= 18 && score >= 70 && diversity >= 4) return 'Research Leaders'
  if (output >= 8 && diversity <= 2) return 'Specialists'
  return 'Active Contributors'
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('distribution') || context.includes('category')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('score comparison') || context.includes('self versus')) return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('top faculty')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function ScatterChart({ rows }) {
  const maxOutput = Math.max(...rows.map((row) => row.output), 1)
  const maxParticipation = Math.max(...rows.map((row) => row.diversity), 1)

  return (
    <article className="chart-card faculty-scatter-card">
      <div className="card-title">
        <span>Participation</span>
        <h2>Output versus participation scatter</h2>
      </div>
      <div className="faculty-scatter">
        {rows.slice(0, 40).map((row) => (
          <button
            type="button"
            key={row.email || row.label}
            title={`${row.label}: ${row.output} outputs, diversity ${row.diversity}`}
            style={{ left: `${(row.output / maxOutput) * 88 + 4}%`, bottom: `${(row.diversity / maxParticipation) * 82 + 8}%` }}
          />
        ))}
      </div>
    </article>
  )
}

function SegmentPanel({ selectedSegment, onChange }) {
  const segments = [
    ['Research Leaders', 'High output, high validated score, high diversity, and consistent contribution.'],
    ['Active Contributors', 'Regular moderate contribution.'],
    ['Emerging Researchers', 'First recorded valid contribution in selected year.'],
    ['Specialists', 'Strong performance concentrated in one category.'],
    ['Inactive Researchers', 'No recorded research activity for the selected period.'],
    ['Declining Contributors', 'Current-year output below previous-year output.'],
  ]

  return (
    <article className="quality-card faculty-segment-panel">
      <h2>Faculty segments</h2>
      <div className="faculty-segment-list">
        {segments.map(([label, description]) => (
          <button className={selectedSegment === label ? 'active' : ''} type="button" key={label} onClick={() => onChange(selectedSegment === label ? '' : label)}>
            <strong>{label}</strong>
            <span>{description}</span>
          </button>
        ))}
      </div>
    </article>
  )
}

function FacultyTable({ facultyRows, onOpen }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('output')
  const [expanded, setExpanded] = useState('')

  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return facultyRows
      .filter((faculty) => JSON.stringify(faculty).toLowerCase().includes(query))
      .sort((a, b) => Number(b[sortBy] || 0) - Number(a[sortBy] || 0))
  }, [facultyRows, search, sortBy])

  return (
    <article className="table-card faculty-performance-table-card">
      <div className="table-toolbar">
        <div>
          <span>Faculty table</span>
          <h2>Aggregated Faculty Research Performance</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search faculty" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="output">Sort by output</option>
            <option value="diversity_score">Sort by diversity</option>
            <option value="funding">Sort by funding</option>
          </select>
        </div>
      </div>
      <div className="faculty-performance-table">
        <div className="faculty-performance-table-head">
          {['Faculty name', 'Employee ID', 'Department', 'School', 'Designation', 'Journal papers', 'Books', 'Patents', 'Projects', 'Funding', 'Guidance', 'Diversity score'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((faculty) => (
          <div key={faculty.email || faculty.employee_id}>
            <button className="faculty-performance-table-row" type="button" onClick={() => setExpanded(expanded === faculty.email ? '' : faculty.email)}>
              <strong>{faculty.faculty_name || faculty.full_name}</strong>
              <span>{faculty.employee_id || '-'}</span>
              <span>{departmentLabel(faculty)}</span>
              <span>{faculty.school || '-'}</span>
              <span>{faculty.designation || '-'}</span>
              <span>{faculty.journal_papers}</span>
              <span>{faculty.books}</span>
              <span>{faculty.patents}</span>
              <span>{faculty.projects}</span>
              <span>{money(faculty.funding)}</span>
              <span>{faculty.guidance}</span>
              <span>{faculty.diversity_score}</span>
            </button>
            {expanded === faculty.email && (
              <div className="faculty-expanded-row">
                <span>Segment: <strong>{faculty.segment}</strong></span>
                <span>Conferences: <strong>{faculty.conferences}</strong></span>
                <span>Awards: <strong>{faculty.awards}</strong></span>
                <button type="button" onClick={() => onOpen(faculty)}>Open detail drawer</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </article>
  )
}

function FacultyDrawer({ faculty, onClose }) {
  const [tab, setTab] = useState('Overview')
  if (!faculty) return null

  const categoryRows = [
    { label: 'Publications', value: faculty.journal_papers },
    { label: 'Books', value: faculty.books },
    { label: 'Patents/IPR', value: faculty.patents },
    { label: 'Projects', value: faculty.projects },
    { label: 'Guidance', value: faculty.guidance },
    { label: 'Conferences/Awards', value: faculty.conferences + faculty.awards },
  ]
  const trendValues = faculty.output_trend || faculty.year_trend || faculty.trend || []

  return (
    <aside className="faculty-drawer-backdrop" role="dialog" aria-modal="true" aria-label="Faculty detail drawer">
      <section className="faculty-drawer">
        <header>
          <div>
            <span>{faculty.department || 'Department'}</span>
            <h2>{faculty.faculty_name || faculty.full_name}</h2>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <nav className="faculty-drawer-tabs">
          {drawerTabs.map((item) => <button className={tab === item ? 'active' : ''} type="button" key={item} onClick={() => setTab(item)}>{item}</button>)}
        </nav>
        <div className="faculty-drawer-content">
          {tab === 'Overview' ? (
            <>
              <MiniBarChart title="Research category distribution" subtitle="Faculty detail" rows={categoryRows} />
              <div className="quality-grid">
                <span>Diversity score <strong>{faculty.diversity_score}</strong></span>
                <span>Funding received <strong>{money(faculty.funding)}</strong></span>
                <span>Consistency across years <strong>{faculty.consistency_years || 1}</strong></span>
                <span>Missing evidence alerts <strong>{faculty.missing_evidence_alerts || 0}</strong></span>
                {trendValues.length > 1 && (
                  <span>Output trend <strong><SparklineRow values={trendValues.map((value) => Number(value || 0))} label="Faculty output trend" /></strong></span>
                )}
              </div>
            </>
          ) : (
            <div className="faculty-drawer-placeholder">
              <strong>{tab}</strong>
              <span>Additional fields and documents for this section stay inside the detail drawer.</span>
            </div>
          )}
        </div>
      </section>
    </aside>
  )
}

function buildMockFacultyRows() {
  return mockResearchAnalytics.faculty.items.map((faculty, index) => {
    const row = {
      ...faculty,
      email: faculty.email,
      faculty_name: faculty.faculty_name,
      journal_papers: faculty.total_research_papers || 0,
      books: faculty.book_publications || 0,
      patents: faculty.patents || 0,
      projects: faculty.research_projects || 0,
      funding: faculty.total_funding || 0,
      guidance: index % 3,
      conferences: faculty.conference_publications || 0,
      awards: index % 2,
      self_score: (faculty.total_vc_score || 0) + 8,
      validated_score: faculty.total_vc_score || 0,
      current_year_output: Math.max(0, Math.floor((faculty.total_research_papers || 0) / 2)),
      previous_year_output: Math.max(0, Math.floor((faculty.total_research_papers || 0) / 3)),
      first_activity_year: index === 2 ? '2025-2026' : '2023-2024',
      consistency_years: 2 + index,
      missing_evidence_alerts: index % 2,
    }
    row.diversity_score = diversityScore(row)
    row.output = totalOutput(row)
    row.segment = segmentFaculty(row, '')
    return row
  })
}

export default function FacultyResearchPerformancePage({ filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [response, setResponse] = useState({ items: buildMockFacultyRows() })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [segmentFilter, setSegmentFilter] = useState('')
  const [selectedFaculty, setSelectedFaculty] = useState(null)

  useEffect(() => {
    let ignore = false
    async function loadFacultyPerformance() {
      setLoading((current) => current)
      setError('')
      try {
        const data = await researchAnalyticsApi.facultyPerformance(filters)
        if (!ignore) setResponse({ items: data.items || data.faculty || [] })
      } catch (requestError) {
        if (!ignore) {
          setResponse({ items: buildMockFacultyRows() })
          setError(`${requestError.message} Showing demo faculty performance analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadFacultyPerformance()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const facultyRows = (response.items || []).map((faculty) => {
    const row = {
      ...faculty,
      email: faculty.email || faculty.faculty_email || faculty.faculty_id,
      faculty_name: faculty.faculty_name || faculty.full_name,
      journal_papers: Number(faculty.journal_papers ?? faculty.total_research_papers ?? faculty.journal_publications ?? 0),
      books: Number(faculty.books ?? faculty.book_publications ?? 0),
      patents: Number(faculty.patents ?? 0),
      projects: Number(faculty.projects ?? faculty.research_projects ?? 0),
      funding: Number(faculty.funding ?? faculty.total_funding ?? faculty.project_funding ?? 0),
      guidance: Number(faculty.guidance ?? faculty.research_guidance ?? 0),
      conferences: Number(faculty.conferences ?? faculty.conference_publications ?? 0),
      awards: Number(faculty.awards ?? 0),
      self_score: Number(faculty.self_score ?? 0),
      validated_score: validatedScore(faculty),
    }
    row.diversity_score = Number(faculty.diversity_score ?? diversityScore(row))
    row.output = totalOutput(row)
    row.segment = faculty.segment || segmentFaculty(row, filters.year)
    return row
  })
  const filteredRows = segmentFilter ? facultyRows.filter((faculty) => faculty.segment === segmentFilter) : facultyRows
  const activeRows = facultyRows.filter((faculty) => faculty.output > 0)
  const leaders = facultyRows.filter((faculty) => faculty.segment === 'Research Leaders')
  const emerging = facultyRows.filter((faculty) => faculty.segment === 'Emerging Researchers')
  const inactive = facultyRows.filter((faculty) => faculty.output === 0 || faculty.segment === 'Inactive Researchers')
  const avgDiversity = facultyRows.length ? facultyRows.reduce((sum, faculty) => sum + faculty.diversity_score, 0) / facultyRows.length : 0
  const avgValidated = facultyRows.length ? facultyRows.reduce((sum, faculty) => sum + faculty.validated_score, 0) / facultyRows.length : 0
  const avgSelf = facultyRows.length ? facultyRows.reduce((sum, faculty) => sum + Number(faculty.self_score || 0), 0) / facultyRows.length : 0
  const topOutputRows = [...facultyRows].sort((a, b) => b.output - a.output).map((faculty) => ({ label: faculty.faculty_name, value: faculty.output, validatedScore: faculty.validated_score }))
  const topScoreRows = [...facultyRows].sort((a, b) => b.validated_score - a.validated_score).map((faculty) => ({ label: faculty.faculty_name, value: faculty.validated_score }))
  const diversityRows = Object.entries(facultyRows.reduce((acc, faculty) => ({ ...acc, [faculty.diversity_score]: (acc[faculty.diversity_score] || 0) + 1 }), {})).map(([label, value]) => ({ label: `${label} categories`, value }))
  const scatterRows = facultyRows.map((faculty) => ({ label: faculty.faculty_name, email: faculty.email, output: faculty.output, diversity: faculty.diversity_score }))
  const diversityPct = facultyRows.length ? (facultyRows.filter((faculty) => faculty.diversity_score >= 3).length / facultyRows.length) * 100 : 0
  const participationPct = facultyRows.length ? (activeRows.length / facultyRows.length) * 100 : 0
  const radarAxes = [
    { key: 'journals', label: 'Journals' },
    { key: 'books', label: 'Books' },
    { key: 'patents', label: 'Patents' },
    { key: 'projects', label: 'Projects' },
    { key: 'guidance', label: 'Guidance' },
    { key: 'conferences', label: 'Conferences' },
  ]
  const radarRows = [...facultyRows].sort((a, b) => b.output - a.output).slice(0, 3).map((faculty) => ({
    label: faculty.faculty_name,
    journals: faculty.journal_papers,
    books: faculty.books,
    patents: faculty.patents,
    projects: faculty.projects,
    guidance: faculty.guidance,
    conferences: faculty.conferences,
  }))

  return (
    <main className="research-page faculty-performance-page">
      <PageHeader
        title="Faculty Research Performance"
        description="Faculty-level research activity, validated scores, diversity, consistency, and transparent performance segments"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading faculty performance">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Research-Active Faculty', value: formatNumber(activeRows.length), icon: 'AF', subtext: 'At least one valid activity' },
            { label: 'Research Leaders', value: formatNumber(leaders.length), icon: 'RL', subtext: 'High output, score, diversity' },
            { label: 'Emerging Researchers', value: formatNumber(emerging.length), icon: 'ER', subtext: 'First contribution in selected year' },
            { label: 'Inactive Researchers', value: formatNumber(inactive.length), icon: 'IR', subtext: 'No recorded research activity for the selected period.' },
            { label: 'Average Diversity Score', value: avgDiversity.toFixed(2), icon: 'DS', subtext: 'Research categories active' },
            { label: 'Average Validated Research Score', value: avgValidated.toFixed(2), icon: 'VS', subtext: 'Final validated score' },
          ]} secondaryKpis={[
            { label: 'Active Contributors', value: facultyRows.filter((faculty) => faculty.segment === 'Active Contributors').length },
            { label: 'Specialists', value: facultyRows.filter((faculty) => faculty.segment === 'Specialists').length },
            { label: 'Declining Contributors', value: facultyRows.filter((faculty) => faculty.segment === 'Declining Contributors').length },
          ]} />

          <div className="stat-rings-row">
            <StatRing value={participationPct} label="Research Participation" color="#6366f1" />
            <StatRing value={diversityPct} label="Diversity Score 3+" color="#22c55e" />
            <StatRing value={avgSelf ? (avgValidated / avgSelf) * 100 : 0} label="Validated Score Ratio" color="#f59e0b" />
          </div>

          <section className="executive-chart-row two-col">
            <RankingList title="Top Faculty by Total Output" subtitle="Output ranking" rows={topOutputRows} badgeKey="validatedScore" badgeFormatter={(value) => `VC ${formatNumber(value)}`} />
            <MiniBarChart title="Top faculty by validated score" subtitle="Validated score" rows={topScoreRows} />
            <RadarChart title="Top Faculty Research Profile" subtitle="Top 3 by output" axes={radarAxes} rows={radarRows} />
            <MiniBarChart title="Research diversity distribution" subtitle="Diversity" rows={diversityRows} />
            <MiniBarChart title="Faculty performance trend" subtitle="Selected period" rows={topOutputRows.slice(0, 6)} />
            <ScatterChart rows={scatterRows} />
            <MiniBarChart title="Self versus final score comparison" subtitle="Score review" rows={facultyRows.map((faculty) => ({ label: faculty.faculty_name, value: Math.max(faculty.self_score - faculty.validated_score, 0) }))} />
          </section>

          <SegmentPanel selectedSegment={segmentFilter} onChange={setSegmentFilter} />
          <FacultyTable facultyRows={filteredRows} onOpen={setSelectedFaculty} />
          <FacultyDrawer faculty={selectedFaculty} onClose={() => setSelectedFaculty(null)} />
        </>
      )}
    </main>
  )
}
