import { useCallback, useEffect, useMemo, useState } from 'react'
import { researchAnalyticsApi } from '../services/researchAnalyticsApi'
import { mockResearchAnalytics } from '../services/researchAnalyticsMockData'

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

export function useResearchAnalytics() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState({
    overview: null,
    indexing: [],
    faculty: { items: [], page: 1, page_size: 10, total: 0, total_pages: 0 },
    trend: [],
    projects: [],
    scores: null,
    topFaculty: [],
    topJournals: [],
    departments: { items: [], page: 1, page_size: 100, total: 0, total_pages: 0 },
    insights: [],
    dataQuality: {},
    filterOptions: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [demoMode, setDemoMode] = useState(false)

  const updateFilters = useCallback((nextFilters) => {
    setFilters((current) => ({ ...current, ...nextFilters, page: nextFilters.page || 1 }))
  }, [])

  const refresh = useCallback(async () => {
    await Promise.resolve()
    setLoading((current) => current)
    setError('')
    setDemoMode(false)

    try {
      const results = await Promise.allSettled([
        researchAnalyticsApi.overview(filters),
        researchAnalyticsApi.indexing(filters),
        researchAnalyticsApi.faculty(filters),
        researchAnalyticsApi.trend(filters),
        researchAnalyticsApi.projects(filters),
        researchAnalyticsApi.scores(filters),
        researchAnalyticsApi.topFaculty(10, filters),
        researchAnalyticsApi.topJournals(10),
        researchAnalyticsApi.filters(),
        researchAnalyticsApi.departments(filters),
        researchAnalyticsApi.insights(filters),
        researchAnalyticsApi.dataQuality(filters),
      ])

      const [overviewRes, indexingRes, facultyRes, trendRes, projectsRes, scoresRes, topFacultyRes, topJournalsRes, filterOptionsRes, departmentsRes, insightsRes, dataQualityRes] = results

      const overview = overviewRes.status === 'fulfilled' ? overviewRes.value : null
      const indexing = indexingRes.status === 'fulfilled' ? indexingRes.value?.data || [] : []
      const faculty = facultyRes.status === 'fulfilled' ? facultyRes.value : { items: [], page: 1, page_size: 10, total: 0, total_pages: 0 }
      const trend = trendRes.status === 'fulfilled' ? trendRes.value?.data || [] : []
      const projects = projectsRes.status === 'fulfilled' ? projectsRes.value?.data || [] : []
      const scores = scoresRes.status === 'fulfilled' ? scoresRes.value : null
      const topFaculty = topFacultyRes.status === 'fulfilled' ? topFacultyRes.value?.data || [] : []
      const topJournals = topJournalsRes.status === 'fulfilled' ? topJournalsRes.value?.data || [] : []
      const filterOptions = filterOptionsRes.status === 'fulfilled' ? filterOptionsRes.value : null
      const departments = departmentsRes.status === 'fulfilled' ? departmentsRes.value : { items: [], page: 1, page_size: 100, total: 0, total_pages: 0 }
      const insights = insightsRes.status === 'fulfilled' ? insightsRes.value?.insights || [] : []
      const dataQuality = dataQualityRes.status === 'fulfilled' ? dataQualityRes.value || {} : {}

      const failedCount = results.filter((r) => r.status === 'rejected').length

      if (overview || faculty.total > 0 || indexing.length > 0 || projects.length > 0) {
        setData({
          overview: overview || mockResearchAnalytics.overview,
          indexing,
          faculty,
          trend,
          projects,
          scores: scores || mockResearchAnalytics.scores,
          topFaculty,
          topJournals,
          departments,
          insights,
          dataQuality,
          filterOptions: filterOptions || { schools: [], departments: [], years: [], indexing_categories: [], project_statuses: [], funding_agencies: [] },
        })
        setDemoMode(false)
        if (failedCount > 0) {
          const firstErr = results.find((r) => r.status === 'rejected')?.reason?.message || ''
          setError(`Partial data loaded from live database. (${firstErr})`)
        }
      } else {
        setData(buildFilteredMock(filters))
        setDemoMode(true)
        const firstErr = results.find((r) => r.status === 'rejected')?.reason?.message || 'Unable to connect to live API.'
        setError(`${firstErr} Showing demo fallback until FastAPI is connected.`)
      }
    } catch (requestError) {
      setData(buildFilteredMock(filters))
      setDemoMode(true)
      setError(`${requestError.message} Showing demo data.`)
    } finally {
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
    window.location.href = researchAnalyticsApi.exportUrl({ ...filters, format: 'csv' })
  }, [filters])

  const exportXlsx = useCallback(() => {
    window.location.href = researchAnalyticsApi.exportUrl({ ...filters, format: 'xlsx' })
  }, [filters])

  return useMemo(
    () => ({ data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx }),
    [data, filters, updateFilters, loading, error, demoMode, refresh, exportCsv, exportXlsx],
  )
}
