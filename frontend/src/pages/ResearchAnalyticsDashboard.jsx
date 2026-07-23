import { useState } from 'react'
import AnalyticsFilters from '../components/research-analytics/AnalyticsFilters'
import AnalyticsHeader from '../components/research-analytics/AnalyticsHeader'
import EmptyState from '../components/research-analytics/EmptyState'
import FacultyResearchDrawer from '../components/research-analytics/FacultyResearchDrawer'
import FacultyResearchTable from '../components/research-analytics/FacultyResearchTable'
import IndexingDistributionChart from '../components/research-analytics/IndexingDistributionChart'
import OverviewCards from '../components/research-analytics/OverviewCards'
import ProjectFundingChart from '../components/research-analytics/ProjectFundingChart'
import PublicationTrendChart from '../components/research-analytics/PublicationTrendChart'
import ScoreComparisonChart from '../components/research-analytics/ScoreComparisonChart'
import TopFacultyChart from '../components/research-analytics/TopFacultyChart'
import { useResearchAnalytics } from '../hooks/useResearchAnalytics'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockFacultyDetail } from '../services/researchAnalyticsMockData'

export default function ResearchAnalyticsDashboard() {
  const { data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx } = useResearchAnalytics()
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

  return (
    <main className="research-page">
      <AnalyticsHeader demoMode={demoMode} onExportCsv={exportCsv} onExportXlsx={exportXlsx} onRefresh={refresh} />
      <AnalyticsFilters filters={filters} options={data.filterOptions} onChange={updateFilters} />

      {loading && (
        <section className="skeleton-grid" aria-label="Loading analytics">
          {Array.from({ length: 8 }).map((_, index) => <span key={index} />)}
        </section>
      )}

      {error && !loading && (
        <div className={demoMode ? 'notice-banner' : 'error-banner'}>
          <strong>{error}</strong>
          <span>For live database connection, ensure `REQUIRE_AUTH=false` in `.env` and PostgreSQL is reachable.</span>
        </div>
      )}

      {!loading && (!error || demoMode) && (
        <>
          <OverviewCards overview={data.overview} />

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

      {drawerError && <EmptyState title={drawerError} message="Unable to open the selected faculty detail." />}
      <FacultyResearchDrawer
        detail={facultyDetail}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onClose={() => setFacultyDetail(null)}
      />
    </main>
  )
}
