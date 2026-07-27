import { useCallback, useEffect, useMemo, useState } from 'react'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'
import { sanitizeFilters } from '../utils/filterUtils'

const initialFilters = {
  page: 1,
  page_size: 10,
  search: '',
  school: '',
  department: '',
  indexing: '',
  year: '',
  sort_by: 'total_research_papers',
  sort_order: 'desc',
}

function matchesFilters(faculty, filters) {
  const school = String(faculty.school || '').toLowerCase()
  const department = String(faculty.department || '').toLowerCase()
  const designation = String(faculty.designation || '').toLowerCase()
  const searchTarget = `${faculty.faculty_name || ''} ${faculty.full_name || ''} ${faculty.employee_id || ''} ${faculty.email || ''}`.toLowerCase()

  return (!filters.school || school === String(filters.school).toLowerCase())
    && (!filters.department || department === String(filters.department).toLowerCase())
    && (!filters.designation || designation === String(filters.designation).toLowerCase())
    && (!filters.search || searchTarget.includes(String(filters.search).toLowerCase()))
}

function buildFilteredMock(filters) {
  const items = mockResearchAnalytics.faculty.items.filter((faculty) => matchesFilters(faculty, filters))
  const totalResearchPapers = items.reduce((sum, faculty) => sum + Number(faculty.total_research_papers || 0), 0)
  const totalBooks = items.reduce((sum, faculty) => sum + Number(faculty.book_publications || 0), 0)
  const totalProjects = items.reduce((sum, faculty) => sum + Number(faculty.research_projects || 0), 0)
  const totalPatents = items.reduce((sum, faculty) => sum + Number(faculty.patents || 0), 0)
  const totalConferences = items.reduce((sum, faculty) => sum + Number(faculty.conference_publications || 0), 0)
  const totalFunding = items.reduce((sum, faculty) => sum + Number(faculty.total_funding || 0), 0)
  const publishingFaculty = items.filter((faculty) => Number(faculty.total_research_papers || 0) > 0).length

  const departments = Object.values(items.reduce((acc, faculty) => {
    const department = faculty.department || `${faculty.school || 'School'} (No department mapped)`
    acc[department] = acc[department] || {
      department,
      school: faculty.school,
      journal_publications: 0,
      total_project_funding: 0,
      faculty_count: 0,
      publishing_faculty: 0,
    }
    acc[department].journal_publications += Number(faculty.total_research_papers || 0)
    acc[department].total_project_funding += Number(faculty.total_funding || 0)
    acc[department].faculty_count += 1
    acc[department].publishing_faculty += Number(faculty.total_research_papers || 0) > 0 ? 1 : 0
    acc[department].publication_participation_percentage = acc[department].faculty_count
      ? (acc[department].publishing_faculty / acc[department].faculty_count) * 100
      : 0
    return acc
  }, {}))

  return {
    ...mockResearchAnalytics,
    overview: {
      ...mockResearchAnalytics.overview,
      total_faculty: items.length,
      total_active_faculty: items.length,
      faculty_with_research: publishingFaculty,
      faculty_with_journal_publication: publishingFaculty,
      total_research_papers: totalResearchPapers,
      total_journal_publications: totalResearchPapers,
      total_books: totalBooks,
      total_book_publications: totalBooks,
      total_projects: totalProjects,
      total_research_projects: totalProjects,
      total_patents: totalPatents,
      total_conferences: totalConferences,
      total_funding: totalFunding,
      total_sanctioned_funding: totalFunding,
      publication_participation_rate: items.length ? (publishingFaculty / items.length) * 100 : 0,
    },
    faculty: {
      ...mockResearchAnalytics.faculty,
      items,
      total: items.length,
      total_pages: 1,
    },
    departments: {
      items: departments,
      page: 1,
      page_size: 100,
      total: departments.length,
      total_pages: 1,
    },
    topFaculty: items
      .map((faculty) => ({ faculty_id: faculty.faculty_id, faculty_name: faculty.faculty_name, total_research_papers: faculty.total_research_papers }))
      .sort((a, b) => Number(b.total_research_papers || 0) - Number(a.total_research_papers || 0)),
  }
}

