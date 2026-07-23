const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const API_PREFIX = `${API_BASE_URL}/api/v1/research-analytics`

function authHeaders() {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, params = {}) {
  const url = new URL(`${API_PREFIX}${path}`)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })

  const response = await fetch(url, { headers: authHeaders() })
  if (!response.ok) {
    const message = response.status === 401 ? 'Sign in to view research analytics.' : 'Unable to load research analytics.'
    throw new Error(message)
  }
  return response.json()
}

export const researchAnalyticsApi = {
  overview: () => request('/overview'),
  indexing: () => request('/publications/indexing'),
  faculty: (params) => request('/faculty', params),
  facultyDetail: (facultyId) => request(`/faculty/${facultyId}`),
  trend: () => request('/publications/trend'),
  projects: () => request('/projects/summary'),
  scores: () => request('/scores/comparison'),
  topFaculty: (limit = 10) => request('/top-faculty', { limit }),
  topJournals: (limit = 10) => request('/top-journals', { limit }),
  filters: () => request('/filters'),
  exportUrl: (params = {}) => {
    const url = new URL(`${API_PREFIX}/export`)
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value)
      }
    })
    return url.toString()
  },
  authHeaders,
}
