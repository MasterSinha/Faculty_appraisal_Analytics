import { useEffect, useState } from 'react'
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

const tabs = ['Institutional Funnel', 'Department Funnel', 'Faculty Innovation', 'Academic-Year Trend', 'Pipeline Gaps']
const stageLabels = ['Research Proposals', 'Sanctioned Projects', 'Patent or IPR', 'Granted Patents', 'Products Developed']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function isGranted(value) {
  return String(value || '').toLowerCase().includes('grant')
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Unknown'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function byCount(records, keyGetter) {
  return Object.entries(groupBy(records, keyGetter))
    .map(([label, rows]) => ({ label, value: rows.length }))
    .sort((a, b) => b.value - a.value)
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('year') || context.includes('trend')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('school') || context.includes('comparison')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('faculty') || context.includes('diversity')) return <BubbleCloudChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
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

function FunnelChart({ stages }) {
  const max = Math.max(...stages.map((stage) => stage.value), 1)

  return (
    <article className="chart-card pipeline-funnel-card">
      <div className="card-title">
        <span>Aggregate funnel</span>
        <h2>Institutional innovation pipeline</h2>
      </div>
      <div className="pipeline-funnel">
        {stages.map((stage, index) => {
          const previous = stages[index - 1]?.value
          const change = previous ? ((stage.value - previous) / previous) * 100 : 0
          return (
            <div className="pipeline-stage" key={stage.label}>
              <div className="pipeline-stage-bar" style={{ width: `${Math.max((stage.value / max) * 100, 8)}%` }}>
                <span>{stage.label}</span>
                <strong>{formatNumber(stage.value)}</strong>
              </div>
              <em>{index === 0 ? 'Baseline count' : `${percent(change)} from previous stage`}</em>
            </div>
          )
        })}
      </div>
    </article>
  )
}

function buildMockPipeline() {
  const faculty = mockResearchAnalytics.faculty.items
  const proposals = faculty.slice(0, 18).map((item, index) => ({
    id: `${item.faculty_id}-proposal-${index}`,
    faculty_email: item.email,
    full_name: item.faculty_name,
    school: item.school,
    department: item.department,
    academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
    amount: 500000 + (index * 90000),
  }))
  const projects = faculty.flatMap((item) =>
    Array.from({ length: item.research_projects || 0 }).map((_, index) => ({
      id: `${item.faculty_id}-project-${index}`,
      faculty_email: item.email,
      full_name: item.faculty_name,
      school: item.school,
      department: item.department,
      academic_year: `202${index + 3}-202${index + 4}`,
      amount: item.total_funding || 0,
      status: index % 2 ? 'Ongoing' : 'Sanctioned',
      external_project: index % 2 === 0,
    })),
  )
  const patents = faculty.slice(0, 12).map((item, index) => ({
    id: `${item.faculty_id}-patent-${index}`,
    faculty_email: item.email,
    full_name: item.faculty_name,
    school: item.school,
    department: item.department,
    academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
    status: index % 3 === 0 ? 'Granted' : 'Published',
  }))
  const ipr = faculty.slice(4, 14).map((item, index) => ({
    id: `${item.faculty_id}-ipr-${index}`,
    faculty_email: item.email,
    full_name: item.faculty_name,
    school: item.school,
    department: item.department,
    academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
    status: index % 2 ? 'Registered' : 'Filed',
  }))
  const products = faculty.slice(0, 7).map((item, index) => ({
    id: `${item.faculty_id}-product-${index}`,
    faculty_email: item.email,
    full_name: item.faculty_name,
    school: item.school,
    department: item.department,
    academic_year: `202${index % 3 + 3}-202${index % 3 + 4}`,
    title: ['Research dashboard', 'Patent workflow tool', 'AI appraisal module'][index % 3],
  }))
  return { proposals, projects, external_projects: projects.filter((project) => project.external_project), patents, ipr_records: ipr, products_developed: products }
}

