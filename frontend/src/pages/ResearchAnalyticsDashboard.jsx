import { useState } from 'react'
import FacultyResearchDrawer from '../components/research-analytics/FacultyResearchDrawer'
import FacultyResearchTable from '../components/research-analytics/FacultyResearchTable'
import FilterBar from '../components/research-analytics/FilterBar'
import IndexingDistributionChart from '../components/research-analytics/IndexingDistributionChart'
import InsightPanel from '../components/research-analytics/InsightPanel'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import ProjectFundingChart from '../components/research-analytics/ProjectFundingChart'
import PublicationTrendChart from '../components/research-analytics/PublicationTrendChart'
import ScoreComparisonChart from '../components/research-analytics/ScoreComparisonChart'
import Sidebar from '../components/research-analytics/Sidebar'
import TopFacultyChart from '../components/research-analytics/TopFacultyChart'
import { useResearchAnalytics } from '../hooks/useResearchAnalytics'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockFacultyDetail } from '../services/researchAnalyticsMockData'

export default function ResearchAnalyticsDashboard() {
  const { data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx } = useResearchAnalytics()
  const [activePage, setActivePage] = useState('overview')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [facultyDetail, setFacultyDetail] = useState(null)
  const [activeTab, setActiveTab] = useState('journal_publications')
  const [drawerError, setDrawerError] = useState('')

  async function openFacultyDetail(facultyId) {
    setDrawerError('')
    try {
      if (demoMode) {
        setFacultyDetail(mockFacultyDetail(facultyId))
        setActiveTab('journal_publications')
        return
      }
      setFacultyDetail(await researchAnalyticsApi.facultyDetail(facultyId))
      setActiveTab('journal_publications')
    } catch (requestError) {
      setDrawerError(requestError.message)
    }
  }

  function handleResetFilters() {
    updateFilters({
      page: 1,
      page_size: 10,
      search: '',
      school: '',
      department: '',
      indexing: '',
      year: '',
      sort_by: 'total_research_papers',
      sort_order: 'desc',
    })
  }

  const primaryKpis = [
    { label: 'Active Faculty', value: data.overview?.total_faculty || 0, icon: '👤', subtext: `${data.overview?.faculty_with_research || 0} active researchers` },
    { label: 'Journal Papers', value: data.overview?.total_research_papers || 0, icon: '📄', subtext: 'Peer reviewed publications' },
    { label: 'Total Patents', value: data.overview?.total_patents || 0, icon: '💡', subtext: 'Registered & filed' },
    { label: 'Sanctioned Funding', value: `₹${((data.overview?.total_funding || 0) / 10000000).toFixed(1)} Cr`, icon: '💰', subtext: 'External grants & projects' },
    { label: 'Research Diversity', value: `${((data.overview?.faculty_with_research || 0) / (data.overview?.total_faculty || 1) * 100).toFixed(1)}%`, icon: '🎯', subtext: 'Participation rate' },
  ]

  const secondaryKpis = [
    { label: 'Books Published', value: data.overview?.total_books || 0, icon: '📚' },
    { label: 'Conferences', value: data.overview?.total_conferences || 0, icon: '🎤' },
    { label: 'Approved VC Score', value: (data.overview?.total_vc_score || 0).toLocaleString(), icon: '⭐' },
    { label: 'Total Projects', value: data.overview?.total_projects || 0, icon: '🔬' },
  ]

  const pageTitleMap = {
    overview: { title: 'Executive Research Overview', desc: 'High-level insights, key indicators, and institutional productivity summary.' },
    publications: { title: 'Publications & Books Analytics', desc: 'Journal papers, indexing distribution, and publishing trends.' },
    books: { title: 'Book Publications & Chapters', desc: 'ISBN books, author order, and department distribution.' },
    patents: { title: 'Patents, IPR & Innovation', desc: 'Patent grant rates, domestic vs international scope, and filing pipeline.' },
    projects: { title: 'Projects & Research Funding', desc: 'Sanctioned grants, funding agency concentration, and proposal trends.' },
    guidance: { title: 'Research Guidance & Supervision', desc: 'PhD, PG, and UG scholar guidance stats across departments.' },
    conferences: { title: 'Conferences & Academic Awards', desc: 'National vs International conference papers and faculty honors.' },
    pipeline: { title: 'Innovation Pipeline & Conversion', desc: 'Aggregate funnel from proposal submission to products developed.' },
    'faculty-performance': { title: 'Faculty Performance Leaderboard', desc: 'Individual research metrics, output rankings, and score breakdown.' },
    'department-performance': { title: 'Department Research Health', desc: 'Department-level output comparison, participation rates, and funding.' },
    'school-performance': { title: 'School Research Performance', desc: 'School-level aggregate metrics and cross-department trends.' },
    'teaching-balance': { title: 'Teaching vs Research Balance', desc: 'Quadrant analysis mapping teaching benchmark scores vs research output.' },
    completion: { title: 'Appraisal Completion Tracking', desc: 'Faculty submission status, research activity, and evidence upload tracking.' },
    'data-quality': { title: 'Data Quality & Verification Alerts', desc: 'Audit alerts, missing indexing, email mismatches, and score variance.' },
    alerts: { title: 'Reviewer Score Variance & Verification', desc: 'Self-score vs VC score adjustment analysis.' },
  }

  const currentPage = pageTitleMap[activePage] || pageTitleMap.overview

  return (
    <div className="analytics-shell">
      <Sidebar
        activePage={activePage}
        onPageSelect={setActivePage}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <main className="research-page">
        <PageHeader
          title={currentPage.title}
          description={currentPage.desc}
          onRefresh={refresh}
          onExportCsv={exportCsv}
          onExportXlsx={exportXlsx}
          onMobileMenuToggle={() => setMobileOpen(true)}
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
            {Array.from({ length: 4 }).map((_, index) => <span key={index} />)}
          </section>
        ) : (
          <>
            <MetricCardGrid primaryKpis={primaryKpis} secondaryKpis={secondaryKpis} />

            <InsightPanel insights={[
              {
                title: 'Highest Publishing Volume',
                explanation: `Recorded research papers stand at ${data.overview?.total_research_papers || 0} publications.`,
                supporting_metric: `${data.overview?.total_research_papers || 0} journal papers`,
                severity: 'positive',
              },
              {
                title: 'Sanctioned Research Funding',
                explanation: `Total research grant volume reached ₹${((data.overview?.total_funding || 0) / 10000000).toFixed(2)} Cr across departments.`,
                supporting_metric: `₹${((data.overview?.total_funding || 0) / 10000000).toFixed(1)} Cr total`,
                severity: 'positive',
              },
              {
                title: 'Faculty Research Participation',
                explanation: `${data.overview?.faculty_with_research || 0} out of ${data.overview?.total_faculty || 0} active faculty have published research.`,
                supporting_metric: `${((data.overview?.faculty_with_research || 0) / (data.overview?.total_faculty || 1) * 100).toFixed(1)}% active rate`,
                severity: 'neutral',
              },
            ]} />

            <section className="chart-grid">
              <IndexingDistributionChart data={data.indexing} />
              <PublicationTrendChart data={data.trend} />
              <ScoreComparisonChart scores={data.scores} />
              <ProjectFundingChart data={data.projects} />
              <TopFacultyChart data={data.topFaculty} />
              <article className="chart-card">
                <div className="card-title">
                  <span>Top journals</span>
                  <h2>Publication count</h2>
                </div>
                <div className="horizontal-chart">
                  {data.topJournals.map((item) => (
                    <div className="hbar-row" key={item.journal}>
                      <span>{item.journal}</span>
                      <div><i style={{ width: `${Math.min((item.total || 0) * 10, 100)}%` }} /></div>
                      <strong>{item.total}</strong>
                    </div>
                  ))}
                </div>
              </article>
            </section>

            <FacultyResearchTable
              data={data.faculty}
              filters={filters}
              onFilterChange={updateFilters}
              onViewDetails={openFacultyDetail}
            />
          </>
        )}

        {drawerError && <div className="error-banner">Unable to load details: {drawerError}</div>}
        <FacultyResearchDrawer
          detail={facultyDetail}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onClose={() => setFacultyDetail(null)}
        />
      </main>
    </div>
  )
}
