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
    setLoading(true)
    setError('')
    setDemoMode(false)

    try {
      const results = await Promise.allSettled([
        researchAnalyticsApi.overview(),
        researchAnalyticsApi.indexing(),
        researchAnalyticsApi.faculty(filters),
        researchAnalyticsApi.trend(),
        researchAnalyticsApi.projects(),
        researchAnalyticsApi.scores(),
        researchAnalyticsApi.topFaculty(10),
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
        setData(mockResearchAnalytics)
        setDemoMode(true)
        const firstErr = results.find((r) => r.status === 'rejected')?.reason?.message || 'Unable to connect to live API.'
        setError(`${firstErr} Showing demo fallback until FastAPI is connected.`)
      }
    } catch (requestError) {
      setData(mockResearchAnalytics)
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
