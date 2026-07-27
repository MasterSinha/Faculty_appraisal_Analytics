import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import SparklineRow from '../components/research-analytics/charts/SparklineRow'
import StatRing from '../components/research-analytics/charts/StatRing'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Funding Overview', 'Research Projects', 'External Projects', 'Proposals', 'Funding Agencies', 'Faculty and Department Funding']

function money(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function normalizeStatus(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return 'Unknown'
  if (text.includes('propos')) return 'Proposed'
  if (text.includes('submit')) return 'Submitted'
  if (text.includes('sanction') || text.includes('approve')) return 'Sanctioned'
  if (text.includes('ongoing') || text.includes('progress')) return 'Ongoing'
  if (text.includes('complete')) return 'Completed'
  if (text.includes('reject')) return 'Rejected'
  if (text.includes('closed') || text.includes('close')) return 'Closed'
  return 'Unknown'
}

function normalizeRole(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return 'Other'
  if (text.includes('principal') || text === 'pi') return 'Principal Investigator'
  if (text.includes('co-principal') || text.includes('co pi') || text.includes('co-pi')) return 'Co-Principal Investigator'
  if (text.includes('co-investigator') || text.includes('coinvestigator')) return 'Co-Investigator'
  if (text.includes('team') || text.includes('member')) return 'Team Member'
  return 'Other'
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Unknown'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function sumAmount(rows) {
  return rows.reduce((sum, row) => sum + Number(row.amount || row.sanctioned_amount || 0), 0)
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('trend') || context.includes('year')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('status') || context.includes('count by agency')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('funding by faculty') || context.includes('funding by department')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('agency') || context.includes('faculty') || context.includes('funding')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <ComparisonTiles title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function DonutChart({ title, subtitle, rows, valueKey = 'value', formatter = formatNumber }) {
  const [active, setActive] = useState(rows[0]?.label || '')
  const total = rows.reduce((sum, row) => sum + Number(row[valueKey] || 0), 0) || 1
  const palette = ['#2563eb', '#14b8a6', '#f59e0b', '#7c3aed', '#ef4444', '#06b6d4']
  const stops = rows.map((row, index) => {
    const start = rows.slice(0, index).reduce((sum, item) => sum + (Number(item[valueKey] || 0) / total) * 100, 0)
    const end = start + (Number(row[valueKey] || 0) / total) * 100
    return `${palette[index % palette.length]} ${start}% ${end}%`
  }).join(', ')
  const activeRow = rows.find((row) => row.label === active) || rows[0]

  return (
    <article className="chart-card interactive-chart-card">
      <div className="card-title">
        <span>{subtitle}</span>
        <h2>{title}</h2>
      </div>
      <div className="interactive-donut-layout">
        <div className="interactive-donut" style={{ background: `conic-gradient(${stops || '#e2e8f0 0 100%'})` }}>
          <strong>{activeRow ? formatter(activeRow[valueKey]) : formatter(total)}</strong>
          <span>{activeRow?.label || 'Total'}</span>
        </div>
        <div className="interactive-legend">
          {rows.map((row, index) => (
            <button type="button" className={active === row.label ? 'active' : ''} key={row.label} onMouseEnter={() => setActive(row.label)} onFocus={() => setActive(row.label)}>
              <i style={{ background: palette[index % palette.length] }} />
              <span>{row.label}</span>
              <strong>{formatter(row[valueKey])}</strong>
            </button>
          ))}
        </div>
      </div>
    </article>
  )
}

function AreaTrendChart({ title, subtitle, rows, formatter = formatNumber }) {
  const [activeIndex, setActiveIndex] = useState(rows.length - 1)
  const width = 420
  const height = 190
  const pad = 24
  const max = Math.max(...rows.map((row) => Number(row.value || 0)), 1)
  const points = rows.map((row, index) => {
    const x = rows.length === 1 ? width / 2 : pad + (index / (rows.length - 1)) * (width - pad * 2)
    const y = height - pad - (Number(row.value || 0) / max) * (height - pad * 2)
    return { ...row, x, y }
  })
  const line = points.map((point) => `${point.x},${point.y}`).join(' ')
  const area = points.length ? `${pad},${height - pad} ${line} ${width - pad},${height - pad}` : ''
  const activePoint = points[activeIndex] || points[0]

  return (
    <article className="chart-card interactive-chart-card">
      <div className="card-title">
        <span>{subtitle}</span>
        <h2>{title}</h2>
      </div>
      <div className="area-chart-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
          <polygon points={area} />
          <polyline points={line} />
          {points.map((point, index) => (
            <circle key={`${point.label}-${index}`} cx={point.x} cy={point.y} r={activeIndex === index ? 6 : 4} onMouseEnter={() => setActiveIndex(index)} />
          ))}
        </svg>
        <div className="area-chart-readout">
          <span>{activePoint?.label || 'Trend'}</span>
          <strong>{formatter(activePoint?.value || 0)}</strong>
        </div>
      </div>
    </article>
  )
}

function BubbleCloudChart({ title, subtitle, rows, formatter = formatNumber }) {
  const max = Math.max(...rows.map((row) => Number(row.value || 0)), 1)
  const shortName = (label) => {
    const words = String(label || 'NA').replace(/[^a-zA-Z0-9 ]/g, ' ').split(/\s+/).filter(Boolean)
    if (!words.length) return 'NA'
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
    return words.slice(0, 3).map((word) => word[0]).join('').toUpperCase()
  }

  return (
    <article className="chart-card interactive-chart-card">
      <div className="card-title">
        <span>{subtitle}</span>
        <h2>{title}</h2>
      </div>
      <div className="bubble-panel">
        <div className="bubble-wrap">
          <div className="bubble-cloud">
            {rows.slice(0, 9).map((row, index) => {
              const color = ['#6366f1', '#06b6d4', '#22c55e', '#f59e0b', '#a855f7', '#ec4899'][index % 6]
              const size = 72 + (Number(row.value || 0) / max) * 82
              return (
                <button type="button" className="bubble-cloud-node" key={row.label} style={{ '--bubble-color': color, width: size, height: size }} title={`${row.label}: ${formatter(row.value)}`}>
                  <span className="bubble-rank">{index + 1}</span>
                  <strong>{formatter(row.value)}</strong>
                  <span className="bubble-short">{shortName(row.label)}</span>
                </button>
              )
            })}
          </div>
        </div>
        <div className="bubble-legend-list">
          {rows.slice(0, 9).map((row, index) => {
            const color = ['#6366f1', '#06b6d4', '#22c55e', '#f59e0b', '#a855f7', '#ec4899'][index % 6]
            return (
              <div className="bubble-legend-item" key={`${row.label}-legend`} style={{ '--bubble-color': color }}>
                <span className="bubble-legend-dot" />
                <span className="bubble-legend-label">{row.label}</span>
                <strong>{formatter(row.value)}</strong>
                {row.count ? <em>{row.count} projects</em> : null}
              </div>
            )
          })}
        </div>
      </div>
    </article>
  )
}

function ComparisonTiles({ title, subtitle, rows, formatter = formatNumber }) {
  const total = rows.reduce((sum, row) => sum + Number(row.value || 0), 0) || 1

  return (
    <article className="chart-card interactive-chart-card">
      <div className="card-title">
        <span>{subtitle}</span>
        <h2>{title}</h2>
      </div>
      <div className="comparison-tiles">
        {rows.map((row) => (
          <div key={row.label}>
            <span>{row.label}</span>
            <strong>{formatter(row.value)}</strong>
            <i style={{ width: `${(Number(row.value || 0) / total) * 100}%` }} />
          </div>
        ))}
      </div>
    </article>
  )
}

function RatioCard({ title, items }) {
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

function ProjectsTable({ projects, proposals }) {
  const [mode, setMode] = useState('projects')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('academic_year')
  const [page, setPage] = useState(1)
  const records = mode === 'projects' ? projects : proposals
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
          <span>{mode === 'projects' ? 'Project table' : 'Proposal table'}</span>
          <h2>{mode === 'projects' ? 'Funded Project Records' : 'Research Proposal Records'}</h2>
        </div>
        <div className="books-table-controls">
          <select value={mode} onChange={(event) => { setMode(event.target.value); setPage(1) }}>
            <option value="projects">Projects</option>
            <option value="proposals">Proposals</option>
          </select>
          <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search records" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="academic_year">Sort by year</option>
            <option value="agency">Sort by agency</option>
            <option value="amount">Sort by amount</option>
            <option value="project_status">Sort by status</option>
          </select>
          <button type="button">CSV Export</button>
        </div>
      </div>

      <div className="funding-table">
        <div className="funding-table-head">
          {['Project title', 'Faculty', 'Department', 'School', 'Agency', 'Sanction date', 'Amount', 'Role', 'Project status', 'Academic year'].map((column) => (
            <span key={column}>{column}</span>
          ))}
        </div>
        {pageItems.map((record, index) => (
          <div className="funding-table-row" key={record.id || `${mode}-${index}`}>
            <strong>{record.title || record.project_title || '-'}</strong>
            <span>{record.full_name || record.faculty_name || record.faculty_email || '-'}</span>
            <span>{departmentLabel(record)}</span>
            <span>{record.school || '-'}</span>
            <span>{record.agency || record.funding_agency || '-'}</span>
            <span>{record.sanction_date || '-'}</span>
            <span>{money(record.amount || record.sanctioned_amount)}</span>
            <span>{normalizeRole(record.role)}</span>
            <span>{normalizeStatus(record.project_status || record.status)}</span>
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

function buildMockProjects() {
  return mockResearchAnalytics.faculty.items.flatMap((faculty) =>
    Array.from({ length: faculty.research_projects || 0 }).map((_, index) => ({
      id: `${faculty.faculty_id}-project-${index}`,
      faculty_email: faculty.email,
      full_name: faculty.faculty_name,
      school: faculty.school,
      department: faculty.department,
      title: ['AI enabled research analytics', 'Outcome based appraisal mining', 'Institutional data quality monitor'][index % 3],
      agency: ['AICTE', 'DST', 'Industry Sponsored'][index % 3],
      sanction_date: `202${index + 3}-09-15`,
      amount: Math.round((faculty.total_funding || 1000000) / Math.max(faculty.research_projects || 1, 1)),
      role: index % 2 ? 'Co-Investigator' : 'Principal Investigator',
      project_status: ['Ongoing', 'Completed', 'Sanctioned'][index % 3],
      academic_year: `202${index + 3}-202${index + 4}`,
      score: 10 + index,
      vc_score: 9 + index,
      external_project: index % 2 === 0,
    })),
  )
}

function buildMockProposals(projects) {
  return projects.map((project, index) => ({
    ...project,
    id: `${project.id}-proposal`,
    title: `${project.title} Proposal`,
    amount: Math.round(Number(project.amount || 0) * 1.2),
    project_status: index % 3 ? 'Submitted' : 'Rejected',
  }))
}

export default function ProjectsFundingAnalyticsPage({ sharedData, filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Funding Overview')
  const [projectResponse, setProjectResponse] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadProjects() {
      setLoading((current) => current)
      setError('')
      try {
        const response = await researchAnalyticsApi.projectRecords(filters)
        if (!ignore) setProjectResponse(response)
      } catch (requestError) {
        if (!ignore) {
          const mockRows = buildMockProjects()
          setProjectResponse({ items: mockRows, total: mockRows.length })
          setError(`${requestError.message} Showing demo projects and funding analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadProjects()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const projects = useMemo(() => projectResponse.items || [], [projectResponse.items])
  const proposals = useMemo(() => buildMockProposals(projects), [projects])
  const activeFaculty = sharedData.overview?.total_active_faculty || sharedData.overview?.total_faculty || 0
  const fundedProjects = projects.filter((record) => Number(record.amount || record.sanctioned_amount || 0) > 0)
  const totalSanctioned = sumAmount(fundedProjects)
  const totalProposed = sumAmount(proposals)
  const externalProjects = projects.filter((record) => record.external_project || String(record.project_type || '').toLowerCase().includes('external') || String(record.agency || '').toLowerCase().includes('industry'))
  const externalFunding = sumAmount(externalProjects)
  const fundedFaculty = new Set(fundedProjects.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const proposalFaculty = new Set(proposals.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const projectFaculty = new Set(projects.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const piCount = new Set(projects.filter((record) => normalizeRole(record.role) === 'Principal Investigator').map((record) => record.faculty_email)).size
  const ongoing = projects.filter((record) => normalizeStatus(record.project_status) === 'Ongoing').length
  const completed = projects.filter((record) => normalizeStatus(record.project_status) === 'Completed').length
  const sanctioned = projects.filter((record) => ['Sanctioned', 'Ongoing', 'Completed'].includes(normalizeStatus(record.project_status))).length
  const proposalToProject = proposals.length ? (sanctioned / proposals.length) * 100 : 0
  const externalFundingPct = totalSanctioned ? (externalFunding / totalSanctioned) * 100 : 0
  const avgProjectAmount = fundedProjects.length ? totalSanctioned / fundedProjects.length : 0
  const avgProposalAmount = proposals.length ? totalProposed / proposals.length : 0
  const fundingPerActive = activeFaculty ? totalSanctioned / activeFaculty : 0
  const fundingPerFunded = fundedFaculty.size ? totalSanctioned / fundedFaculty.size : 0

  const departmentFunding = Object.entries(groupBy(projects, (record) => departmentLabel(record))).map(([label, rows]) => ({ label, value: sumAmount(rows), count: rows.length })).sort((a, b) => b.value - a.value)
  const schoolFunding = Object.entries(groupBy(projects, (record) => record.school)).map(([label, rows]) => ({ label, value: sumAmount(rows), count: rows.length })).sort((a, b) => b.value - a.value)
  const facultyFunding = Object.entries(groupBy(projects, (record) => record.faculty_email)).map(([email, rows]) => ({ label: rows[0]?.full_name || email, value: sumAmount(rows), count: rows.length })).sort((a, b) => b.value - a.value)
  const agencyFunding = Object.entries(groupBy(projects, (record) => record.agency || record.funding_agency)).map(([label, rows]) => ({ label, value: sumAmount(rows), count: rows.length })).sort((a, b) => b.value - a.value)
  const statusRows = Object.entries(groupBy(projects, (record) => normalizeStatus(record.project_status))).map(([label, rows]) => ({ label, value: rows.length }))
  const trendRows = Object.entries(groupBy(projects, (record) => String(record.sanction_date || record.academic_year || '').slice(0, 4))).map(([label, rows]) => ({ label, value: sumAmount(rows) }))
  const proposalTrendRows = Object.entries(groupBy(proposals, (record) => record.academic_year)).map(([label, rows]) => ({ label, value: rows.length }))
  const topFiveFacultyShare = totalSanctioned ? (facultyFunding.slice(0, 5).reduce((sum, row) => sum + row.value, 0) / totalSanctioned) * 100 : 0
  const topFiveDepartmentShare = totalSanctioned ? (departmentFunding.slice(0, 5).reduce((sum, row) => sum + row.value, 0) / totalSanctioned) * 100 : 0
  const departmentsWithProposalsNoProjects = [...new Set(proposals.map((record) => record.department).filter(Boolean))].filter((department) => !departmentFunding.some((row) => row.label === department)).length
  const facultyWithProposalsNoProjects = [...proposalFaculty].filter((email) => !projectFaculty.has(email)).length
  const schoolsWithNoExternal = (options?.schools || []).filter((school) => !externalProjects.some((record) => record.school === school)).length

  const primaryKpis = [
    { label: 'Total Sanctioned Funding', value: money(totalSanctioned), icon: 'INR', subtext: `${formatNumber(fundedProjects.length)} funded records` },
    { label: 'Total Proposed Funding', value: money(totalProposed), icon: 'PF', subtext: `${formatNumber(proposals.length)} proposals` },
    { label: 'Funded Project Count', value: formatNumber(fundedProjects.length), icon: 'FC', subtext: 'Projects with amount' },
    { label: 'Proposal Count', value: formatNumber(proposals.length), icon: 'PC', subtext: 'Approximate proposal records' },
    { label: 'Average Project Amount', value: money(avgProjectAmount), icon: 'AVG', subtext: 'Sanctioned / funded count' },
    { label: 'External Funding Percentage', value: percent(externalFundingPct), icon: 'EXT', subtext: 'External / total funding' },
  ]

  return (
    <main className="research-page funding-page">
      <PageHeader
        title="Projects and Funding Analytics"
        description="Sanctioned research projects, external funding, proposals, agencies, and faculty funding concentration"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}

      <div className="data-limitation-notice">
        <strong>Approximate metric</strong>
        <span>Proposal-to-Project Indicator is approximate because proposals and projects do not share a proposal identifier.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading funding analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={[
            { label: 'Funding per active faculty', value: money(fundingPerActive) },
            { label: 'Faculty receiving project funding', value: fundedFaculty.size },
            { label: 'Principal investigator count', value: piCount },
            { label: 'Ongoing projects', value: ongoing },
            { label: 'Completed projects', value: completed },
            { label: 'Proposal-to-project indicator', value: percent(proposalToProject) },
            { label: 'Funding per funded faculty', value: money(fundingPerFunded) },
            { label: 'Average proposal amount', value: money(avgProposalAmount) },
          ]} />

          <nav className="page-tabs" aria-label="Projects and funding tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Funding Overview' && (
            <>
              <div className="stat-rings-row">
                <StatRing value={proposalToProject} label="Proposal to Project" color="#22c55e" />
                <StatRing value={externalFundingPct} label="External Funding" color="#06b6d4" />
                <StatRing value={topFiveFacultyShare} label="Top 5 Faculty Share" color="#f59e0b" />
                <SparklineRow values={trendRows.map((row) => Number(row.value || 0))} color="#06b6d4" label="Funding trend" />
              </div>
              <section className="executive-chart-row two-col">
                <BubbleCloudChart title="Which departments receive the most sanctioned funding" subtitle="Sanctioned amount by department" rows={departmentFunding} formatter={money} />
                <DonutChart title="How sanctioned funding is distributed by school" subtitle="School funding share" rows={schoolFunding} formatter={money} />
                <RankingList title="Which agencies sanction the most funding" subtitle="Agency funding concentration" rows={agencyFunding} formatter={money} badgeKey="count" badgeFormatter={formatNumber} />
                <ComparisonTiles title="Funding source split: internal versus external" subtitle="Sanctioned project funding source" rows={[
                  { label: 'Internal / unspecified', value: Math.max(totalSanctioned - externalFunding, 0) },
                  { label: 'External', value: externalFunding },
                ]} formatter={money} />
                <AreaTrendChart title="How sanctioned funding changed by sanction year" subtitle="Year-wise sanctioned amount" rows={trendRows} formatter={money} />
                <RatioCard title="Funding concentration" items={[
                  { label: 'Top five faculty funding share', value: percent(topFiveFacultyShare) },
                  { label: 'Top five department funding share', value: percent(topFiveDepartmentShare) },
                  { label: 'Highest funded faculty', value: facultyFunding[0]?.label || '-' },
                  { label: 'Year-over-year funding growth', value: 'Needs yearly backend baseline' },
                ]} />
              </section>
            </>
          )}

          {activeTab === 'Research Projects' && (
            <section className="executive-chart-row two-col">
              <DonutChart title="How projects are distributed by normalized status" subtitle="Project lifecycle status" rows={statusRows} />
              <MiniBarChart title="Which faculty receive the most sanctioned project funding" subtitle="Faculty funding ranking" rows={facultyFunding} formatter={money} />
              <RatioCard title="Project health" items={[
                { label: 'Ongoing projects', value: ongoing },
                { label: 'Completed projects', value: completed },
                { label: 'Ongoing vs completed ratio', value: completed ? `${(ongoing / completed).toFixed(2)}:1` : 'N/A' },
                { label: 'PI participation', value: piCount },
              ]} />
            </section>
          )}

          {activeTab === 'External Projects' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Which agencies provide the most external funding" subtitle="External project amount by agency" rows={Object.entries(groupBy(externalProjects, (record) => record.agency)).map(([label, rows]) => ({ label, value: sumAmount(rows) }))} formatter={money} />
              <MiniBarChart title="Which schools receive the most external funding" subtitle="External project amount by school" rows={Object.entries(groupBy(externalProjects, (record) => record.school)).map(([label, rows]) => ({ label, value: sumAmount(rows) }))} formatter={money} />
              <RatioCard title="External project gaps" items={[
                { label: 'External funding percentage', value: percent(externalFundingPct) },
                { label: 'Schools with no external projects', value: schoolsWithNoExternal },
              ]} />
            </section>
          )}

          {activeTab === 'Proposals' && (
            <section className="executive-chart-row two-col">
              <AreaTrendChart title="How proposed funding activity changed by academic year" subtitle="Proposal count trend" rows={proposalTrendRows} />
              <BubbleCloudChart title="Which agencies receive the largest proposed funding requests" subtitle="Proposal amount by agency" rows={Object.entries(groupBy(proposals, (record) => record.agency)).map(([label, rows]) => ({ label, value: sumAmount(rows), count: rows.length }))} formatter={money} />
              <RatioCard title="Proposal conversion indicators" items={[
                { label: 'Proposal-to-project indicator', value: percent(proposalToProject) },
                { label: 'Departments with proposals but no funded projects', value: departmentsWithProposalsNoProjects },
                { label: 'Faculty with proposals but no funded projects', value: facultyWithProposalsNoProjects },
              ]} />
            </section>
          )}

          {activeTab === 'Funding Agencies' && (
            <section className="executive-chart-row two-col">
              <RankingList title="Agencies ranked by sanctioned funding amount" subtitle="Funding amount and project count" rows={agencyFunding} formatter={money} badgeKey="count" badgeFormatter={formatNumber} />
              <DonutChart title="Agency share by funded project count" subtitle="Number of funded projects" rows={agencyFunding} valueKey="count" />
            </section>
          )}

          {activeTab === 'Faculty and Department Funding' && (
            <section className="executive-chart-row two-col">
              <RankingList title="Faculty ranked by sanctioned funding received" subtitle="Faculty funding leaderboard" rows={facultyFunding} formatter={money} />
              <MiniBarChart title="Sanctioned funding amount by faculty" subtitle="Faculty funding comparison" rows={facultyFunding} formatter={money} />
              <MiniBarChart title="Sanctioned funding amount by department" subtitle="Department funding comparison" rows={departmentFunding} formatter={money} />
              <RatioCard title="Participation and role analytics" items={[
                { label: 'Faculty receiving funding', value: fundedFaculty.size },
                { label: 'Principal investigators', value: piCount },
                { label: 'Co-investigator/team members', value: projects.filter((record) => normalizeRole(record.role) !== 'Principal Investigator').length },
                { label: 'Funding per funded faculty', value: money(fundingPerFunded) },
              ]} />
            </section>
          )}

          <ProjectsTable projects={projects} proposals={proposals} />
        </>
      )}
    </main>
  )
}
