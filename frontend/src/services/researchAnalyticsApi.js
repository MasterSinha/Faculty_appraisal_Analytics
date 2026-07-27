import { sanitizeFilters } from '../utils/filterUtils'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const API_PREFIX = `${API_BASE_URL}/api/v1/analytics/research`
const REQUEST_TIMEOUT_MS = 15000
const ANALYTICS_RECORD_LIMIT = 5000
const ANALYTICS_MAX_PAGES = 50

function buildUrl(path, params = {}) {
  const base = typeof window === 'undefined' ? 'http://localhost' : window.location.origin
  const url = new URL(`${API_PREFIX}${path}`, base)
  const cleanParams = sanitizeFilters(params)

  Object.entries(cleanParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key === 'year' ? 'academic_year' : key, value)
    }
  })

  return url
}

function normalizeOverview(data = {}) {
  return {
    ...data,
    total_faculty: data.total_active_faculty ?? data.total_faculty ?? 0,
    faculty_with_research: data.faculty_with_journal_publication ?? data.faculty_with_research ?? 0,
    total_research_papers: data.total_journal_publications ?? data.total_research_papers ?? 0,
    total_projects: data.total_research_projects ?? data.total_projects ?? 0,
    total_patents: data.total_patents ?? 0,
    total_books: data.total_book_publications ?? data.total_books ?? 0,
    total_conferences: data.total_conferences ?? 0,
    total_funding: data.total_sanctioned_funding ?? data.total_funding ?? 0,
    total_vc_score: data.total_research_score || 0,
  }
}

function mapFacultyPage(data = {}) {
  return {
    ...data,
    items: (data.items || data.faculty || []).map((item) => ({
      ...item,
      faculty_id: item.faculty_email || item.email || item.faculty_id,
      faculty_name: item.full_name || item.faculty_name,
      total_research_papers: item.journal_publications ?? item.total_research_papers ?? 0,
      book_publications: item.book_publications ?? item.books ?? 0,
      conference_publications: item.conferences ?? item.conference_publications ?? 0,
      research_projects: item.research_projects ?? item.projects ?? 0,
      total_funding: item.project_funding ?? item.total_funding ?? item.funding ?? 0,
      total_vc_score: item.total_research_score ?? item.total_vc_score ?? 0,
    })),
    page: data.page || 1,
    page_size: data.page_size || 10,
    total: data.total || (data.items || data.faculty || []).length,
    total_pages: data.total_pages || 1,
  }
}

function recordParams(params = {}) {
  return { ...params, page: 1, page_size: ANALYTICS_RECORD_LIMIT }
}

function appendArrayMap(target, source, skipKeys = []) {
  Object.entries(source || {}).forEach(([key, value]) => {
    if (!skipKeys.includes(key) && Array.isArray(value)) {
      target[key] = [...(target[key] || []), ...value]
    }
  })
}

function mergePagedResponses(firstPage, pages) {
  const combined = { ...firstPage }

  if (Array.isArray(firstPage.items)) {
    combined.items = [...firstPage.items]
    pages.forEach((page) => {
      combined.items.push(...(Array.isArray(page.items) ? page.items : []))
    })
  } else if (firstPage.items && typeof firstPage.items === 'object') {
    combined.items = { ...firstPage.items }
    pages.forEach((page) => appendArrayMap(combined.items, page.items))
  }

  Object.entries(firstPage || {}).forEach(([key, value]) => {
    if (key !== 'items' && Array.isArray(value)) {
      combined[key] = [...value]
    }
  })
  pages.forEach((page) => appendArrayMap(combined, page, ['items']))

  combined.page = 1
  combined.total = Array.isArray(combined.items) ? combined.items.length : (firstPage.total || combined.total || 0)
  combined.total_pages = 1

  return combined
}

