import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import ComparisonTiles from '../components/research-analytics/charts/ComparisonTiles'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import FunnelChart from '../components/research-analytics/charts/FunnelChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import RankingList from '../components/research-analytics/charts/RankingList'
import StatRing from '../components/research-analytics/charts/StatRing'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tableModes = [
  ['not_submitted', 'Faculty who have not submitted'],
  ['research_active_incomplete', 'Research-active faculty with incomplete appraisal'],
  ['submitted_no_research', 'Submitted faculty with no research records'],
  ['records_without_evidence', 'Research records without uploaded evidence'],
  ['awaiting_review', 'Appraisals awaiting reviewer action'],
]

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function displayStatus(value) {
  const text = String(value || '').trim()
  const lower = text.toLowerCase()
  if (!text) return 'Other recorded statuses'
  if (lower.includes('draft')) return 'Draft'
  if (lower.includes('pending')) return 'Pending Review'
  if (lower.includes('hod')) return 'HOD Reviewed'
  if (lower.includes('director')) return 'Director Reviewed'
  if (lower.includes('dean')) return 'Dean Reviewed'
  if (lower.includes('vc') || lower.includes('approved')) return 'VC Approved'
  return text
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
  if (context.includes('trend') || context.includes('year')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('review-stage') || context.includes('status')) return <FunnelChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('versus')) return <ComparisonTiles title={title} subtitle={subtitle} items={chartRows.map((row) => ({ label: row.label, value: formatter(row.value) }))} />
  if (context.includes('school')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('department')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function StatusPanel({ rows }) {
  return (
    <article className="quality-card">
      <h2>Status analytics</h2>
      <div className="quality-grid">
        {rows.map((row) => (
          <span key={row.label}>{row.label}<strong>{row.value}</strong></span>
        ))}
      </div>
    </article>
  )
}

function DepartmentMetricsTable({ rows }) {
  return (
    <article className="table-card completion-table-card">
      <div className="table-toolbar">
        <div>
          <span>Department metrics</span>
          <h2>Completion and Evidence Readiness</h2>
        </div>
      </div>
      <div className="completion-department-table">
        <div className="completion-department-table-head">
          {['Department', 'Active faculty', 'Submitted', 'Pending', 'Completion rate', 'Research-active not submitted', 'Records without documents', 'Avg docs / research-active faculty'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {rows.map((row) => (
          <div className="completion-department-table-row" key={row.department}>
            <strong>{row.department}</strong>
            <span>{row.active_faculty}</span>
            <span>{row.submitted_count}</span>
            <span>{row.pending_count}</span>
            <span>{percent(row.completion_rate)}</span>
            <span>{row.research_active_not_submitted}</span>
            <span>{row.records_without_documents}</span>
            <span>{Number(row.average_document_count_per_research_active_faculty || 0).toFixed(2)}</span>
          </div>
        ))}
      </div>
    </article>
  )
}

function OperationalTables({ tables }) {
  const [mode, setMode] = useState('not_submitted')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const rows = tables[mode] || []
    const query = search.toLowerCase()
    return rows.filter((row) => JSON.stringify(row).toLowerCase().includes(query))
  }, [tables, mode, search])

  return (
    <article className="table-card completion-table-card">
      <div className="table-toolbar">
        <div>
          <span>Follow-up tables</span>
          <h2>{tableModes.find(([key]) => key === mode)?.[1]}</h2>
        </div>
        <div className="books-table-controls">
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            {tableModes.map(([key, label]) => <option value={key} key={key}>{label}</option>)}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search follow-up list" />
        </div>
      </div>
      <div className="completion-followup-table">
        <div className="completion-followup-table-head">
          {['Faculty', 'Department', 'School', 'Status', 'Academic year', 'Reason / evidence'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((row, index) => (
          <div className="completion-followup-table-row" key={row.id || `${mode}-${index}`}>
            <strong>{row.full_name || row.faculty_name || row.faculty_email || '-'}</strong>
            <span>{departmentLabel(row)}</span>
            <span>{row.school || '-'}</span>
            <span>{displayStatus(row.status)}</span>
            <span>{row.academic_year || '-'}</span>
            <span>{row.reason || row.evidence_status || row.record_title || '-'}</span>
          </div>
        ))}
      </div>
    </article>
  )
}

function buildMockCompletion() {
  const faculty = mockResearchAnalytics.faculty.items
  const appraisals = faculty.map((item, index) => ({
    ...item,
    full_name: item.faculty_name,
    faculty_email: item.email,
    status: ['Draft', 'Pending Review', 'HOD Reviewed', 'Director Reviewed', 'Dean Reviewed', 'VC Approved'][index % 6],
    academic_year: '2025-2026',
    research_active: Number(item.total_research_papers || 0) + Number(item.research_projects || 0) > 0,
    submitted: index % 3 !== 0,
    document_count: 2 + index,
    records_without_documents: index % 2,
  }))
  const notSubmitted = appraisals.filter((item) => !item.submitted).map((item) => ({ ...item, reason: 'Appraisal not submitted' }))
  const researchActiveIncomplete = appraisals.filter((item) => item.research_active && item.status !== 'VC Approved').map((item) => ({ ...item, reason: 'Research-active faculty with incomplete appraisal' }))
  const submittedNoResearch = appraisals.filter((item) => item.submitted && !item.research_active).map((item) => ({ ...item, reason: 'Submitted with no research records' }))
  const recordsWithoutEvidence = appraisals.filter((item) => item.records_without_documents > 0).map((item) => ({ ...item, evidence_status: 'Research record missing uploaded evidence' }))
  const awaitingReview = appraisals.filter((item) => ['Pending Review', 'HOD Reviewed', 'Director Reviewed', 'Dean Reviewed'].includes(item.status)).map((item) => ({ ...item, reason: 'Awaiting reviewer action' }))
  return {
    appraisals,
    tables: {
      not_submitted: notSubmitted,
      research_active_incomplete: researchActiveIncomplete,
      submitted_no_research: submittedNoResearch,
      records_without_evidence: recordsWithoutEvidence,
      awaiting_review: awaitingReview,
    },
  }
}

export default function AppraisalCompletionAnalyticsPage({ filters, updateFilters, refresh, exportCsv, exportXlsx, options }) {
  const [response, setResponse] = useState(buildMockCompletion())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadCompletion() {
      setLoading((current) => current)
      setError('')
      try {
        const data = await researchAnalyticsApi.appraisalCompletion(filters)
        if (!ignore) setResponse({
          appraisals: data.appraisals || data.items || [],
          tables: data.tables || {},
          department_metrics: data.department_metrics || [],
        })
      } catch (requestError) {
        if (!ignore) {
          setResponse(buildMockCompletion())
          setError(`${requestError.message} Showing demo appraisal completion analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadCompletion()
    return () => {
      ignore = true
    }
  }, [filters])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const appraisals = response.appraisals || []
  const activeFaculty = appraisals.length
  const submitted = appraisals.filter((item) => item.submitted || !['Draft', 'Other recorded statuses'].includes(displayStatus(item.status))).length
  const pending = Math.max(activeFaculty - submitted, 0)
  const researchActive = appraisals.filter((item) => item.research_active)
  const researchActiveNotSubmitted = researchActive.filter((item) => !item.submitted).length
  const missingEvidence = appraisals.reduce((sum, item) => sum + Number(item.records_without_documents || 0), 0)
  const statusRows = Object.entries(groupBy(appraisals, (item) => displayStatus(item.status))).map(([label, rows]) => ({ label, value: rows.length }))
  const vcApproved = statusRows.find((row) => row.label === 'VC Approved')?.value || 0
  const researchActiveSubmitted = researchActive.filter((item) => item.submitted).length
  const departmentMetrics = response.department_metrics?.length
    ? response.department_metrics.map((row) => ({ ...row, department: departmentLabel(row) }))
    : Object.entries(groupBy(appraisals, (item) => departmentLabel(item))).map(([department, rows]) => {
    const submittedCount = rows.filter((item) => item.submitted).length
    const researchActiveRows = rows.filter((item) => item.research_active)
    return {
      department,
      active_faculty: rows.length,
      submitted_count: submittedCount,
      pending_count: rows.length - submittedCount,
      completion_rate: rows.length ? (submittedCount / rows.length) * 100 : 0,
      research_active_not_submitted: researchActiveRows.filter((item) => !item.submitted).length,
      records_without_documents: rows.reduce((sum, item) => sum + Number(item.records_without_documents || 0), 0),
      average_document_count_per_research_active_faculty: researchActiveRows.length ? rows.reduce((sum, item) => sum + Number(item.document_count || 0), 0) / researchActiveRows.length : 0,
    }
  })
  const schoolRows = Object.entries(groupBy(appraisals, (item) => item.school)).map(([label, rows]) => {
    const submittedCount = rows.filter((item) => item.submitted).length
    return { label, value: rows.length ? (submittedCount / rows.length) * 100 : 0 }
  })
  const yearRows = Object.entries(groupBy(appraisals, (item) => item.academic_year)).map(([label, rows]) => ({ label, value: rows.filter((item) => item.submitted).length }))

  return (
    <main className="research-page completion-page">
      <PageHeader
        title="Appraisal Completion Analytics"
        description="Submission completion, review stages, evidence readiness, and research-active follow-up lists"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}
      <div className="data-limitation-notice">
        <strong>Evidence mapping note</strong>
        <span>Uploaded documents are not assumed to map one-to-one with research records unless doc_key or section mapping confirms it.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading appraisal completion analytics">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Active Faculty', value: formatNumber(activeFaculty), icon: 'AF', subtext: 'Faculty in selected period' },
            { label: 'Submitted Appraisals', value: formatNumber(submitted), icon: 'SA', subtext: 'Submitted or reviewed' },
            { label: 'Pending Appraisals', value: formatNumber(pending), icon: 'PA', subtext: 'Awaiting submission' },
            { label: 'Completion Percentage', value: percent(activeFaculty ? (submitted / activeFaculty) * 100 : 0), icon: 'CP', subtext: 'Submitted / active faculty' },
            { label: 'Research-Active Faculty Not Submitted', value: formatNumber(researchActiveNotSubmitted), icon: 'RN', subtext: 'Research activity recorded' },
            { label: 'Research Records Missing Evidence', value: formatNumber(missingEvidence), icon: 'ME', subtext: 'Document evidence gap' },
          ]} secondaryKpis={statusRows} />

          <div className="stat-rings-row">
            <StatRing value={activeFaculty ? (submitted / activeFaculty) * 100 : 0} label="Completion Rate" color="#22c55e" />
            <StatRing value={activeFaculty ? (vcApproved / activeFaculty) * 100 : 0} label="VC Approved Rate" color="#6366f1" />
            <StatRing value={researchActive.length ? (researchActiveSubmitted / researchActive.length) * 100 : 0} label="Research Active Submitted" color="#f59e0b" />
          </div>

          <section className="executive-chart-row two-col">
            <RankingList title="Submission status by department" subtitle="Department" rows={departmentMetrics.map((row) => ({ label: row.department, value: row.submitted_count }))} />
            <MiniBarChart title="Completion rate by school" subtitle="School" rows={schoolRows} formatter={percent} />
            <MiniBarChart title="Submission trend by academic year" subtitle="Academic year" rows={yearRows} />
            <MiniBarChart title="Research-active versus submitted faculty" subtitle="Submission alignment" rows={[
              { label: 'Research-active faculty', value: researchActive.length },
              { label: 'Submitted appraisals', value: submitted },
              { label: 'Research-active not submitted', value: researchActiveNotSubmitted },
            ]} />
            <MiniBarChart title="Evidence completion by department" subtitle="Missing evidence" rows={departmentMetrics.map((row) => ({ label: row.department, value: row.records_without_documents }))} />
            <MiniBarChart title="Review-stage distribution" subtitle="Reviewer action" rows={statusRows} />
            <StatusPanel rows={statusRows} />
          </section>

          <DepartmentMetricsTable rows={departmentMetrics} />
          <OperationalTables tables={response.tables || {}} />
        </>
      )}
    </main>
  )
}
