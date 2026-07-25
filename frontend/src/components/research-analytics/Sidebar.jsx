import { useState } from 'react'

const Icon = ({ d, size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
    {Array.isArray(d) ? d.map((p, i) => <path key={i} d={p} />) : <path d={d} />}
  </svg>
)

const ICONS = {
  overview:                <Icon d={['M3 3h7v7H3z','M14 3h7v7h-7z','M14 14h7v7h-7z','M3 14h7v7H3z']} />,
  publications:            <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" />,
  books:                   <Icon d={['M4 19.5A2.5 2.5 0 0 1 6.5 17H20','M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z']} />,
  patents:                 <Icon d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />,
  projects:                <Icon d={['M12 2v20','M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6']} />,
  guidance:                <Icon d={['M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2','M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z','M23 21v-2a4 4 0 0 0-3-3.87','M16 3.13a4 4 0 0 1 0 7.75']} />,
  conferences:             <Icon d={['M8 2v4','M16 2v4','M3 10h18','M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z']} />,
  pipeline:                <Icon d="M22 12h-4l-3 9L9 3l-3 9H2" />,
  'faculty-performance':   <Icon d={['M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2','M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z']} />,
  'department-performance':<Icon d={['M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z','M9 22V12h6v10']} />,
  'school-performance':    <Icon d={['M2 20h20','M4 20V10','M20 20V10','M12 2l8 8H4z','M9 20v-5h6v5']} />,
  'teaching-balance':      <Icon d={['M12 3v18','M3 9l4-4 4 4','M17 19l4-4-4-4','M7 9h10','M7 15h10']} />,
  completion:              <Icon d={['M9 11l3 3L22 4','M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11']} />,
  'data-quality':          <Icon d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
}

const navGroups = [
  {
    title: 'Research Analytics',
    items: [
      { id: 'overview',     label: 'Overview' },
      { id: 'publications', label: 'Publications' },
      { id: 'books',        label: 'Books' },
      { id: 'patents',      label: 'Patents & IPR' },
      { id: 'projects',     label: 'Projects & Funding' },
      { id: 'guidance',     label: 'Research Guidance' },
      { id: 'conferences',  label: 'Conferences & Awards' },
      { id: 'pipeline',     label: 'Innovation Pipeline' },
    ],
  },
  {
    title: 'Performance',
    items: [
      { id: 'faculty-performance',     label: 'Faculty Performance' },
      { id: 'department-performance',  label: 'Department Performance' },
      { id: 'school-performance',      label: 'School Performance' },
      { id: 'teaching-balance',        label: 'Teaching vs Research' },
    ],
  },
  {
    title: 'Administration',
    items: [
      { id: 'completion',   label: 'Appraisal Completion' },
      { id: 'data-quality', label: 'Data Quality' },
    ],
  },
]

export default function Sidebar({ activePage, onPageSelect, mobileOpen, onMobileClose }) {
  const [collapsed, setCollapsed] = useState({})
  const toggle = (t) => setCollapsed((p) => ({ ...p, [t]: !p[t] }))

  return (
    <>
      <aside className={`analytics-sidebar${mobileOpen ? ' open' : ''}`}>

        {/* ── Brand ── */}
        <div className="sidebar-brand">
          <div className="brand-icon-wrap" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
              <path d="M6 12v5c3 3 9 3 12 0v-5" />
            </svg>
          </div>
          <div className="brand-text">
            <h2>Faculty Analytics</h2>
            <span>Appraisal Intelligence</span>
          </div>
          <button className="mobile-close" onClick={onMobileClose} aria-label="Close menu">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ── Nav ── */}
        <nav className="sidebar-nav" aria-label="Dashboard navigation">
          {navGroups.map((group) => {
            const isCollapsed = collapsed[group.title]
            return (
              <div key={group.title} className="nav-group">
                <button
                  type="button"
                  className="nav-group-title"
                  onClick={() => toggle(group.title)}
                  aria-expanded={!isCollapsed}
                >
                  <span>{group.title}</span>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
                    strokeLinejoin="round" aria-hidden="true"
                    style={{ transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)', transition: 'transform 0.2s', flexShrink: 0 }}>
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>

                {!isCollapsed && (
                  <ul className="nav-list">
                    {group.items.map((item) => {
                      const active = activePage === item.id
                      return (
                        <li key={item.id}>
                          <button
                            type="button"
                            className={`nav-item${active ? ' active' : ''}`}
                            onClick={() => { onPageSelect(item.id); onMobileClose() }}
                            aria-current={active ? 'page' : undefined}
                          >
                            <span className="nav-icon">{ICONS[item.id]}</span>
                            <span className="nav-label">{item.label}</span>
                          </button>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </div>
            )
          })}
        </nav>

        {/* ── Footer ── */}
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