export default function InnovationPipelinePage({ sharedData, filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Institutional Funnel')
  const [response, setResponse] = useState(buildMockPipeline())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadPipeline() {
      setLoading(true)
      setError('')
      try {
        const data = await researchAnalyticsApi.innovationPipeline(filters)
        if (!ignore) setResponse({
          proposals: data.proposals || data.research_proposals || [],
          projects: data.projects || data.research_projects || [],
          external_projects: data.external_projects || data.external_research_projects || [],
          patents: data.patents || [],
          ipr_records: data.ipr_records || data.ipr || [],
          products_developed: data.products_developed || data.products || [],
        })
      } catch (requestError) {
        if (!ignore) {
          setResponse(buildMockPipeline())
          setError(`${requestError.message} Showing demo innovation pipeline analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadPipeline()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const proposals = response.proposals || []
  const projects = response.projects || []
  const externalProjects = response.external_projects || []
  const patents = response.patents || []
  const iprRecords = response.ipr_records || []
  const products = response.products_developed || []
  const patentIpr = [...patents, ...iprRecords]
  const grantedPatents = patents.filter((patent) => isGranted(patent.status || patent.patent_status))
  const innovationFaculty = new Set([...proposals, ...projects, ...externalProjects, ...patentIpr, ...products].map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const stages = [
    { label: stageLabels[0], value: proposals.length },
    { label: stageLabels[1], value: projects.length },
    { label: stageLabels[2], value: patentIpr.length },
    { label: stageLabels[3], value: grantedPatents.length },
    { label: stageLabels[4], value: products.length },
  ]

  const facultyCategoryMap = (() => {
    const map = new Map()
    ;[
      [proposals, 'proposals'],
      [projects, 'projects'],
      [patentIpr, 'patentIpr'],
      [grantedPatents, 'granted'],
      [products, 'products'],
    ].forEach(([records, category]) => {
      records.forEach((record) => {
        const email = String(record.faculty_email || '').toLowerCase()
        if (!email) return
        const entry = map.get(email) || { label: record.full_name || record.faculty_name || email, value: 0, categories: new Set() }
        entry.categories.add(category)
        entry.value = entry.categories.size
        map.set(email, entry)
      })
    })
    return [...map.values()].sort((a, b) => b.value - a.value)
  })()

  const departmentRows = byCount([...proposals, ...projects, ...patentIpr, ...products], (record) => departmentLabel(record))
  const schoolRows = byCount([...proposals, ...projects, ...patentIpr, ...products], (record) => record.school)
  const yearRows = Object.entries(groupBy([...proposals, ...projects, ...patentIpr, ...products], (record) => record.academic_year))
    .map(([label, rows]) => ({ label, value: rows.length }))
    .sort((a, b) => String(a.label).localeCompare(String(b.label)))
  const projectDepartments = new Set(projects.map((record) => departmentLabel(record)).filter(Boolean))
  const patentDepartments = new Set(patentIpr.map((record) => departmentLabel(record)).filter(Boolean))
  const productDepartments = new Set(products.map((record) => departmentLabel(record)).filter(Boolean))
  const projectSchools = new Set(externalProjects.map((record) => record.school).filter(Boolean))
  const allSchools = new Set((sharedData.faculty?.items || []).map((faculty) => faculty.school).filter(Boolean))
  const patentFaculty = new Set(patentIpr.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const productFaculty = new Set(products.map((record) => String(record.faculty_email || '').toLowerCase()).filter(Boolean))
  const strongFundingWeakProducts = Object.entries(groupBy(projects, (record) => departmentLabel(record))).filter(([department, rows]) => {
    const amount = rows.reduce((sum, row) => sum + Number(row.amount || row.sanctioned_amount || 0), 0)
    return amount >= 1000000 && !productDepartments.has(department)
  }).length
  const gapItems = [
    { label: 'Proposals without corresponding aggregate project activity', value: Math.max(proposals.length - projects.length, 0) },
    { label: 'Departments with projects but no patents', value: [...projectDepartments].filter((department) => !patentDepartments.has(department)).length },
    { label: 'Faculty with patents but no products', value: [...patentFaculty].filter((email) => !productFaculty.has(email)).length },
    { label: 'Departments with no products developed', value: departmentRows.filter((row) => !productDepartments.has(row.label)).length },
    { label: 'Schools with no external projects', value: [...allSchools].filter((school) => !projectSchools.has(school)).length },
    { label: 'Faculty active in three or more innovation categories', value: facultyCategoryMap.filter((faculty) => faculty.value >= 3).length },
    { label: 'Strong project funding but weak product output departments', value: strongFundingWeakProducts },
  ]

  const primaryKpis = [
    { label: 'Proposals Submitted', value: formatNumber(proposals.length), icon: 'RP', subtext: 'Research proposals' },
    { label: 'Projects Sanctioned', value: formatNumber(projects.length), icon: 'PS', subtext: 'Sanctioned or active projects' },
    { label: 'Patent or IPR Records', value: formatNumber(patentIpr.length), icon: 'IP', subtext: 'Patent + IPR records' },
    { label: 'Patents Granted', value: formatNumber(grantedPatents.length), icon: 'PG', subtext: 'Granted patent status' },
    { label: 'Products Developed', value: formatNumber(products.length), icon: 'PD', subtext: 'Product records' },
    { label: 'Innovation-Active Faculty', value: formatNumber(innovationFaculty.size), icon: 'IA', subtext: 'Any pipeline category' },
  ]

  return (
    <main className="research-page pipeline-page">
      <PageHeader
        title="Innovation Pipeline"
        description="Aggregate proposal, project, patent, IPR, and product development activity"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />

      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />

      {error && <div className="notice-banner"><strong>{error}</strong></div>}
      <div className="data-limitation-notice">
        <strong>Important limitation</strong>
        <span>Pipeline stages represent aggregate institutional counts. Existing database records do not contain a shared innovation identifier, so individual proposals cannot be followed reliably through every stage.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading innovation pipeline">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={gapItems.slice(0, 5)} />

          <nav className="page-tabs" aria-label="Innovation pipeline tabs">
            {tabs.map((tab) => (
              <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>
                {tab}
              </button>
            ))}
          </nav>

          {activeTab === 'Institutional Funnel' && (
            <section className="executive-chart-row two-col">
              <FunnelChart stages={stages} />
              <MiniBarChart title="Innovation activity by school" subtitle="School contribution" rows={schoolRows} />
              <MiniBarChart title="Pipeline stages by department" subtitle="Department contribution" rows={departmentRows} />
              <MiniBarChart title="Academic-year pipeline trend" subtitle="Year comparison" rows={yearRows} />
            </section>
          )}

          {activeTab === 'Department Funnel' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Pipeline stages by department" subtitle="All innovation categories" rows={departmentRows} />
              <InsightCard title="Department pipeline gaps" items={gapItems.filter((item) => item.label.includes('Departments') || item.label.includes('funding'))} />
            </section>
          )}

          {activeTab === 'Faculty Innovation' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Faculty innovation diversity" subtitle="Categories active" rows={facultyCategoryMap} />
              <InsightCard title="Faculty innovation profile" items={[
                { label: 'Innovation-active faculty', value: innovationFaculty.size },
                { label: 'Faculty active in three or more categories', value: facultyCategoryMap.filter((faculty) => faculty.value >= 3).length },
                { label: 'Faculty with patents but no products', value: [...patentFaculty].filter((email) => !productFaculty.has(email)).length },
              ]} />
            </section>
          )}

          {activeTab === 'Academic-Year Trend' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Academic-year pipeline trend" subtitle="All stages" rows={yearRows} />
              <MiniBarChart title="Academic-year comparison" subtitle="Proposal baseline" rows={byCount(proposals, (record) => record.academic_year)} />
            </section>
          )}

          {activeTab === 'Pipeline Gaps' && (
            <section className="executive-chart-row two-col">
              <InsightCard title="Gap analytics" items={gapItems} />
              <MiniBarChart title="Departments with product output" subtitle="Products developed" rows={byCount(products, (record) => departmentLabel(record))} />
            </section>
          )}
        </>
      )}
    </main>
  )
}
