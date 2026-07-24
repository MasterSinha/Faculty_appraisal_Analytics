import { useState } from 'react'

const navGroups = [
  {
    title: 'Research Analytics',
    items: [
      { id: 'overview',      label: 'Overview',             icon: '📊' },
      { id: 'publications',  label: 'Publications',          icon: '📄' },
      { id: 'books',         label: 'Books',                 icon: '📚' },
      { id: 'patents',       label: 'Patents & IPR',         icon: '💡' },
      { id: 'projects',      label: 'Projects & Funding',    icon: '💰' },
      { id: 'guidance',      label: 'Research Guidance',     icon: '🎓' },
      { id: 'conferences',   label: 'Conferences & Awards',  icon: '🏆' },
      { id: 'pipeline',      label: 'Innovation Pipeline',   icon: '⚙️' },
    ],
  },
  {
    title: 'Performance',
    items: [
      { id: 'faculty-performance',    label: 'Faculty Performance',    icon: '👤' },
      { id: 'department-performance', label: 'Department Performance', icon: '🏢' },
      { id: 'school-performance',     label: 'School Performance',     icon: '🏛️' },
      { id: 'teaching-balance',       label: 'Teaching vs Research',   icon: '⚖️' },
    ],
  },
  {
    title: 'Administration',
    items: [
      { id: 'completion',   label: 'Appraisal Completion', icon: '✅' },
      { id: 'data-quality', label: 'Data Quality',         icon: '🛡️' },
      { id: 'alerts',       label: 'Verification Alerts',  icon: '⚠️' },
    ],
  },
]

export default function Sidebar({ activePage, onPageSelect, mobileOpen, onMobileClose }) {
  const [collapsedGroups, setCollapsedGroups] = useState({})

  function toggleGroup(groupTitle) {
    setCollapsedGroups((prev) => ({ ...prev, [groupTitle]: !prev[groupTitle] }))
  }

  return (
    <>
      <aside className={`analytics-sidebar ${mobileOpen ? 'open' : ''}`}>
        {/* Brand */}
        <div className="sidebar-brand">
          <span className="brand-logo">🎓</span>
          <div className="brand-text">
            <h2>Faculty Analytics</h2>
            <span>Appraisal Intelligence</span>
          </div>
          <button className="mobile-close" onClick={onMobileClose} aria-label="Close menu">×</button>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav" aria-label="Dashboard sections">
          {navGroups.map((group) => {
            const isCollapsed = collapsedGroups[group.title]
            return (
              <div key={group.title} className="nav-group">
                <button
                  type="button"
                  className="nav-group-title"
                  onClick={() => toggleGroup(group.title)}
                  aria-expanded={!isCollapsed}
                >
                  <span>{group.title}</span>
                  <span className="chevron">{isCollapsed ? '►' : '▼'}</span>
                </button>
                {!isCollapsed && (
                  <ul className="nav-list">
                    {group.items.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                          onClick={() => { onPageSelect(item.id); onMobileClose() }}
                          aria-current={activePage === item.id ? 'page' : undefined}
                        >
                          <span className="nav-icon">{item.icon}</span>
                          <span className="nav-label">{item.label}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot online" />
            <span>Live PostgreSQL Sync</span>
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <div className="sidebar-backdrop" onClick={onMobileClose} aria-hidden="true" />
      )}
    </>
  )
}
