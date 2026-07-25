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
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0))
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
  if (context.includes('trend') || context.includes('growth') || context.includes('year')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('funding') || context.includes('contribution') || context.includes('patent')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('diversity') || context.includes('ranking')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('participation') || context.includes('department comparison')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function CategoryComparison({ rows }) {
  const categories = [
    ['Journals', 'journal_papers'],
    ['Books', 'books'],
    ['Patents', 'patents'],
    ['Projects', 'research_projects'],
    ['Guidance', 'students_guided'],
    ['Products', 'products'],
  ]
  const max = Math.max(...rows.flatMap((row) => categories.map(([, key]) => Number(row[key] || 0))), 1)

  return (
    <article className="chart-card school-performance-chart-card">
      <div className="card-title">
        <span>Category comparison</span>
        <h2>Research category comparison by school</h2>
      </div>
      <div className="school-category-grid">
        {rows.map((row) => (
          <div className="school-category-row" key={row.school}>
            <strong>{row.school}</strong>
            {categories.map(([label, key]) => (
              <span key={key}>
                <em>{label}</em>
                <i style={{ width: `${(Number(row[key] || 0) / max) * 100}%` }} />
              </span>
            ))}
          </div>
        ))}
      </div>
    </article>
  )
}

function InsightPanel({ insights }) {
  return (
    <section className="attention-section">
      <div className="section-title">
        <span>Insights</span>
        <h2>School-level observations</h2>
      </div>
      <div className="attention-grid">
        {insights.map((insight) => (
          <article className="attention-card" key={insight.title}>
            <div>
              <strong>{insight.title}</strong>
              <p>{insight.message}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function SchoolTable({ rows, onOpen }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('total_output')

  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return rows
      .filter((row) => JSON.stringify(row).toLowerCase().includes(query))
      .sort((a, b) => Number(b[sortBy] || 0) - Number(a[sortBy] || 0))
  }, [rows, search, sortBy])

  return (
    <article className="table-card school-performance-table-card">
      <div className="table-toolbar">
        <div>
          <span>School table</span>
          <h2>School Research Performance</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search schools" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="total_output">Sort by output</option>
            <option value="total_funding">Sort by funding</option>
            <option value="publication_participation">Sort by participation</option>
            <option value="patents">Sort by patents</option>
            <option value="year_over_year_growth">Sort by growth</option>
          </select>
        </div>
      </div>
      <div className="school-performance-table">
        <div className="school-performance-table-head">
          {['School', 'Active faculty', 'Departments', 'Total output', 'Publication participation', 'Papers / faculty', 'Books', 'Patents', 'Projects', 'Total funding', 'Students guided', 'Awards', 'Products', 'Diversity', 'YoY growth'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((row) => (
          <button className="school-performance-table-row" type="button" key={row.school} onClick={() => onOpen(row)}>
            <strong>{row.school}</strong>
            <span>{row.active_faculty}</span>
            <span>{row.departments}</span>
            <span>{row.total_output}</span>
            <span>{percent(row.publication_participation)}</span>
            <span>{Number(row.papers_per_faculty || 0).toFixed(2)}</span>
            <span>{row.books}</span>
            <span>{row.patents}</span>
            <span>{row.research_projects}</span>
            <span>{money(row.total_funding)}</span>
            <span>{row.students_guided}</span>
            <span>{row.awards}</span>
            <span>{row.products}</span>
            <span>{row.diversity_score}</span>
            <span>{percent(row.year_over_year_growth)}</span>
          </button>
        ))}
      </div>
    </article>
  )
}

function SchoolDrawer({ school, onClose }) {
  if (!school) return null

  return (
    <aside className="faculty-drawer-backdrop" role="dialog" aria-modal="true" aria-label="School detail drawer">
      <section className="faculty-drawer">
        <header>
          <div>
            <span>School detail</span>
            <h2>{school.school}</h2>
          </div>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <div className="faculty-drawer-content">
          <MiniBarChart title="Department comparison" subtitle="Departments" rows={(school.department_comparison || []).map((row) => ({ label: row.department, value: row.total_output }))} />
          <div className="quality-grid">
            <span>Faculty participation <strong>{percent(school.publication_participation)}</strong></span>
            <span>Research category profile <strong>{school.diversity_score} categories</strong></span>
            <span>Funding agency profile <strong>{school.funding_agencies?.length || 0}</strong></span>
            <span>Patents <strong>{school.patents}</strong></span>
            <span>Guidance <strong>{school.students_guided}</strong></span>
            <span>Growth <strong>{percent(school.year_over_year_growth)}</strong></span>
            <span>Data-quality issues <strong>{school.data_quality_issues || 0}</strong></span>
          </div>
        </div>
      </section>
    </aside>
  )
}

function buildMockSchools() {
  return Object.entries(groupBy(mockResearchAnalytics.faculty.items, (faculty) => faculty.school)).map(([school, facultyRows], index) => {
    const departments = Object.keys(groupBy(facultyRows, (faculty) => departmentLabel(faculty)))
    const journalPapers = facultyRows.reduce((sum, faculty) => sum + Number(faculty.total_research_papers || 0), 0)
    const books = facultyRows.reduce((sum, faculty) => sum + Number(faculty.book_publications || 0), 0)
    const patents = facultyRows.reduce((sum, faculty) => sum + Number(faculty.patents || 0), 0)
    const projects = facultyRows.reduce((sum, faculty) => sum + Number(faculty.research_projects || 0), 0)
    const funding = facultyRows.reduce((sum, faculty) => sum + Number(faculty.total_funding || 0), 0)
    const publishingFaculty = facultyRows.filter((faculty) => Number(faculty.total_research_papers || 0) > 0).length
    const products = index === 0 ? 3 : 0
    const studentsGuided = index + 3
    return {
      school,
      active_faculty: facultyRows.length,
      departments: departments.length,
      total_output: journalPapers + books + patents + projects + studentsGuided + products,
      publication_participation: facultyRows.length ? (publishingFaculty / facultyRows.length) * 100 : 0,
      papers_per_faculty: facultyRows.length ? journalPapers / facultyRows.length : 0,
      journal_papers: journalPapers,
      books,
      patents,
      ipr_records: index,
      research_projects: projects,
      external_projects: index === 0 ? 2 : 0,
      total_funding: funding,
      students_guided: studentsGuided,
      awards: index + 1,
      products,
      diversity_score: [journalPapers, books, patents, projects, funding, studentsGuided, products].filter((value) => Number(value || 0) > 0).length,
      year_over_year_growth: 18 - index * 7,
      funding_agencies: ['AICTE', 'DST', 'Industry Sponsored'].slice(0, index + 2),
      dependent_researcher_share: 42 + index * 12,
      data_quality_issues: index,
      department_comparison: departments.map((department) => ({ department, total_output: Math.max(1, Math.round((journalPapers + books + patents + projects) / departments.length)) })),
    }
  })
}

export default function SchoolResearchPerformancePage({ filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [response, setResponse] = useState({ items: buildMockSchools() })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedSchool, setSelectedSchool] = useState(null)

  useEffect(() => {
    let ignore = false
    async function loadSchools() {
      setLoading(true)
      setError('')
      try {
        const data = await researchAnalyticsApi.schoolPerformance(filters)
        if (!ignore) setResponse({ items: data.items || data.schools || [] })
      } catch (requestError) {
        if (!ignore) {
          setResponse({ items: buildMockSchools() })
          setError(`${requestError.message} Showing demo school performance analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadSchools()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const rows = response.items || []
  const universityOutput = rows.reduce((sum, row) => sum + Number(row.total_output || 0), 0)
  const topOutput = [...rows].sort((a, b) => b.total_output - a.total_output)[0]
  const topFunding = [...rows].sort((a, b) => b.total_funding - a.total_funding)[0]
  const topParticipation = [...rows].sort((a, b) => b.publication_participation - a.publication_participation)[0]
  const topPatents = [...rows].sort((a, b) => b.patents - a.patents)[0]
  const noExternalProject = rows.filter((row) => Number(row.external_projects || 0) === 0)
  const fundingPerFaculty = [...rows].sort((a, b) => (b.total_funding / Math.max(b.active_faculty, 1)) - (a.total_funding / Math.max(a.active_faculty, 1)))[0]
  const topGrowth = [...rows].sort((a, b) => b.year_over_year_growth - a.year_over_year_growth)[0]
  const lowParticipationHighFaculty = [...rows].filter((row) => row.active_faculty >= 10 || rows.length <= 3).sort((a, b) => a.publication_participation - b.publication_participation)[0]
  const dependentSchool = [...rows].sort((a, b) => b.dependent_researcher_share - a.dependent_researcher_share)[0]
  const chartRows = rows.map((row) => ({ label: row.school, value: row.total_output }))
  const contributionRows = rows.map((row) => ({ label: row.school, value: universityOutput ? (row.total_output / universityOutput) * 100 : 0 }))
  const patentRows = rows.map((row) => ({ label: row.school, value: Number(row.patents || 0) + Number(row.ipr_records || 0) }))

  const insights = [
    { title: 'Largest publication share', message: `${topOutput?.school || '-'} contributes the largest share of publications and output in the selected period.` },
    { title: 'Highest funding per faculty', message: `${fundingPerFaculty?.school || '-'} has the highest funding per active faculty.` },
    { title: 'Highest growth', message: `${topGrowth?.school || '-'} shows the strongest year-over-year growth.` },
    { title: 'Low participation with faculty strength', message: `${lowParticipationHighFaculty?.school || '-'} should review participation breadth across active faculty.` },
    { title: 'No external funding', message: `${noExternalProject[0]?.school || 'No school'} has no external project recorded in this view.` },
    { title: 'Researcher concentration', message: `${dependentSchool?.school || '-'} appears most dependent on a small number of researchers.` },
  ]

  return (
    <main className="research-page school-performance-page">
      <PageHeader
        title="School Research Performance"
        description="School-level research output, participation, funding, innovation, guidance, and contribution share"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading school performance">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Total Schools', value: formatNumber(rows.length), icon: 'TS', subtext: 'Schools in scope' },
            { label: 'Highest Research-Output School', value: topOutput?.school || '-', icon: 'RO', subtext: `${formatNumber(topOutput?.total_output)} outputs` },
            { label: 'Highest-Funded School', value: topFunding?.school || '-', icon: 'HF', subtext: money(topFunding?.total_funding) },
            { label: 'Highest Participation School', value: topParticipation?.school || '-', icon: 'HP', subtext: percent(topParticipation?.publication_participation) },
            { label: 'Highest Patent-Producing School', value: topPatents?.school || '-', icon: 'PT', subtext: `${formatNumber(topPatents?.patents)} patents` },
            { label: 'Schools with No External Project', value: formatNumber(noExternalProject.length), icon: 'NE', subtext: 'External project gap' },
          ]} secondaryKpis={[
            { label: 'University output', value: formatNumber(universityOutput) },
            { label: 'Total funding', value: money(rows.reduce((sum, row) => sum + Number(row.total_funding || 0), 0)) },
            { label: 'Total students guided', value: formatNumber(rows.reduce((sum, row) => sum + Number(row.students_guided || 0), 0)) },
          ]} />

          <section className="executive-chart-row two-col">
            <RankingList title="School research output" subtitle="Total output ranking" rows={chartRows} />
            <RadarChart title="School Research Profile" subtitle="Category comparison" axes={[
              { key: 'journals', label: 'Journals' },
              { key: 'books', label: 'Books' },
              { key: 'patents', label: 'Patents' },
              { key: 'projects', label: 'Projects' },
              { key: 'guidance', label: 'Guidance' },
            ]} rows={rows.slice(0, 3).map((row) => ({
              label: row.school,
              journals: row.journal_papers,
              books: row.books,
              patents: row.patents,
              projects: row.research_projects,
              guidance: row.students_guided,
            }))} />
            <CategoryComparison rows={rows} />
            <MiniBarChart title="Publication participation by school" subtitle="Participation" rows={rows.map((row) => ({ label: row.school, value: row.publication_participation }))} formatter={percent} />
            <MiniBarChart title="Funding by school" subtitle="Funding" rows={rows.map((row) => ({ label: row.school, value: row.total_funding }))} formatter={money} />
            <MiniBarChart title="Patent and IPR contribution by school" subtitle="Innovation" rows={patentRows} />
            <MiniBarChart title="Academic-year trend" subtitle="Growth" rows={rows.map((row) => ({ label: row.school, value: row.year_over_year_growth }))} formatter={percent} />
            <MiniBarChart title="School research diversity" subtitle="Diversity" rows={rows.map((row) => ({ label: row.school, value: row.diversity_score }))} />
            <MiniBarChart title="School contribution percentage to university output" subtitle="Contribution share" rows={contributionRows} formatter={percent} />
            <MiniBarChart title="School output ranking" subtitle="Total output" rows={chartRows} />
          </section>

          <InsightPanel insights={insights} />
          <SchoolTable rows={rows} onOpen={setSelectedSchool} />
          <SchoolDrawer school={selectedSchool} onClose={() => setSelectedSchool(null)} />
        </>
      )}
    </main>
  )
}
