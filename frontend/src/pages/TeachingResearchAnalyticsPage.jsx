import { useEffect, useMemo, useState } from 'react'
import FilterBar from '../components/research-analytics/FilterBar'
import MetricCardGrid from '../components/research-analytics/MetricCardGrid'
import PageHeader from '../components/research-analytics/PageHeader'
import AreaTrendChart from '../components/research-analytics/charts/AreaTrendChart'
import DonutChart from '../components/research-analytics/charts/DonutChart'
import HorizontalBarChart from '../components/research-analytics/charts/HorizontalBarChart'
import ScatterChart from '../components/research-analytics/charts/ScatterChart'
import StatRing from '../components/research-analytics/charts/StatRing'
import TileGrid from '../components/research-analytics/charts/TileGrid'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { departmentLabel } from '../utils/academicUnit'

const tabs = ['Faculty Quadrant', 'Department Balance', 'Teaching Components', 'Research Components', 'Trends']

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0)
}

function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function normalizeScore(score, maxMarks = 100) {
  return maxMarks ? Math.max(0, Math.min((Number(score || 0) / Number(maxMarks)) * 100, 100)) : 0
}

function quadrantFor(teaching, research) {
  if (teaching >= 60 && research >= 60) return 'Balanced Leaders'
  if (teaching >= 60 && research < 60) return 'Teaching Focused'
  if (teaching < 60 && research >= 60) return 'Research Focused'
  return 'Development Opportunity'
}

function groupBy(records, keyGetter) {
  return records.reduce((acc, record) => {
    const key = keyGetter(record) || 'Unknown'
    acc[key] = acc[key] || []
    acc[key].push(record)
    return acc
  }, {})
}

function average(rows, key) {
  return rows.length ? rows.reduce((sum, row) => sum + Number(row[key] || 0), 0) / rows.length : 0
}

function MiniBarChart({ title, subtitle, rows, labelKey = 'label', valueKey = 'value', formatter = formatNumber }) {
  const chartRows = rows.map((row) => ({ ...row, label: row[labelKey], value: Number(row[valueKey] || 0), x: Number(row.teaching ?? row[valueKey] ?? 0), y: Number(row.research ?? row[valueKey] ?? 0) }))
  const context = `${title} ${subtitle}`.toLowerCase()
  if (context.includes('trend') || context.includes('year')) return <AreaTrendChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('distribution') || context.includes('quadrant')) return <DonutChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  if (context.includes('balance')) return <ScatterChart title={title} subtitle={subtitle} rows={chartRows} xLabel="Teaching" yLabel="Research" xFormatter={percent} yFormatter={percent} />
  if (context.includes('score') || context.includes('component')) return <HorizontalBarChart title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
  return <TileGrid title={title} subtitle={subtitle} rows={chartRows} formatter={formatter} />
}