function emptyFaculty() {
  return { items: [], page: 1, page_size: 10, total: 0, total_pages: 0 }
}

function emptyDepartments() {
  return { items: [], page: 1, page_size: 100, total: 0, total_pages: 0 }
}

function emptyFilterOptions() {
  return { schools: [], departments: [], years: [], indexing_categories: [], project_statuses: [], funding_agencies: [] }
}

function fulfilled(result, fallback = null) {
  return result.status === 'fulfilled' ? result.value : fallback
}

function firstFailureMessage(results) {
  return results.find((result) => result.status === 'rejected')?.reason?.message || ''
}

function hasLiveCoreData({ overview, faculty, trend, departments }) {
  return Boolean(
    overview
    || Number(faculty?.total || 0) > 0
    || Number(departments?.total || 0) > 0
    || (trend || []).length > 0,
  )
}

function indexingFromOverview(overview) {
  if (!overview) return []
  return [
    { indexing: 'Journals', total_papers: overview.total_journal_publications || overview.total_research_papers || 0, total_faculty: overview.faculty_with_journal_publication || 0, vc_score: 0 },
    { indexing: 'Books', total_papers: overview.total_book_publications || overview.total_books || 0, total_faculty: overview.faculty_with_book_publication || 0, vc_score: 0 },
    { indexing: 'Patents', total_papers: overview.total_patents || 0, total_faculty: 0, vc_score: 0 },
    { indexing: 'Projects', total_papers: overview.total_research_projects || overview.total_projects || 0, total_faculty: 0, vc_score: 0 },
  ]
}

