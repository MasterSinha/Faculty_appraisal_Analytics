export function departmentLabel(recordOrDepartment, fallbackSchool = '') {
  const department = typeof recordOrDepartment === 'object'
    ? recordOrDepartment?.department
    : recordOrDepartment
  const school = typeof recordOrDepartment === 'object'
    ? recordOrDepartment?.school
    : fallbackSchool

  const cleanDepartment = String(department || '').trim()
  const cleanSchool = String(school || '').trim()

  if (cleanDepartment) return cleanDepartment
  if (cleanSchool) return `${cleanSchool} (No department mapped)`
  return 'No department mapped'
}
