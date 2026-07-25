import { useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import InsightPanel from '../components/research-analytics/InsightPanel'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import PublicationTrendChart from '../components/research-analytics/PublicationTrendChart'
import Sidebar from '../components/research-analytics/Sidebar'
import { useResearchAnalytics } from '../hooks/useResearchAnalytics'
import AppraisalCompletionAnalyticsPage from './AppraisalCompletionAnalyticsPage'
import BooksAnalyticsPage from './BooksAnalyticsPage'
import ConferencesAwardsAnalyticsPage from './ConferencesAwardsAnalyticsPage'
import DepartmentResearchPerformancePage from './DepartmentResearchPerformancePage'
import FacultyResearchPerformancePage from './FacultyResearchPerformancePage'
import InnovationPipelinePage from './InnovationPipelinePage'
import JournalPublicationsAnalyticsPage from './JournalPublicationsAnalyticsPage'
import PatentsIprAnalyticsPage from './PatentsIprAnalyticsPage'
import ProjectsFundingAnalyticsPage from './ProjectsFundingAnalyticsPage'
import ResearchDataQualityPage from './ResearchDataQualityPage'
import ResearchGuidanceAnalyticsPage from './ResearchGuidanceAnalyticsPage'
import SchoolResearchPerformancePage from './SchoolResearchPerformancePage'
import TeachingResearchAnalyticsPage from './TeachingResearchAnalyticsPage'

function formatInr(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function HorizontalMetricChart({ title, eyebrow, rows, valueKey, labelKey = 'department', formatter = (value) => value }) {
  const max = Math.max(...rows.map((row) => Number(row[valueKey] || 0)), 1)

  return (
    <article className="chart-card executive-chart-card">
      <div className="card-title">
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      <div className="executive-bars">
        {rows.length ? rows.slice(0, 8).map((row) => {
          const value = Number(row[valueKey] || 0)
          return (
            <div className="executive-bar-row" key={`${row[labelKey]}-${title}`}>
              <span>{row[labelKey] || 'Unknown'}</span>
              <div><i style={{ width: `${(value / max) * 100}%` }} /></div>
              <strong>{formatter(value)}</strong>
            </div>
          )
        }) : (
          <div className="mini-empty">No data available</div>
        )}
      </div>
    </article>
  )
}

function CategoryOutputChart({ data }) {
  return (
    <article className="chart-card executive-chart-card">
      <div className="card-title">
        <span>Research output</span>
        <h2>Output by category</h2>
      </div>
      <div className="category-stack">
        {data.map((item) => (
          <div className="category-row" key={item.indexing}>
            <span>{item.indexing}</span>
            <strong>{item.total_papers || 0}</strong>
          </div>
        ))}
      </div>
    </article>
  )
}

function PatentStatusCard({ overview }) {
  const granted = Number(overview?.patents_granted || 0)
  const total = Number(overview?.total_patents || 0)
  const pending = Math.max(total - granted, 0)
  const grantedShare = total ? (granted / total) * 100 : 0

  return (
    <article className="chart-card executive-chart-card">
      <div className="card-title">
        <span>Innovation</span>
        <h2>Patent status distribution</h2>
      </div>
      <div className="patent-donut-wrap">
        <div
          className="patent-donut"
          style={{ background: `conic-gradient(var(--green) 0 ${grantedShare}%, var(--amber) 0 100%)` }}
        >
          <strong>{percent(grantedShare)}</strong>
          <span>granted</span>
        </div>
        <div className="status-legend">
          <span><i className="green-dot" /> Granted <strong>{granted}</strong></span>
          <span><i className="amber-dot" /> Pending / filed <strong>{pending}</strong></span>
        </div>
      </div>
    </article>
  )
}

function ManagementAttentionPanel({ alerts }) {
  return (
    <section className="attention-section">
      <div className="section-title">
        <span>Management attention</span>
        <h2>Priority follow-ups</h2>
      </div>
      <div className="attention-grid">
        {alerts.slice(0, 5).map((alert, index) => (
          <article className={`attention-card ${alert.severity || 'warning'}`} key={`${alert.title}-${index}`}>
            <div>
              <strong>{alert.title}</strong>
              <p>{alert.message}</p>
            </div>
            <button type="button">{alert.linkLabel || 'Drill down'}</button>
          </article>
        ))}
      </div>
    </section>
  )
}

export default function ResearchAnalyticsDashboard() {
  const { data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx } = useResearchAnalytics()
  const [activePage, setActivePage] = useState('overview')

  if (activePage === 'books') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <BooksAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'publications') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <JournalPublicationsAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'patents') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <PatentsIprAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'projects') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <ProjectsFundingAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'guidance') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <ResearchGuidanceAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'conferences') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <ConferencesAwardsAnalyticsPage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'pipeline') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <InnovationPipelinePage
          sharedData={data}
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'faculty-performance') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <FacultyResearchPerformancePage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'department-performance') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <DepartmentResearchPerformancePage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'school-performance') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <SchoolResearchPerformancePage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'teaching-balance') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <TeachingResearchAnalyticsPage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'completion') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <AppraisalCompletionAnalyticsPage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  if (activePage === 'data-quality') {
    return (
      <div className="analytics-shell executive-shell">
        <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />
        <ResearchDataQualityPage
          filters={filters}
          updateFilters={updateFilters}
          refresh={refresh}
          exportCsv={exportCsv}
          exportXlsx={exportXlsx}
          options={data.filterOptions}
        />
      </div>
    )
  }

  function handleResetFilters() {
    updateFilters({
      page: 1,
      page_size: 10,
      search: '',
      school: '',
      department: '',
      designation: '',
      category: '',
      indexing: '',
      year: '',
      sort_by: 'total_research_papers',
      sort_order: 'desc',
    })
  }

  const overview = data.overview || {}
  const departments = data.departments?.items || []
  const activeFaculty = overview.total_active_faculty || overview.total_faculty || 0
  const publishingFaculty = overview.faculty_with_journal_publication || overview.faculty_with_research || 0
  const participationRate = overview.publication_participation_rate || ((publishingFaculty / (activeFaculty || 1)) * 100)
  const inactiveResearchers = Math.max(activeFaculty - publishingFaculty, 0)
  const categoryCount = [
    overview.total_journal_publications || overview.total_research_papers,
    overview.total_book_publications || overview.total_books,
    overview.total_patents,
    overview.total_research_projects || overview.total_projects,
    overview.total_research_proposals,
    overview.total_research_scholars_guided,
    overview.total_conferences,
    overview.total_awards,
    overview.total_products_developed,
  ].filter((value) => Number(value || 0) > 0).length
  const diversityScore = activeFaculty ? categoryCount / activeFaculty : 0

  const primaryKpis = [
    { label: 'Active Faculty', value: activeFaculty, icon: 'AF', subtext: `${publishingFaculty} publishing faculty` },
    { label: 'Journal Publications', value: overview.total_journal_publications || overview.total_research_papers || 0, icon: 'JP', subtext: 'Valid journal records' },
    { label: 'Participation Rate', value: percent(participationRate), icon: 'PR', subtext: 'Faculty with publications' },
    { label: 'Total Patents', value: overview.total_patents || 0, icon: 'PT', subtext: `${overview.patents_granted || 0} granted` },
    { label: 'Sanctioned Funding', value: formatInr(overview.total_sanctioned_funding || overview.total_funding), icon: 'INR', subtext: 'Projects and external grants' },
    { label: 'Avg Diversity Score', value: diversityScore.toFixed(2), icon: 'DS', subtext: 'Categories per active faculty' },
  ]

  const secondaryKpis = [
    { label: 'Books Published', value: overview.total_book_publications || overview.total_books || 0 },
    { label: 'Patents Granted', value: overview.patents_granted || 0 },
    { label: 'Research Proposals', value: overview.total_research_proposals || 0 },
    { label: 'Students Guided', value: overview.total_research_scholars_guided || 0 },
    { label: 'Conferences', value: overview.total_conferences || 0 },
    { label: 'Awards', value: overview.total_awards || 0 },
    { label: 'Products Developed', value: overview.total_products_developed || 0 },
    { label: 'Faculty with No Research Activity', value: inactiveResearchers },
  ]

  const dynamicInsights = (data.insights || []).slice(0, 5).map((item) => ({
    title: 'Research Insight',
    explanation: item,
    supporting_metric: 'Calculated from live analytics',
    severity: 'neutral',
  }))

  const fallbackInsights = [
    {
      title: 'Publication Participation',
      explanation: `${percent(participationRate)} of active faculty have at least one journal publication.`,
      supporting_metric: `${publishingFaculty} of ${activeFaculty} active faculty`,
      severity: participationRate >= 50 ? 'positive' : 'warning',
    },
    {
      title: 'Research Funding',
      explanation: `Institutional sanctioned funding is ${formatInr(overview.total_sanctioned_funding || overview.total_funding)}.`,
      supporting_metric: `${formatInr(overview.funding_per_active_faculty || 0)} per active faculty`,
      severity: 'positive',
    },
    {
      title: 'Inactive Researchers',
      explanation: `${inactiveResearchers} active faculty currently show no journal publication contribution.`,
      supporting_metric: `${percent((inactiveResearchers / (activeFaculty || 1)) * 100)} inactive by publication`,
      severity: inactiveResearchers > 0 ? 'warning' : 'positive',
    },
  ]

  const lowParticipationDepartments = departments.filter((dept) => Number(dept.publication_participation_percentage || 0) < 30)
  const noPatentDepartments = departments.filter((dept) => Number(dept.patents || 0) === 0)
  const incompleteRecords = Object.values(data.dataQuality || {}).reduce((sum, value) => sum + Number(value || 0), 0)
  const alerts = [
    lowParticipationDepartments.length > 0 && {
      title: 'Low participation departments',
      message: `${lowParticipationDepartments.length} departments are below 30% publication participation.`,
      linkLabel: 'View department analytics',
      severity: 'warning',
    },
    noPatentDepartments.length > 0 && {
      title: 'No patents or IPR',
      message: `${noPatentDepartments.length} departments have no patent/IPR contribution in the selected filters.`,
      linkLabel: 'Open innovation view',
      severity: 'warning',
    },
    incompleteRecords > 0 && {
      title: 'Incomplete research records',
      message: `${incompleteRecords} data-quality issues require verification before final reporting.`,
      linkLabel: 'Review data quality',
      severity: 'risk',
    },
    inactiveResearchers > 0 && {
      title: 'Inactive research contribution',
      message: `${inactiveResearchers} active faculty have no publication activity in the current overview.`,
      linkLabel: 'View faculty list',
      severity: 'warning',
    },
  ].filter(Boolean)

  return (
    <div className="analytics-shell executive-shell">
      <Sidebar activePage={activePage} onPageSelect={setActivePage} mobileOpen={false} onMobileClose={() => {}} />

      <main className="research-page executive-page">
        <PageHeader
          title="Research Analytics Overview"
          description="Institutional research performance, participation, innovation, and funding summary"
          lastRefreshed="Just now"
          onRefresh={refresh}
          onExportCsv={exportCsv}
          onExportXlsx={exportXlsx}
          onMobileMenuToggle={() => {}}
        />

        <FilterBar
          filters={filters}
          options={data.filterOptions}
          onChange={updateFilters}
          onReset={handleResetFilters}
        />

        {error && !loading && (
          <div className={demoMode ? 'notice-banner' : 'error-banner'}>
            <strong>{error}</strong>
          </div>
        )}

        {loading ? (
          <section className="skeleton-grid" aria-label="Loading analytics">
            {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
          </section>
        ) : (
          <>
            <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={secondaryKpis} />

            <InsightPanel insights={dynamicInsights.length ? dynamicInsights : fallbackInsights} />

            <section className="executive-chart-row two-col">
              <CategoryOutputChart data={data.indexing || []} />
              <PublicationTrendChart data={data.trend || []} />
            </section>

            <section className="executive-chart-row two-col">
              <HorizontalMetricChart
                title="Publications by department"
                eyebrow="Department analytics"
                rows={departments}
                valueKey="journal_publications"
              />
              <HorizontalMetricChart
                title="Participation rate by department"
                eyebrow="Faculty participation"
                rows={departments}
                valueKey="publication_participation_percentage"
                formatter={(value) => percent(value)}
              />
            </section>

            <section className="executive-chart-row two-col">
              <HorizontalMetricChart
                title="Research funding by department"
                eyebrow="Project funding"
                rows={departments}
                valueKey="total_project_funding"
                formatter={formatInr}
              />
              <PatentStatusCard overview={overview} />
            </section>

            <ManagementAttentionPanel alerts={alerts.length ? alerts : [{
              title: 'No immediate alerts',
              message: 'No major management attention items were detected for the selected filters.',
              linkLabel: 'Continue monitoring',
              severity: 'positive',
            }]} />
          </>
        )}
      </main>
    </div>
  )
}
