const DEFAULT_FILTER_VALUES = new Set([
  'all',
  'none',
  'null',
  'undefined',
  'all schools',
  'all departments',
  'all years',
  'all designations',
  'all categories',
  'all indexing',
])

export function normalizeFilterValue(value) {
  if (value === undefined || value === null) return ''

  const stringValue = String(value).trim()
  const lowerValue = stringValue.toLowerCase()

  if (!stringValue || DEFAULT_FILTER_VALUES.has(lowerValue) || lowerValue.startsWith('all ')) {
    return ''
  }

  return stringValue
}

export function sanitizeFilters(filters = {}) {
  return Object.entries(filters).reduce((cleanFilters, [key, value]) => {
    cleanFilters[key] = normalizeFilterValue(value)
    return cleanFilters
  }, {})
}
