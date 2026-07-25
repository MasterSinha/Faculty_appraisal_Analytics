import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import StatRing from '../components/research-analytics/charts/StatRing'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Overview', 'Missing Information', 'Possible Duplicates', 'Unmatched Records', 'Outliers', 'Completeness by Department']
const severities = ['Critical', 'Warning', 'Informational']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
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
  if (context.includes('severity') || context.includes('category')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function AlertTable({ alerts, reviewSupported }) {
  const [severity, setSeverity] = useState('')
  const [category, setCategory] = useState('')
  const [department, setDepartment] = useState('')
  const [search, setSearch] = useState('')

  const departments = [...new Set(alerts.map((alert) => departmentLabel(alert)).filter(Boolean))]
  const categories = [...new Set(alerts.map((alert) => alert.category).filter(Boolean))]

  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return alerts.filter((alert) =>
      (!severity || alert.severity === severity)
      && (!category || alert.category === category)
      && (!department || departmentLabel(alert) === department)
      && JSON.stringify(alert).toLowerCase().includes(query),
    )
  }, [alerts, severity, category, department, search])

  return (
    <article className="table-card data-quality-table-card">
      <div className="table-toolbar">
        <div>
          <span>Alert table</span>
          <h2>Research Data-Quality Alerts</h2>
        </div>
        <div className="books-table-controls">
          <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="">All severities</option>
            {severities.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={department} onChange={(event) => setDepartment(event.target.value)}>
            <option value="">All departments</option>
            {departments.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search alerts" />
          <button type="button">Export alerts</button>
        </div>
      </div>
      <div className="data-quality-table">
        <div className="data-quality-table-head">
          {['Severity', 'Alert type', 'Category', 'Faculty', 'Department', 'Record title', 'Academic year', 'Issue description', 'Suggested action', 'Open record'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((alert, index) => (
          <div className="data-quality-table-row" key={alert.id || `${alert.alert_type}-${index}`}>
            <strong className={`severity-pill ${String(alert.severity).toLowerCase()}`}>{alert.severity}</strong>
            <span>{alert.alert_type}</span>
            <span>{alert.category}</span>
            <span>{alert.faculty_name || alert.faculty_email || '-'}</span>
            <span>{departmentLabel(alert)}</span>
            <span>{alert.record_title || '-'}</span>
            <span>{alert.academic_year || '-'}</span>
            <span>{alert.issue_description}</span>
            <span>{alert.suggested_action}</span>
            <span>
              <button type="button">Open</button>
              <button type="button" disabled={!reviewSupported}>{reviewSupported ? 'Mark reviewed' : 'Review unsupported'}</button>
            </span>
          </div>
        ))}
      </div>
    </article>
  )
}

function buildMockAlerts() {
  const faculty = mockResearchAnalytics.faculty.items
  const checks = [
    ['Critical', 'Missing journal publication title', 'Journal Publications', 'Missing information'],
    ['Warning', 'Missing journal ISSN', 'Journal Publications', 'Missing information'],
    ['Warning', 'Missing journal indexing', 'Journal Publications', 'Missing information'],
    ['Warning', 'Missing book ISBN', 'Books', 'Missing information'],
    ['Critical', 'Missing patent status', 'Patents and IPR', 'Missing information'],
    ['Critical', 'Missing project amount', 'Projects and Funding', 'Missing information'],
    ['Critical', 'Unmatched faculty_email', 'Faculty Reference', 'Unmatched reference'],
    ['Warning', 'Duplicate title for same faculty and academic year', 'Research Records', 'Possible duplicate'],
    ['Warning', 'Same title submitted by different faculty', 'Research Records', 'Possible duplicate'],
    ['Warning', 'Duplicate ISBN', 'Books', 'Possible duplicate'],
    ['Warning', 'Duplicate patent file number', 'Patents and IPR', 'Possible duplicate'],
    ['Critical', 'Negative funding', 'Projects and Funding', 'Outlier'],
    ['Critical', 'Future patent date', 'Patents and IPR', 'Outlier'],
    ['Critical', 'Reviewer score above maximum marks', 'Reviewer Scores', 'Verification required'],
    ['Informational', 'Self-score present while reviewer scores are null', 'Reviewer Scores', 'Verification required'],
    ['Critical', 'Missing supporting document', 'Evidence', 'Data quality alert'],
    ['Warning', 'Unknown academic year', 'Academic Year', 'Data quality alert'],
    ['Informational', 'Extremely high record count for one faculty', 'Faculty Activity', 'Outlier'],
  ]
  return checks.map(([severity, alertType, category, label], index) => {
    const owner = faculty[index % faculty.length]
    return {
      id: `dq-${index}`,
      severity,
      alert_type: label,
      category,
      faculty_email: owner.email,
      faculty_name: owner.faculty_name,
      department: index % 7 === 0 ? '' : owner.department,
      school: index % 8 === 0 ? '' : owner.school,
      record_title: alertType,
      academic_year: index % 5 === 0 ? 'Unknown' : '2025-2026',
      issue_description: alertType,
      suggested_action: label === 'Possible duplicate' ? 'Verify records before merging or deleting.' : 'Review source record and update the missing or inconsistent field.',
    }
  })
}

export default function ResearchDataQualityPage({ filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [response, setResponse] = useState({ alerts: buildMockAlerts(), review_supported: false })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadDataQuality() {
      setLoading(true)
      setError('')
      try {
        const data = await researchAnalyticsApi.dataQuality(filters)
        if (!ignore) setResponse({ alerts: data.alerts || data.items || [], review_supported: Boolean(data.review_supported), completeness_percentage: data.completeness_percentage })
      } catch (requestError) {
        if (!ignore) {
          setResponse({ alerts: buildMockAlerts(), review_supported: false })
          setError(`${requestError.message} Showing demo research data-quality analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadDataQuality()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const alerts = response.alerts || []
  const critical = alerts.filter((alert) => alert.severity === 'Critical')
  const duplicates = alerts.filter((alert) => alert.alert_type === 'Possible duplicate')
  const missing = alerts.filter((alert) => alert.alert_type === 'Missing information')
  const unmatched = alerts.filter((alert) => alert.alert_type === 'Unmatched reference')
  const completeness = response.completeness_percentage ?? Math.max(0, 100 - (alerts.length * 2))
  const severityRows = Object.entries(groupBy(alerts, (alert) => alert.severity)).map(([label, rows]) => ({ label, value: rows.length }))
  const categoryRows = Object.entries(groupBy(alerts, (alert) => alert.category)).map(([label, rows]) => ({ label, value: rows.length }))
  const departmentRows = Object.entries(groupBy(alerts, (alert) => departmentLabel(alert))).map(([label, rows]) => ({ label, value: rows.length, completeness: Math.max(0, 100 - rows.length * 8) }))
  const tabAlerts = activeTab === 'Missing Information' ? missing
    : activeTab === 'Possible Duplicates' ? duplicates
      : activeTab === 'Unmatched Records' ? unmatched
        : activeTab === 'Outliers' ? alerts.filter((alert) => alert.alert_type === 'Outlier')
          : alerts

  return (
    <main className="research-page data-quality-page">
      <PageHeader
        title="Research Data Quality"
        description="Research data completeness, duplicates, reference matching, outliers, and evidence readiness"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}
      <div className="data-limitation-notice">
        <strong>Verification language</strong>
        <span>Records are flagged for review only. The dashboard never labels a record as fraudulent.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading research data quality">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Total Data-Quality Alerts', value: formatNumber(alerts.length), icon: 'QA', subtext: 'All severities' },
            { label: 'Critical Issues', value: formatNumber(critical.length), icon: 'CI', subtext: 'Requires priority review' },
            { label: 'Possible Duplicates', value: formatNumber(duplicates.length), icon: 'PD', subtext: 'Verify before action' },
            { label: 'Missing Mandatory Fields', value: formatNumber(missing.length), icon: 'MF', subtext: 'Required data missing' },
            { label: 'Unmatched Faculty Emails', value: formatNumber(unmatched.length), icon: 'UE', subtext: 'Faculty reference mismatch' },
            { label: 'Data Completeness Percentage', value: percent(completeness), icon: 'DC', subtext: 'Estimated completeness' },
          ]} secondaryKpis={severityRows} />

          <div className="stat-rings-row">
            <StatRing value={completeness} label="Overall Data Completeness" color="#22c55e" />
          </div>

          <nav className="page-tabs" aria-label="Data quality tabs">
            {tabs.map((tab) => <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>{tab}</button>)}
          </nav>

          {activeTab === 'Completeness by Department' ? (
            <section className="executive-chart-row two-col">
              <RankingList title="Completeness by department" subtitle="Completeness" rows={departmentRows} valueKey="completeness" formatter={percent} />
              <MiniBarChart title="Alerts by department" subtitle="Department" rows={departmentRows} />
            </section>
          ) : (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Alerts by severity" subtitle="Severity groups" rows={severityRows} />
              <MiniBarChart title="Alerts by category" subtitle="Research category" rows={categoryRows} />
              <MiniBarChart title="Missing information by department" subtitle="Missing fields" rows={departmentRows} />
            </section>
          )}

          <AlertTable alerts={tabAlerts} reviewSupported={response.review_supported} />
        </>
      )}
    </main>
  )
}
