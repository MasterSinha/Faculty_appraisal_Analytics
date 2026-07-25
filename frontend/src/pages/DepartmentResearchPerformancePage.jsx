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
import StatRing from '../components/research-analytics/charts/StatRing'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Comparison', 'Participation', 'Funding and Innovation', 'Research Health', 'Gaps and Opportunities']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0))
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function healthCategory(score) {
  if (score >= 80) return 'Excellent'
  if (score >= 65) return 'Strong'
  if (score >= 45) return 'Developing'
  return 'Needs Attention'
}

function clamp(value) {
  return Math.max(0, Math.min(Number(value || 0), 100))
}

function calculateHealth(row) {
  const components = {
    publication_participation: clamp(row.publication_participation_rate),
    output_per_faculty: clamp((row.papers_per_active_faculty || 0) * 20),
    funding_performance: clamp((row.funding || 0) / 100000),
    patent_ipr_performance: clamp((row.patents || 0) * 20),
    research_guidance: clamp((row.research_guidance || 0) * 20),
    yoy_growth: clamp(50 + Number(row.year_over_year_growth || 0)),
  }
  const score = (components.publication_participation * 0.3)
    + (components.output_per_faculty * 0.2)
    + (components.funding_performance * 0.15)
    + (components.patent_ipr_performance * 0.15)
    + (components.research_guidance * 0.1)
    + (components.yoy_growth * 0.1)
  return { score, components }
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
  if (context.includes('growth') || context.includes('year')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('patent') || context.includes('no patents')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('participation') || context.includes('health score')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('funding') || context.includes('output')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function HealthBreakdown({ department }) {
  if (!department) return null
  const parts = [
    ['Publication participation', department.health_components.publication_participation, '30%'],
    ['Output per faculty', department.health_components.output_per_faculty, '20%'],
    ['Funding performance', department.health_components.funding_performance, '15%'],
    ['Patent and IPR performance', department.health_components.patent_ipr_performance, '15%'],
    ['Research guidance', department.health_components.research_guidance, '10%'],
    ['Year-over-year growth', department.health_components.yoy_growth, '10%'],
  ]
  return (
    <article className="quality-card department-health-card">
      <h2>Research-health score breakdown</h2>
      <div className="department-health-list">
        {parts.map(([label, value, weight]) => (
          <div key={label}>
            <span>{label}<em>{weight}</em></span>
            <div><i style={{ width: `${clamp(value)}%` }} /></div>
            <strong>{percent(value)}</strong>
          </div>
        ))}
      </div>
      <div className="quality-grid">
        <span>Research diversity <strong>{department.diversity_score}</strong></span>
        <span>Inactive faculty percentage <strong>{percent(department.inactive_faculty_percentage)}</strong></span>
        <span>Data completeness <strong>{percent(department.data_completeness)}</strong></span>
        <span>Funding concentration <strong>{percent(department.funding_concentration)}</strong></span>
      </div>
    </article>
  )
}

function DepartmentHeatmap({ rows }) {
  const categories = ['Journals', 'Books', 'Patents', 'Projects', 'Funding', 'Guidance']
  const keys = ['journal_papers', 'books', 'patents', 'projects', 'funding_scaled', 'research_guidance']
  return (
    <article className="chart-card department-performance-chart-card">
      <div className="card-title">
        <span>Category heatmap</span>
        <h2>Department category heatmap</h2>
      </div>
      <div className="department-heatmap">
        <div className="department-heatmap-head">
          <span>Department</span>
          {categories.map((category) => <span key={category}>{category}</span>)}
        </div>
        {rows.slice(0, 8).map((row) => (
          <div className="department-heatmap-row" key={row.department}>
            <strong>{row.department}</strong>
            {keys.map((key) => <i key={key} style={{ opacity: Math.max(clamp(row[key] * 18) / 100, 0.15) }} />)}
          </div>
        ))}
      </div>
    </article>
  )
}

function DepartmentTable({ rows, onOpen }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('research_health_score')
  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return rows
      .filter((row) => JSON.stringify(row).toLowerCase().includes(query))
      .sort((a, b) => Number(b[sortBy] || 0) - Number(a[sortBy] || 0))
  }, [rows, search, sortBy])

  return (
    <article className="table-card department-performance-table-card">
      <div className="table-toolbar">
        <div>
          <span>Department table</span>
          <h2>Department Research Performance</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search departments" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="research_health_score">Sort by health score</option>
            <option value="total_research_output">Sort by output</option>
            <option value="publication_participation_rate">Sort by participation</option>
            <option value="funding">Sort by funding</option>
          </select>
        </div>
      </div>
      <div className="department-performance-table">
        <div className="department-performance-table-head">
          {['School', 'Department', 'Active faculty', 'Total output', 'Publishing faculty', 'Participation rate', 'Papers / faculty', 'Books', 'Patents', 'Funding', 'Guidance', 'Diversity', 'YoY growth', 'Health score'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((row) => (
          <button className="department-performance-table-row" type="button" key={`${row.school}-${row.department}`} onClick={() => onOpen(row)}>
            <span>{row.school}</span>
            <strong>{row.department}</strong>
            <span>{row.active_faculty}</span>
            <span>{row.total_research_output}</span>
            <span>{row.publishing_faculty}</span>
            <span>{percent(row.publication_participation_rate)}</span>
            <span>{Number(row.papers_per_active_faculty || 0).toFixed(2)}</span>
            <span>{row.books}</span>
            <span>{row.patents}</span>
            <span>{money(row.funding)}</span>
            <span>{row.research_guidance}</span>
            <span>{row.diversity_score}</span>
            <span>{percent(row.year_over_year_growth)}</span>
            <span>{Math.round(row.research_health_score)} · {row.health_category}</span>
          </button>
        ))}
      </div>
    </article>
  )
}

function DepartmentDrawer({ department, onClose }) {
  if (!department) return null
  return (
    <aside className="faculty-drawer-backdrop" role="dialog" aria-modal="true" aria-label="Department detail drawer">
      <section className="faculty-drawer">
        <header>
          <div>
            <span>{department.school}</span>
            <h2>{department.department}</h2>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <div className="faculty-drawer-content">
          <HealthBreakdown department={department} />
          <div className="quality-grid">
            <span>Faculty distribution <strong>{department.active_faculty} active</strong></span>
            <span>Category contributions <strong>{department.diversity_score} categories</strong></span>
            <span>Top faculty <strong>{department.top_faculty?.[0] || 'Not available'}</strong></span>
            <span>Research concentration <strong>{percent(department.research_concentration)}</strong></span>
            <span>Funding agencies <strong>{department.funding_agencies?.length || 0}</strong></span>
            <span>Patent status <strong>{department.patent_status || 'No patents recorded'}</strong></span>
            <span>Guidance participation <strong>{department.research_guidance}</strong></span>
            <span>Gaps <strong>{department.gaps?.length || 0}</strong></span>
            <span>Data-quality issues <strong>{department.data_quality_issues || 0}</strong></span>
          </div>
        </div>
      </section>
    </aside>
  )
}

function buildMockDepartments() {
  return Object.entries(groupBy(mockResearchAnalytics.faculty.items, (faculty) => departmentLabel(faculty))).map(([department, facultyRows], index) => {
    const activeFaculty = facultyRows.length
    const journalPapers = facultyRows.reduce((sum, faculty) => sum + Number(faculty.total_research_papers || 0), 0)
    const books = facultyRows.reduce((sum, faculty) => sum + Number(faculty.book_publications || 0), 0)
    const patents = facultyRows.reduce((sum, faculty) => sum + Number(faculty.patents || 0), 0)
    const projects = facultyRows.reduce((sum, faculty) => sum + Number(faculty.research_projects || 0), 0)
    const funding = facultyRows.reduce((sum, faculty) => sum + Number(faculty.total_funding || 0), 0)
    const publishingFaculty = facultyRows.filter((faculty) => Number(faculty.total_research_papers || 0) > 0).length
    const row = {
      school: facultyRows[0]?.school || 'Unknown',
      department,
      active_faculty: activeFaculty,
      total_research_output: journalPapers + books + patents + projects,
      publishing_faculty: publishingFaculty,
      publication_participation_rate: activeFaculty ? (publishingFaculty / activeFaculty) * 100 : 0,
      papers_per_active_faculty: activeFaculty ? journalPapers / activeFaculty : 0,
      journal_papers: journalPapers,
      books,
      patents,
      projects,
      funding,
      funding_scaled: funding / 1000000,
      research_guidance: index + 1,
      diversity_score: [journalPapers, books, patents, projects, funding, index + 1].filter((value) => Number(value || 0) > 0).length,
      year_over_year_growth: 12 - (index * 5),
      inactive_faculty_percentage: 0,
      data_completeness: 88 - index * 4,
      funding_concentration: 35 + index * 8,
      research_concentration: 42 + index * 6,
      top_faculty: facultyRows.map((faculty) => faculty.faculty_name),
      funding_agencies: ['AICTE', 'DST'].slice(0, index + 1),
      patent_status: patents ? 'Filed / Granted mix' : 'No patents recorded',
      gaps: patents ? [] : ['Patent and IPR activity gap'],
      data_quality_issues: index,
    }
    const health = calculateHealth(row)
    row.health_components = health.components
    row.research_health_score = health.score
    row.health_category = healthCategory(health.score)
    return row
  })
}

export default function DepartmentResearchPerformancePage({ filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [response, setResponse] = useState({ items: buildMockDepartments() })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('Comparison')
  const [selectedDepartment, setSelectedDepartment] = useState(null)

  useEffect(() => {
    let ignore = false
    async function loadDepartments() {
      setLoading((current) => current)
      setError('')
      try {
        const data = await researchAnalyticsApi.departmentPerformance(filters)
        if (!ignore) setResponse({ items: data.items || data.departments || [] })
      } catch (requestError) {
        if (!ignore) {
          setResponse({ items: buildMockDepartments() })
          setError(`${requestError.message} Showing demo department performance analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadDepartments()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const rows = (response.items || []).map((item) => {
    const health = item.health_components ? { score: item.research_health_score, components: item.health_components } : calculateHealth(item)
    return {
      ...item,
      department: departmentLabel(item),
      health_components: health.components,
      research_health_score: Number(health.score || 0),
      health_category: item.health_category || healthCategory(health.score),
      funding_scaled: Number(item.funding || 0) / 1000000,
    }
  })
  const topOutput = [...rows].sort((a, b) => b.total_research_output - a.total_research_output)[0]
  const topParticipation = [...rows].sort((a, b) => b.publication_participation_rate - a.publication_participation_rate)[0]
  const topFunding = [...rows].sort((a, b) => b.funding - a.funding)[0]
  const noPatents = rows.filter((row) => Number(row.patents || 0) === 0)
  const attention = rows.filter((row) => row.health_category === 'Needs Attention')
  const chartRows = rows.map((row) => ({ ...row, label: departmentLabel(row), value: row.total_research_output }))

  return (
    <main className="research-page department-performance-page">
      <PageHeader
        title="Department Research Performance"
        description="Department-level output, participation, innovation, funding, and research-health breakdown"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading department performance">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Total Departments', value: formatNumber(rows.length), icon: 'TD', subtext: 'Departments in scope' },
            { label: 'Highest Research-Output Department', value: topOutput?.department || '-', icon: 'RO', subtext: `${formatNumber(topOutput?.total_research_output)} outputs` },
            { label: 'Highest Participation Department', value: topParticipation?.department || '-', icon: 'HP', subtext: percent(topParticipation?.publication_participation_rate) },
            { label: 'Highest-Funded Department', value: topFunding?.department || '-', icon: 'HF', subtext: money(topFunding?.funding) },
            { label: 'Departments with No Patents', value: formatNumber(noPatents.length), icon: 'NP', subtext: 'Patent/IPR gap' },
            { label: 'Departments Needing Attention', value: formatNumber(attention.length), icon: 'NA', subtext: 'Research-health category' },
          ]} secondaryKpis={[
            { label: 'Excellent departments', value: rows.filter((row) => row.health_category === 'Excellent').length },
            { label: 'Strong departments', value: rows.filter((row) => row.health_category === 'Strong').length },
            { label: 'Developing departments', value: rows.filter((row) => row.health_category === 'Developing').length },
          ]} />

          <nav className="page-tabs" aria-label="Department performance tabs">
            {tabs.map((tab) => <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>{tab}</button>)}
          </nav>

          {activeTab === 'Comparison' && (
            <section className="executive-chart-row two-col">
              <StatRing value={rows.length ? (rows.filter((row) => row.health_category === 'Excellent' || row.health_category === 'Strong').length / rows.length) * 100 : 0} label="Strong Departments" color="#22c55e" />
              <RankingList title="Department output ranking" subtitle="Research output" rows={chartRows} />
              <MiniBarChart title="Department output ranking" subtitle="Research output" rows={chartRows} />
              <RadarChart title="Top Department Research Profile" subtitle="Top 3 departments" axes={[
                { key: 'journals', label: 'Journals' },
                { key: 'patents', label: 'Patents' },
                { key: 'projects', label: 'Projects' },
                { key: 'guidance', label: 'Guidance' },
                { key: 'conferences', label: 'Conferences' },
              ]} rows={[...rows].sort((a, b) => b.total_research_output - a.total_research_output).slice(0, 3).map((row) => ({
                label: row.department,
                journals: row.journal_papers,
                patents: row.patents,
                projects: row.projects,
                guidance: row.research_guidance,
                conferences: row.conferences,
              }))} />
              <DepartmentHeatmap rows={rows} />
            </section>
          )}
          {activeTab === 'Participation' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Participation rate by department" subtitle="Publishing faculty" rows={rows.map((row) => ({ label: row.department, value: row.publication_participation_rate }))} formatter={percent} />
              <MiniBarChart title="Year-over-year growth" subtitle="Growth" rows={rows.map((row) => ({ label: row.department, value: row.year_over_year_growth }))} formatter={percent} />
            </section>
          )}
          {activeTab === 'Funding and Innovation' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Funding by department" subtitle="Funding" rows={rows.map((row) => ({ label: row.department, value: row.funding }))} formatter={money} />
              <MiniBarChart title="Patent and IPR activity" subtitle="Innovation" rows={rows.map((row) => ({ label: row.department, value: row.patents }))} />
            </section>
          )}
          {activeTab === 'Research Health' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Research health score breakdown" subtitle="Health score" rows={rows.map((row) => ({ label: row.department, value: row.research_health_score }))} />
              <HealthBreakdown department={rows[0]} />
            </section>
          )}
          {activeTab === 'Gaps and Opportunities' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Departments with no patents" subtitle="Gap count" rows={noPatents.map((row) => ({ label: row.department, value: 1 }))} />
              <MiniBarChart title="Departments needing attention" subtitle="Health category" rows={attention.map((row) => ({ label: row.department, value: row.research_health_score }))} />
            </section>
          )}

          <DepartmentTable rows={rows} onOpen={setSelectedDepartment} />
          <DepartmentDrawer department={selectedDepartment} onClose={() => setSelectedDepartment(null)} />
        </>
      )}
    </main>
  )
}
