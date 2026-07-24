const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const API_PREFIX = `${API_BASE_URL}/api/v1/analytics/research`

function buildUrl(path, params = {}) {
  const base = typeof window === 'undefined' ? 'http://localhost' : window.location.origin
  const url = new URL(`${API_PREFIX}${path}`, base)

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })

  return url
}

function authHeaders() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, params = {}) {
  const url = buildUrl(path, params)

  const response = await fetch(url, { headers: authHeaders() })
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
}

export const researchAnalyticsApi = {
  overview: async () => {
    const data = await request('/overview')
    return {
      ...data,
      total_faculty: data.total_active_faculty,
      faculty_with_research: data.faculty_with_journal_publication,
      total_research_papers: data.total_journal_publications,
      total_projects: data.total_research_projects,
      total_patents: data.total_patents,
      total_books: data.total_book_publications,
      total_conferences: data.total_conferences,
      total_funding: data.total_sanctioned_funding,
      total_vc_score: data.total_research_score || 0,
    }
  },
  indexing: async () => {
    const overview = await request('/overview')
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
    return {
      ...data,
      items: (data.items || []).map((item) => ({
        ...item,
        faculty_id: item.faculty_email,
        faculty_name: item.full_name,
        total_research_papers: item.journal_publications,
        book_publications: item.book_publications,
        conference_publications: item.conferences,
        research_projects: item.research_projects,
        total_funding: item.project_funding,
        total_vc_score: item.total_research_score,
      })),
    }
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
  trend: async () => {
    const data = await request('/trends')
    return {
      data: (data.publications_by_academic_year || []).map((item) => ({
        year: item.academic_year,
        total_papers: item.journal_publications,
      })),
    }
  },
  projects: async () => {
    const data = await request('/funding')
    return {
      data: [
        { group: 'funding_agency', name: 'Total sanctioned', total: 1, amount: data.total_sanctioned_funding },
        { group: 'funding_agency', name: 'External funded', total: 1, amount: data.external_funded_amount },
      ],
    }
  },
  scores: async () => {
    const data = await request('/overview')
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
  topFaculty: async (limit = 10) => {
    const data = await request('/faculty', { page_size: limit })
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
  exportUrl: (params = {}) => {
    return buildUrl('/export', params).toString()
  },
  authHeaders,
}
