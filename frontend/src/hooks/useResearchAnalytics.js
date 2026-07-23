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
      const [overview, indexing, faculty, trend, projects, scores, topFaculty, topJournals, filterOptions] =
        await Promise.all([
          researchAnalyticsApi.overview(),
          researchAnalyticsApi.indexing(),
          researchAnalyticsApi.faculty(filters),
          researchAnalyticsApi.trend(),
          researchAnalyticsApi.projects(),
          researchAnalyticsApi.scores(),
          researchAnalyticsApi.topFaculty(10),
          researchAnalyticsApi.topJournals(10),
          researchAnalyticsApi.filters(),
        ])

      setData({
        overview,
        indexing: indexing.data || [],
        faculty,
        trend: trend.data || [],
        projects: projects.data || [],
        scores,
        topFaculty: topFaculty.data || [],
        topJournals: topJournals.data || [],
        filterOptions,
      })
    } catch (requestError) {
      setData(mockResearchAnalytics)
      setDemoMode(true)
      setError(`${requestError.message} Showing demo data until FastAPI is connected.`)
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