export function useResearchAnalytics() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState({
    overview: null,
    indexing: [],
    faculty: emptyFaculty(),
    trend: [],
    projects: [],
    scores: null,
    topFaculty: [],
    topJournals: [],
    departments: emptyDepartments(),
    insights: [],
    attentionAlerts: [],
    dataQuality: {},
    filterOptions: null,
    schoolSummary: [],
    meta: {},
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [demoMode, setDemoMode] = useState(false)

  const updateFilters = useCallback((nextFilters) => {
    setFilters((current) => {
      const nextCleanFilters = sanitizeFilters(nextFilters)
      return { ...current, ...nextCleanFilters, page: nextFilters.page || 1 }
    })
  }, [])

  const refresh = useCallback(async () => {
    setError('')
    setDemoMode(false)

    try {
      const cleanFilters = sanitizeFilters(filters)

      try {
        const dashboard = await researchAnalyticsApi.dashboard(cleanFilters)
        setData((current) => ({
          ...current,
          overview: dashboard.overview || mockResearchAnalytics.overview,
          indexing: dashboard.indexing?.length ? dashboard.indexing : indexingFromOverview(dashboard.overview),
          faculty: dashboard.faculty?.items?.length ? dashboard.faculty : current.faculty,
          trend: dashboard.trend || [],
          projects: dashboard.projects || [],
          scores: dashboard.scores || current.scores || mockResearchAnalytics.scores,
          topFaculty: dashboard.topFaculty || [],
          topJournals: dashboard.topJournals || [],
          departments: dashboard.departments || emptyDepartments(),
          schoolSummary: dashboard.schoolSummary || [],
          insights: dashboard.insights || [],
          attentionAlerts: dashboard.attentionAlerts || [],
          dataQuality: dashboard.dataQuality || {},
          filterOptions: dashboard.filterOptions || current.filterOptions || emptyFilterOptions(),
          meta: dashboard.meta || {},
        }))
        setLoading(false)
        setDemoMode(false)
        return
      } catch (dashboardError) {
        if (!String(dashboardError.message || '').includes('[HTTP 404]')) {
          setError(`Dashboard summary unavailable, loading live sections separately. ${dashboardError.message}`)
        }
      }

      const coreResults = await Promise.allSettled([
        researchAnalyticsApi.overview(cleanFilters),
        researchAnalyticsApi.faculty(cleanFilters),
        researchAnalyticsApi.trend(cleanFilters),
      ])

      const [overviewRes, facultyRes, trendRes] = coreResults

      const overview = fulfilled(overviewRes)
      const faculty = fulfilled(facultyRes, emptyFaculty())
      const trend = fulfilled(trendRes)?.data || []
      const departments = emptyDepartments()

      if (hasLiveCoreData({ overview, faculty, trend, departments })) {
        setData((current) => ({
          ...current,
          overview: overview || mockResearchAnalytics.overview,
          indexing: indexingFromOverview(overview),
          faculty,
          trend,
          departments,
          filterOptions: current.filterOptions || emptyFilterOptions(),
        }))
        setLoading(false)
        setDemoMode(false)

        const secondaryResults = await Promise.allSettled([
          researchAnalyticsApi.indexing(cleanFilters),
          researchAnalyticsApi.projects(cleanFilters),
          researchAnalyticsApi.scores(cleanFilters),
          researchAnalyticsApi.topFaculty(10, cleanFilters),
          researchAnalyticsApi.topJournals(10),
          researchAnalyticsApi.filters(),
          researchAnalyticsApi.departments(cleanFilters),
          researchAnalyticsApi.insights(cleanFilters),
          researchAnalyticsApi.dataQuality(cleanFilters),
        ])

        const [indexingRes, projectsRes, scoresRes, topFacultyRes, topJournalsRes, filterOptionsRes, departmentsRes, insightsRes, dataQualityRes] = secondaryResults
        const indexing = fulfilled(indexingRes)?.data || indexingFromOverview(overview)
        const projects = fulfilled(projectsRes)?.data || []
        const scores = fulfilled(scoresRes)
        const topFaculty = fulfilled(topFacultyRes)?.data || []
        const topJournals = fulfilled(topJournalsRes)?.data || []
        const filterOptions = fulfilled(filterOptionsRes)
        const liveDepartments = fulfilled(departmentsRes, emptyDepartments())
        const insights = fulfilled(insightsRes)?.insights || []
        const dataQuality = fulfilled(dataQualityRes) || {}

        setData((current) => ({
          ...current,
          indexing,
          projects,
          scores: scores || mockResearchAnalytics.scores,
          topFaculty,
          topJournals,
          filterOptions: filterOptions || current.filterOptions || emptyFilterOptions(),
          departments: liveDepartments,
          insights,
          dataQuality,
        }))

        const failedCount = [...coreResults, ...secondaryResults].filter((result) => result.status === 'rejected').length
        if (failedCount > 0) {
          setError(`Live data loaded partially. ${firstFailureMessage([...coreResults, ...secondaryResults])}`)
        }
      } else {
        setData(buildFilteredMock(cleanFilters))
        setDemoMode(true)
        const firstErr = firstFailureMessage(coreResults) || 'Unable to connect to live API.'
        setError(`${firstErr} Showing demo fallback until FastAPI is connected.`)
        setLoading(false)
      }
    } catch (requestError) {
      setData(buildFilteredMock(sanitizeFilters(filters)))
      setDemoMode(true)
      setError(`${requestError.message} Showing demo data.`)
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      refresh()
    }, 0)

    return () => window.clearTimeout(timeoutId)
  }, [refresh])

  const exportCsv = useCallback(() => {
    window.location.href = researchAnalyticsApi.exportUrl({ ...sanitizeFilters(filters), format: 'csv' })
  }, [filters])

  const exportXlsx = useCallback(() => {
    window.location.href = researchAnalyticsApi.exportUrl({ ...sanitizeFilters(filters), format: 'xlsx' })
  }, [filters])

  return useMemo(
    () => ({ data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx }),
    [data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx],
  )
}
