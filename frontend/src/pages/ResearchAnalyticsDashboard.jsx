import { useEffect, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import InsightPanel from '../components/research-analytics/InsightPanel'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import Sidebar from '../components/research-analytics/Sidebar'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import ComparisonTiles from '../components/research-analytics/charts/ComparisonTiles'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HeatmapChart from '../components/research-analytics/charts/HeatmapChart'
import RadarChart from '../components/research-analytics/charts/RadarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import StatRing from '../components/research-analytics/charts/StatRing'
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

/* ── Formatters ─────────────────────────────────────────── */
function fmtInr(v) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
    notation: 'compact', compactDisplay: 'short',
  }).format(v || 0)
}
function pct(v) { return `${Number(v || 0).toFixed(1)}%` }

function publicationCount(row) {
  return Number(
    row.journal_publications
    ?? row.total_journal_publications
    ?? row.total_research_papers
    ?? row.total_publications
    ?? row.publication_count
    ?? row.publications
    ?? row.total_papers
    ?? row.papers
    ?? row.value
    ?? 0,
  )
}

/* ── Alert panel ──────────────────────────────────────── */
function AlertPanel({ alerts }) {
  if (!alerts.length) return null
  return (
    <section className="page-section">
      <div className="page-section-header">
        <h3>Priority Follow-ups</h3>
      </div>
      <div className="alert-list">
        {alerts.map((a, i) => {
          const type = a.severity === 'risk' ? 'red' : a.severity === 'positive' ? 'green' : 'amber'
          const icon = a.severity === 'positive' ? '✓' : a.severity === 'risk' ? '✕' : '⚠'
          return (
            <div key={i} className={`alert-item alert-${type}`}>
              <span className="alert-icon">{icon}</span>
              <div className="alert-body">
                <div className="alert-title">{a.title}</div>
                <div className="alert-desc">{a.message}</div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

/* ── Main component ───────────────────────────────────── */
export default function ResearchAnalyticsDashboard() {
  const { data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx } = useResearchAnalytics()
  const [activePage, setActivePage] = useState('overview')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [autoRefreshTick, setAutoRefreshTick] = useState(0)

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      refresh()
      setAutoRefreshTick((tick) => tick + 1)
    }, 60000)

    return () => window.clearInterval(intervalId)
  }, [refresh])

  const sharedProps = { sharedData: data, filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options: data.filterOptions }
  const perfProps   = { filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options: data.filterOptions }

  /* Sub-page routing */
  const subPages = {
    publications:           <JournalPublicationsAnalyticsPage   {...sharedProps} />,
    books:                  <BooksAnalyticsPage                 {...sharedProps} />,
    patents:                <PatentsIprAnalyticsPage            {...sharedProps} />,
    projects:               <ProjectsFundingAnalyticsPage       {...sharedProps} />,
    guidance:               <ResearchGuidanceAnalyticsPage      {...sharedProps} />,
    conferences:            <ConferencesAwardsAnalyticsPage     {...sharedProps} />,
    pipeline:               <InnovationPipelinePage             {...sharedProps} />,
    'faculty-performance':      <FacultyResearchPerformancePage    {...perfProps} />,
    'department-performance':   <DepartmentResearchPerformancePage {...perfProps} />,
    'school-performance':       <SchoolResearchPerformancePage      {...perfProps} />,
    'teaching-balance':         <TeachingResearchAnalyticsPage      {...perfProps} />,
    completion:             <AppraisalCompletionAnalyticsPage   {...perfProps} />,
    'data-quality':         <ResearchDataQualityPage            {...perfProps} />,
  }

  const sidebar = (
    <Sidebar
      activePage={activePage}
      onPageSelect={setActivePage}
      mobileOpen={mobileOpen}
      onMobileClose={() => setMobileOpen(false)}
    />
  )

  if (subPages[activePage]) {
    return (
      <div className="analytics-shell">
        {sidebar}
        {subPages[activePage]}
      </div>
    )
  }

  /* ── Overview ─────────────────────────────────────────── */
  function handleReset() {
    updateFilters({
      page: 1, page_size: 10, search: '', school: '',
      department: '', designation: '', category: '', indexing: '', year: '',
      sort_by: 'total_research_papers', sort_order: 'desc',
    })
  }

  const ov      = data.overview || {}
  const depts   = data.departments?.items || []
  const active  = ov.total_active_faculty || ov.total_faculty || 0
  const pub     = ov.faculty_with_journal_publication || ov.faculty_with_research || 0
  const partPct = ov.publication_participation_rate || ((pub / (active || 1)) * 100)
  const inactive = Math.max(active - pub, 0)
  const totalPatents = Number(ov.total_patents || 0)
  const patentsGranted = Number(ov.patents_granted || 0)
  const grantRate = totalPatents ? (patentsGranted / totalPatents) * 100 : 0
  const researchDimensions = [
    ov.total_journal_publications || ov.total_research_papers,
    ov.total_book_publications || ov.total_books,
    ov.total_patents,
    ov.total_research_projects || ov.total_projects,
    ov.total_research_scholars_guided,
    ov.total_conferences,
    ov.total_awards,
  ].filter((value) => Number(value || 0) > 0).length
  const averageDiversity = Number(ov.average_research_diversity_score ?? ov.avg_research_diversity_score ?? ov.research_diversity_score ?? researchDimensions)
  const radarAxes = [
    { key: 'journals', label: 'Journals' },
    { key: 'books', label: 'Books' },
    { key: 'patents', label: 'Patents' },
    { key: 'projects', label: 'Projects' },
    { key: 'guidance', label: 'Guidance' },
    { key: 'conferences', label: 'Conferences' },
  ]
  const radarRows = [{
    label: 'University',
    journals: Number(ov.total_journal_publications || ov.total_research_papers || 0),
    books: Number(ov.total_book_publications || ov.total_books || 0),
    patents: totalPatents,
    projects: Number(ov.total_research_projects || ov.total_projects || 0),
    guidance: Number(ov.total_research_scholars_guided || 0),
    conferences: Number(ov.total_conferences || 0),
  }]
  const schoolPublicationRows = (() => {
    const schoolMap = new Map()
    depts.forEach((department) => {
      const school = String(department.school || department.school_name || '').trim()
      if (!school) return
      schoolMap.set(school, (schoolMap.get(school) || 0) + publicationCount(department))
    })

    const hasSchoolValues = [...schoolMap.values()].some((value) => Number(value || 0) > 0)
    if (!schoolMap.size || !hasSchoolValues) {
      schoolMap.clear()
      ;(data.faculty?.items || []).forEach((faculty) => {
        const school = String(faculty.school || faculty.school_name || '').trim()
        if (!school) return
        schoolMap.set(school, (schoolMap.get(school) || 0) + publicationCount(faculty))
      })
    }

    return [...schoolMap.entries()]
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
  })()

  const primaryKpis = [
    { label: 'Active Faculty',       value: active,  icon: '👤', subtext: `${pub} publishing` },
    { label: 'Journal Papers',       value: ov.total_journal_publications || ov.total_research_papers || 0, icon: '📄', subtext: 'Peer-reviewed' },
    { label: 'Participation Rate',   value: pct(partPct),                                          icon: '🎯', subtext: 'Faculty with publications' },
    { label: 'Total Patents',        value: ov.total_patents || 0,                                 icon: '💡', subtext: `${ov.patents_granted || 0} granted` },
    { label: 'Sanctioned Funding',   value: fmtInr(ov.total_sanctioned_funding || ov.total_funding), icon: '💰', subtext: 'Grants & projects' },
    { label: 'Research Diversity',   value: averageDiversity.toFixed(1),                           icon: 'RD', subtext: `${researchDimensions} active research areas` },
  ]

  const secondaryKpis = [
    { label: 'Books Published',       value: ov.total_book_publications || ov.total_books || 0 },
    { label: 'Conferences',           value: ov.total_conferences || 0 },
    { label: 'Research Projects',     value: ov.total_research_projects || ov.total_projects || 0 },
    { label: 'Students Guided',       value: ov.total_research_scholars_guided || 0 },
    { label: 'Awards',                value: ov.total_awards || 0 },
    { label: 'Inactive Researchers',  value: inactive },
  ]

  const insights = [
    {
      title: 'Publication Participation',
      explanation: `${pct(partPct)} of active faculty have at least one journal publication recorded.`,
      supporting_metric: `${pub} of ${active} active faculty`,
      severity: partPct >= 50 ? 'positive' : 'warning',
    },
    {
      title: 'Research Funding',
      explanation: `Total sanctioned institutional funding is ${fmtInr(ov.total_sanctioned_funding || ov.total_funding)}.`,
      supporting_metric: `Across ${ov.total_projects || 0} research projects`,
      severity: 'positive',
    },
    {
      title: 'Inactive Researchers',
      explanation: `${inactive} active faculty currently have no journal publication for the selected filters.`,
      supporting_metric: `${pct((inactive / (active || 1)) * 100)} of total faculty`,
      severity: inactive > 5 ? 'warning' : 'neutral',
    },
  ]

  const alerts = [
    depts.filter((d) => Number(d.publication_participation_percentage || 0) < 30).length > 0 && {
      title: 'Low-participation departments',
      message: `${depts.filter((d) => Number(d.publication_participation_percentage || 0) < 30).length} departments are below 30% participation.`,
      severity: 'warning',
    },
    inactive > 0 && {
      title: 'Inactive research contributors',
      message: `${inactive} faculty members have zero publication activity in the current view.`,
      severity: 'warning',
    },
    (ov.total_patents || 0) === 0 && {
      title: 'No patents on record',
      message: 'No patents are recorded for the current filter selection.',
      severity: 'risk',
    },
  ].filter(Boolean)

  return (
    <div className="analytics-shell">
      {sidebar}

      <main className="research-page">
        <PageHeader
          title="Executive Research Overview"
          description="Institutional research performance, participation, innovation and funding at a glance."
          onRefresh={refresh}
          onExportCsv={exportCsv}
          onExportXlsx={exportXlsx}
          onMobileMenuToggle={() => setMobileOpen(true)}
        />

        <FilterBar
          filters={filters}
          options={data.filterOptions}
          onChange={updateFilters}
          onReset={handleReset}
        />

        {error && !loading && (
          <div className={demoMode ? 'notice-banner' : 'error-banner'}>
            <strong>{error}</strong>
          </div>
        )}

        {loading ? (
          <section className="skeleton-grid" aria-label="Loading">
            {Array.from({ length: 6 }).map((_, i) => <span key={i} />)}
          </section>
        ) : (
          <>
            <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={secondaryKpis} />

            <div className="stat-rings-row">
              <StatRing value={partPct} label="Publication Participation" color="#6366f1" />
              <StatRing value={grantRate} label="Patent Grant Rate" color="#22c55e" />
              <StatRing value={(inactive / (active || 1)) * 100} label="Inactive Researchers" color="#ef4444" />
            </div>

            <InsightPanel insights={insights} />

            <div className="chart-grid">
              <DonutChart
                title="Publications by indexing"
                subtitle="Research output"
                rows={(data.indexing || []).map((d) => ({ label: d.indexing, value: d.total_papers || 0 }))}
                emptyMessage="No indexing data"
              />
              <AreaTrendChart
                title="Research paper trend"
                subtitle="Year-wise output"
                rows={(data.trend || []).map((d) => ({ label: d.year || d.academic_year, value: d.total_papers || 0 }))}
                color="var(--indigo)"
              />
              <RankingList
                title="Publications by school"
                subtitle="School analytics"
                rows={schoolPublicationRows}
                emptyMessage="No school publication data"
              />
              <HeatmapChart
                title="Participation rate by department"
                subtitle="Participation"
                rows={depts.map((d) => ({ label: d.department, participation: Number(d.publication_participation_percentage || 0).toFixed(0) }))}
                categories={['participation']}
                formatter={(v) => `${v}%`}
              />
              <RankingList
                title="Research funding by dept"
                subtitle="Project funding"
                rows={depts.map((d) => ({ label: d.department, value: Number(d.total_project_funding || 0) }))}
                formatter={fmtInr}
              />
              <DonutChart
                title="Patent status"
                subtitle="Innovation"
                rows={[
                  { label: 'Granted', value: Number(ov.patents_granted || 0) },
                  { label: 'Pending', value: Math.max(Number(ov.total_patents || 0) - Number(ov.patents_granted || 0), 0) },
                ]}
                emptyMessage="No patent data"
              />
            </div>

            <section className="executive-chart-row">
              <RadarChart
                title="University Research Profile"
                subtitle="Institutional dimensions"
                axes={radarAxes}
                rows={radarRows}
              />
            </section>

            <ComparisonTiles
              title="Research snapshot"
              subtitle="Key comparisons"
              items={[
                { label: 'Publishing Faculty', value: pub, subtext: `of ${active} active`, color: '#6366f1' },
                { label: 'Participation Rate', value: pct(partPct), color: '#22c55e', badge: partPct >= 50 ? '✓ Good' : '⚠ Low' },
                { label: 'Inactive Researchers', value: inactive, color: inactive > 5 ? '#ef4444' : '#f59e0b', subtext: 'No publications' },
                { label: 'Research Diversity', value: averageDiversity.toFixed(1), color: '#06b6d4', subtext: `${researchDimensions} active areas` },
              ]}
              style={{ marginBottom: '28px' }}
            />

            <AlertPanel alerts={alerts} />
          </>
        )}
      </main>
    </div>
  )
}