function QuadrantChart({ rows }) {
  return (
    <article className="chart-card teaching-quadrant-card">
      <div className="card-title">
        <span>Normalized comparison</span>
        <h2>Teaching performance score vs Research performance score</h2>
      </div>
      <div className="teaching-quadrant">
        <span className="q-label q-balanced">Balanced Leaders</span>
        <span className="q-label q-teaching">Teaching Focused</span>
        <span className="q-label q-research">Research Focused</span>
        <span className="q-label q-development">Development Opportunity</span>
        <i className="axis-x" />
        <i className="axis-y" />
        {rows.map((row) => (
          <button
            type="button"
            key={row.email || row.faculty_name}
            title={`${row.faculty_name}: Teaching ${percent(row.teaching_score)}, Research ${percent(row.research_score)}`}
            className={`quadrant-dot ${row.quadrant.toLowerCase().replaceAll(' ', '-')}`}
            style={{ left: `${Math.min(row.teaching_score, 96)}%`, bottom: `${Math.min(row.research_score, 96)}%` }}
          />
        ))}
      </div>
      <div className="quadrant-axis-copy">
        <span>X-axis: Teaching performance score</span>
        <span>Y-axis: Research performance score</span>
      </div>
    </article>
  )
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

function FacultyBalanceTable({ rows }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('teaching_score')
  const filtered = useMemo(() => {
    const query = search.toLowerCase()
    return rows
      .filter((row) => JSON.stringify(row).toLowerCase().includes(query))
      .sort((a, b) => Number(b[sortBy] || 0) - Number(a[sortBy] || 0))
  }, [rows, search, sortBy])

  return (
    <article className="table-card teaching-balance-table-card">
      <div className="table-toolbar">
        <div>
          <span>Faculty balance</span>
          <h2>Teaching versus Research Faculty View</h2>
        </div>
        <div className="books-table-controls">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search faculty" />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="teaching_score">Sort by teaching score</option>
            <option value="research_score">Sort by research score</option>
            <option value="student_feedback_score">Sort by feedback</option>
            <option value="innovative_teaching_score">Sort by innovation</option>
          </select>
        </div>
      </div>
      <div className="teaching-balance-table">
        <div className="teaching-balance-table-head">
          {['Faculty', 'Department', 'School', 'Teaching score', 'Research score', 'Student feedback', 'Innovative teaching', 'ICT usage', 'Quadrant'].map((column) => <span key={column}>{column}</span>)}
        </div>
        {filtered.map((row) => (
          <div className="teaching-balance-table-row" key={row.email || row.faculty_name}>
            <strong>{row.faculty_name}</strong>
            <span>{departmentLabel(row)}</span>
            <span>{row.school}</span>
            <span>{percent(row.teaching_score)}</span>
            <span>{percent(row.research_score)}</span>
            <span>{percent(row.student_feedback_score)}</span>
            <span>{percent(row.innovative_teaching_score)}</span>
            <span>{percent(row.ict_usage_score)}</span>
            <span>{row.quadrant}</span>
          </div>
        ))}
      </div>
    </article>
  )
}

function buildMockRows() {
  return mockResearchAnalytics.faculty.items.map((faculty, index) => {
    const teachingRaw = 72 + (index * 7)
    const researchRaw = Math.min(95, (faculty.total_vc_score || 0) + index * 3)
    const teachingScore = normalizeScore(teachingRaw, 100)
    const researchScore = normalizeScore(researchRaw, 100)
    return {
      email: faculty.email,
      faculty_name: faculty.faculty_name,
      department: faculty.department,
      school: faculty.school,
      teaching_score: teachingScore,
      research_score: researchScore,
      student_feedback_score: normalizeScore(70 + index * 6, 100),
      innovative_teaching_score: normalizeScore(62 + index * 8, 100),
      ict_usage_score: normalizeScore(68 + index * 5, 100),
      teaching_process_score: normalizeScore(76 + index * 4, 100),
      course_files_score: normalizeScore(80 - index * 5, 100),
      self_development_score: normalizeScore(65 + index * 7, 100),
      publications_score: normalizeScore(faculty.total_research_papers || 0, 20),
      projects_score: normalizeScore(faculty.research_projects || 0, 5),
      patents_score: normalizeScore(faculty.patents || 0, 3),
      academic_year: `202${index + 3}-202${index + 4}`,
      quadrant: quadrantFor(teachingScore, researchScore),
    }
  })
}

export default function TeachingResearchAnalyticsPage({ filters, updateFilters, refresh, autoRefreshTick, exportCsv, exportXlsx, options }) {
  const [activeTab, setActiveTab] = useState('Faculty Quadrant')
  const [response, setResponse] = useState({ items: buildMockRows() })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    async function loadBalance() {
      setLoading(true)
      setError('')
      try {
        const data = await researchAnalyticsApi.teachingResearchBalance(filters)
        if (!ignore) setResponse({ items: data.items || data.faculty || [] })
      } catch (requestError) {
        if (!ignore) {
          setResponse({ items: buildMockRows() })
          setError(`${requestError.message} Showing demo teaching versus research analytics.`)
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    loadBalance()
    return () => {
      ignore = true
    }
  }, [filters, autoRefreshTick])

  function resetFilters() {
    updateFilters({ search: '', school: '', department: '', designation: '', category: '', indexing: '', year: '', page: 1 })
  }

  const rows = (response.items || []).map((row) => {
    const teachingScore = row.teaching_score_percentage ?? normalizeScore(row.teaching_score, row.teaching_max_marks || 100)
    const researchScore = row.research_score_percentage ?? normalizeScore(row.research_score, row.research_max_marks || 100)
    return {
      ...row,
      faculty_name: row.faculty_name || row.full_name || row.faculty_email,
      teaching_score: teachingScore,
      research_score: researchScore,
      student_feedback_score: row.student_feedback_score_percentage ?? normalizeScore(row.student_feedback_score, row.student_feedback_max_marks || 100),
      innovative_teaching_score: row.innovative_teaching_score_percentage ?? normalizeScore(row.innovative_teaching_score, row.innovative_teaching_max_marks || 100),
      ict_usage_score: row.ict_usage_score_percentage ?? normalizeScore(row.ict_usage_score, row.ict_usage_max_marks || 100),
      teaching_process_score: row.teaching_process_score_percentage ?? normalizeScore(row.teaching_process_score, row.teaching_process_max_marks || 100),
      course_files_score: row.course_files_score_percentage ?? normalizeScore(row.course_files_score, row.course_files_max_marks || 100),
      self_development_score: row.self_development_score_percentage ?? normalizeScore(row.self_development_score, row.self_development_max_marks || 100),
      publications_score: row.publications_score_percentage ?? normalizeScore(row.publications_score, row.publications_max_marks || 100),
      projects_score: row.projects_score_percentage ?? normalizeScore(row.projects_score, row.projects_max_marks || 100),
      patents_score: row.patents_score_percentage ?? normalizeScore(row.patents_score, row.patents_max_marks || 100),
    }
  }).map((row) => ({ ...row, quadrant: row.quadrant || quadrantFor(row.teaching_score, row.research_score) }))

  const balanced = rows.filter((row) => row.quadrant === 'Balanced Leaders')
  const teachingFocused = rows.filter((row) => row.quadrant === 'Teaching Focused')
  const researchFocused = rows.filter((row) => row.quadrant === 'Research Focused')
  const development = rows.filter((row) => row.quadrant === 'Development Opportunity')
  const departmentRows = Object.entries(groupBy(rows, (row) => departmentLabel(row))).map(([label, items]) => ({
    label,
    teaching: average(items, 'teaching_score'),
    research: average(items, 'research_score'),
    value: Math.abs(average(items, 'teaching_score') - average(items, 'research_score')),
  }))
  const yearRows = Object.entries(groupBy(rows, (row) => row.academic_year)).map(([label, items]) => ({ label, value: items.filter((item) => item.quadrant === 'Balanced Leaders').length }))
  const highResearchLowFeedback = rows.filter((row) => row.research_score >= 60 && row.student_feedback_score < 60)

  return (
    <main className="research-page teaching-research-page">
      <PageHeader
        title="Teaching versus Research Analytics"
        description="Normalized teaching and research performance balance using approved percentage-based comparison"
        lastRefreshed="Just now"
        onRefresh={refresh}
        onExportCsv={exportCsv}
        onExportXlsx={exportXlsx}
        onMobileMenuToggle={() => {}}
      />
      <FilterBar filters={filters} options={options} onChange={updateFilters} onReset={resetFilters} />
      {error && <div className="notice-banner"><strong>{error}</strong></div>}
      <div className="data-limitation-notice">
        <strong>Important disclaimer</strong>
        <span>This dashboard shows associations within recorded appraisal data. It does not prove that one activity caused another. Scores are normalised to percentages before comparison.</span>
      </div>

      {loading ? (
        <section className="skeleton-grid" aria-label="Loading teaching research balance">
          {Array.from({ length: 6 }).map((_, index) => <span key={index} />)}
        </section>
      ) : (
        <>
          <MetricCardGrid primaryKpis={[
            { label: 'Balanced High Performers', value: formatNumber(balanced.length), icon: 'BH', subtext: 'High teaching and research' },
            { label: 'Teaching-Focused Faculty', value: formatNumber(teachingFocused.length), icon: 'TF', subtext: 'Teaching score leads' },
            { label: 'Research-Focused Faculty', value: formatNumber(researchFocused.length), icon: 'RF', subtext: 'Research score leads' },
            { label: 'Development Opportunity Group', value: formatNumber(development.length), icon: 'DO', subtext: 'Support opportunity' },
            { label: 'Average Teaching Score', value: percent(average(rows, 'teaching_score')), icon: 'TS', subtext: 'Normalized percentage' },
            { label: 'Average Research Score', value: percent(average(rows, 'research_score')), icon: 'RS', subtext: 'Normalized percentage' },
          ]} secondaryKpis={[
            { label: 'Faculty strong in both areas', value: balanced.length },
            { label: 'High teaching and low research', value: teachingFocused.length },
            { label: 'High research and lower feedback', value: highResearchLowFeedback.length },
          ]} />

          <div className="stat-rings-row">
            <StatRing value={rows.length ? (balanced.length / rows.length) * 100 : 0} label="Balanced Leaders" color="#22c55e" />
            <StatRing value={rows.length ? (teachingFocused.length / rows.length) * 100 : 0} label="Teaching Focused" color="#6366f1" />
            <StatRing value={rows.length ? (researchFocused.length / rows.length) * 100 : 0} label="Research Focused" color="#f59e0b" />
          </div>

          <nav className="page-tabs" aria-label="Teaching research tabs">
            {tabs.map((tab) => <button className={activeTab === tab ? 'active' : ''} type="button" key={tab} onClick={() => setActiveTab(tab)}>{tab}</button>)}
          </nav>

          {activeTab === 'Faculty Quadrant' && (
            <section className="executive-chart-row two-col">
              <QuadrantChart rows={rows} />
              <InsightCard title="Faculty groups" items={[
                { label: 'Faculty strong in both areas', value: balanced.length },
                { label: 'Faculty with high teaching and low research', value: teachingFocused.length },
                { label: 'Faculty with high research and lower student feedback', value: highResearchLowFeedback.length },
              ]} />
            </section>
          )}
          {activeTab === 'Department Balance' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Department teaching-research balance" subtitle="Score gap" rows={departmentRows} formatter={percent} />
              <MiniBarChart title="Average teaching score by department" subtitle="Teaching" rows={departmentRows} valueKey="teaching" formatter={percent} />
              <MiniBarChart title="Average research score by department" subtitle="Research" rows={departmentRows} valueKey="research" formatter={percent} />
            </section>
          )}
          {activeTab === 'Teaching Components' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Innovative teaching versus student feedback association" subtitle="Association only" rows={rows.map((row) => ({ label: row.faculty_name, value: Math.abs(row.innovative_teaching_score - row.student_feedback_score) }))} formatter={percent} />
              <MiniBarChart title="ICT usage versus student feedback association" subtitle="Association only" rows={rows.map((row) => ({ label: row.faculty_name, value: Math.abs(row.ict_usage_score - row.student_feedback_score) }))} formatter={percent} />
              <MiniBarChart title="Teaching process score" subtitle="Teaching source" rows={rows.map((row) => ({ label: row.faculty_name, value: row.teaching_process_score }))} formatter={percent} />
              <MiniBarChart title="Course files and self development" subtitle="Teaching source" rows={rows.map((row) => ({ label: row.faculty_name, value: (row.course_files_score + row.self_development_score) / 2 }))} formatter={percent} />
            </section>
          )}
          {activeTab === 'Research Components' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Publication component" subtitle="Research source" rows={rows.map((row) => ({ label: row.faculty_name, value: row.publications_score }))} formatter={percent} />
              <MiniBarChart title="Projects component" subtitle="Research source" rows={rows.map((row) => ({ label: row.faculty_name, value: row.projects_score }))} formatter={percent} />
              <MiniBarChart title="Patent and IPR component" subtitle="Research source" rows={rows.map((row) => ({ label: row.faculty_name, value: row.patents_score }))} formatter={percent} />
            </section>
          )}
          {activeTab === 'Trends' && (
            <section className="executive-chart-row two-col">
              <MiniBarChart title="Balanced performance trend by academic year" subtitle="Balanced leaders" rows={yearRows} />
              <MiniBarChart title="Faculty quadrant distribution" subtitle="Quadrants" rows={[
                { label: 'Balanced Leaders', value: balanced.length },
                { label: 'Teaching Focused', value: teachingFocused.length },
                { label: 'Research Focused', value: researchFocused.length },
                { label: 'Development Opportunity', value: development.length },
              ]} />
            </section>
          )}

          <FacultyBalanceTable rows={rows} />
        </>
      )}
    </main>
  )
}