function authHeaders() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, params = {}, options = {}) {
  const url = buildUrl(path, params)
  const controller = new AbortController()
  const timeoutMs = options.timeoutMs || REQUEST_TIMEOUT_MS
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, { headers: authHeaders(), signal: controller.signal })
    if (!response.ok) {
      let detail = ''
      try {
        const errBody = await response.json()
        detail = errBody.detail || ''
      } catch {
        // ignore json parse error
      }
      const message = response.status === 401
        ? 'Authentication token required or invalid.'
        : (detail ? `[HTTP ${response.status}] ${detail}` : `[HTTP ${response.status}] Unable to load research analytics.`)
      throw new Error(message)
    }
    return response.json()
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s. Check FastAPI logs and database query speed.`, { cause: error })
    }
    throw error
  } finally {
    globalThis.clearTimeout(timeoutId)
  }
}

async function requestAllPages(path, params = {}) {
  const firstPage = await request(path, recordParams(params))
  const returnedPageSize = Number(firstPage.page_size || firstPage.limit || ANALYTICS_RECORD_LIMIT)
  const total = Number(firstPage.total || 0)
  const declaredPages = Number(firstPage.total_pages || 0)
  const calculatedPages = total && returnedPageSize ? Math.ceil(total / returnedPageSize) : 1
  const totalPages = Math.min(Math.max(declaredPages || calculatedPages || 1, 1), ANALYTICS_MAX_PAGES)

  if (totalPages <= 1) return firstPage

  const remainingPages = await Promise.all(
    Array.from({ length: totalPages - 1 }, (_, index) =>
      request(path, { ...recordParams(params), page: index + 2, page_size: returnedPageSize }),
    ),
  )

  return mergePagedResponses(firstPage, remainingPages)
}

export const researchAnalyticsApi = {
  dashboard: async (params = {}) => {
    const data = await request('/dashboard', params)
    const overview = normalizeOverview(data.overview || data)
    const categorySummary = data.category_summary || data.categories || []

    return {
      raw: data,
      overview,
      kpis: data.kpis || [],
      indexing: categorySummary.map((item) => ({
        indexing: item.category || item.indexing || item.label || item.name,
        total_papers: item.total_papers ?? item.total ?? item.value ?? item.count ?? 0,
        total_faculty: item.total_faculty ?? item.faculty_count ?? 0,
        vc_score: item.vc_score ?? 0,
      })),
      faculty: mapFacultyPage(data.faculty_summary || data.faculty || {}),
      trend: (data.trend || data.yearly_trend || []).map((item) => ({
        ...item,
        year: item.year || item.academic_year,
        total_papers: item.total_papers ?? item.journal_publications ?? item.total ?? item.value ?? 0,
      })),
      projects: data.funding_summary || [],
      scores: data.scores || null,
      topFaculty: data.top_faculty || [],
      topJournals: data.top_journals || [],
      departments: {
        items: data.department_summary || [],
        page: 1,
        page_size: 100,
        total: (data.department_summary || []).length,
        total_pages: 1,
      },
      schoolSummary: data.school_summary || [],
      insights: data.insights || [],
      attentionAlerts: data.attention_alerts || [],
      dataQuality: data.data_quality || {},
      filterOptions: data.filter_options || null,
      meta: data.meta || {},
    }
  },
  overview: async (params = {}) => {
    const data = await request('/overview', params)
    return normalizeOverview(data)
  },
  indexing: async (params = {}) => {
    const overview = await request('/overview', params)
    return {
      data: [
        { indexing: 'Journals', total_papers: overview.total_journal_publications, total_faculty: overview.faculty_with_journal_publication, vc_score: 0 },
        { indexing: 'Books', total_papers: overview.total_book_publications, total_faculty: overview.faculty_with_book_publication, vc_score: 0 },
        { indexing: 'Patents', total_papers: overview.total_patents, total_faculty: 0, vc_score: 0 },
        { indexing: 'Projects', total_papers: overview.total_research_projects, total_faculty: 0, vc_score: 0 },
      ],
    }
  },
  faculty: async (params) => {
    const data = await request('/faculty', params)
    return mapFacultyPage(data)
  },
  facultyDetail: async (facultyEmail) => {
    const data = await request(`/faculty/${encodeURIComponent(facultyEmail)}`)
    const profile = data.profile || {}
    return {
      faculty: {
        ...profile,
        faculty_id: profile.email,
        faculty_name: profile.full_name,
      },
      score_summary: {},
      records: {
        journal_publications: data.journals || [],
        book_publications: data.books || [],
        conferences: data.conferences || [],
        patents: [...(data.patents || []), ...(data.ipr || [])],
        research_projects: [...(data.projects || []), ...(data.external_projects || []), ...(data.proposals || [])],
        research_guidance: data.guidance || [],
        awards: data.awards || [],
      },
    }
  },
  trend: async (params = {}) => {
    const data = await request('/trends', params)
    return {
      data: (data.publications_by_academic_year || []).map((item) => ({
        year: item.academic_year,
        total_papers: item.journal_publications,
      })),
    }
  },
  projects: async (params = {}) => {
    const data = await request('/funding', params)
    return {
      data: [
        { group: 'funding_agency', name: 'Total sanctioned', total: 1, amount: data.total_sanctioned_funding },
        { group: 'funding_agency', name: 'External funded', total: 1, amount: data.external_funded_amount },
      ],
    }
  },
  scores: async (params = {}) => {
    const data = await request('/overview', params)
    return {
      self_score: data.total_journal_publications,
      director_score: data.total_book_publications,
      dean_score: data.total_research_projects,
      vc_score: data.total_patents,
      reduced_by_director: 0,
      reduced_by_dean: 0,
      reduced_by_vc: 0,
      unchanged_records: 0,
    }
  },
  topFaculty: async (limit = 10, params = {}) => {
    const data = await request('/faculty', { ...params, page_size: limit })
    return {
      data: (data.items || []).map((item) => ({
        ...item,
        faculty_id: item.faculty_email,
        faculty_name: item.full_name,
        total_research_papers: item.journal_publications,
      })),
    }
  },
  topJournals: async () => ({ data: [] }),
  filters: () => request('/filters'),
  departments: (params) => request('/departments', { ...params, page: 1, page_size: 500 }),
  insights: (params) => request('/insights', params),
  dataQuality: (params) => requestAllPages('/data-quality', params),
  books: (params) => requestAllPages('/books', params),
  publications: (params) => requestAllPages('/publications', params),
  patents: (params) => requestAllPages('/patents', params),
  projectRecords: (params) => requestAllPages('/projects', params),
  funding: (params) => request('/funding', params),
  guidance: (params) => requestAllPages('/guidance', params),
  conferencesAwards: (params) => requestAllPages('/conferences-awards', params),
  innovationPipeline: (params) => requestAllPages('/innovation-pipeline', params),
  facultyPerformance: (params) => requestAllPages('/faculty-performance', params),
  departmentPerformance: (params) => requestAllPages('/department-performance', params),
  schoolPerformance: (params) => requestAllPages('/school-performance', params),
  teachingResearchBalance: (params) => requestAllPages('/teaching-research-balance', params),
  appraisalCompletion: (params) => requestAllPages('/appraisal-completion', params),
  exportUrl: (params = {}) => {
    return buildUrl('/export', params).toString()
  },
  authHeaders,
}
