import { useState } from 'react'

export default function PageHeader({
  title,
  description,
  lastRefreshed,
  onRefresh,
  onExportCsv,
  onExportXlsx,
  onMobileMenuToggle,
}) {
  const [showHelp, setShowHelp] = useState(false)

  return (
    <header className="page-header">
      <div className="header-left">
        {/* Mobile hamburger */}
        <button
          className="mobile-toggle"
          type="button"
          onClick={onMobileMenuToggle}
          aria-label="Open navigation menu"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>

        <div>
          <span className="eyebrow">DY Patil International University</span>
          <h1>{title}</h1>
          {description && <p className="description">{description}</p>}
        </div>
      </div>

      <div className="header-actions">
        {lastRefreshed && (
          <span className="last-refreshed">
            Updated {lastRefreshed}
          </span>
        )}

        <button
          type="button"
          className="btn-secondary"
          onClick={onRefresh}
          title="Refresh data"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 4v6h-6" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          Refresh
        </button>

        <button
          type="button"
          className="btn-secondary"
          onClick={onExportCsv}
          title="Export as CSV"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          CSV
        </button>

        <button
          type="button"
          className="btn-primary"
          onClick={onExportXlsx}
          title="Export Excel report"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export Excel
        </button>

        <button
          type="button"
          className="btn-help"
          onClick={() => setShowHelp(!showHelp)}
          title="Metric definitions"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" />
          </svg>
          Help
        </button>
      </div>

      {showHelp && (
        <div
          className="metric-help-dialog"
          role="dialog"
          aria-modal="true"
          aria-label="Metric Definitions"
          onClick={(e) => { if (e.target === e.currentTarget) setShowHelp(false) }}
        >
          <div className="help-content">
            <h3>Metric Definitions &amp; Guidance</h3>
            <ul>
              <li>
                <strong>Publication Participation Rate:</strong> Percentage of active faculty
                with at least one valid journal publication recorded.
              </li>
              <li>
                <strong>Papers per Active Faculty:</strong> Total valid journal papers
                divided by total active faculty count.
              </li>
              <li>
                <strong>Research Diversity Score:</strong> Number of distinct research
                categories contributed by a faculty member (max 7).
              </li>
              <li>
                <strong>Validation Ratio:</strong> Final VC-approved score as a
                percentage of the self-reported score.
              </li>
              <li>
                <strong>VC Score:</strong> Total verified and approved research score
                by the Vice Chancellor's office.
              </li>
            </ul>
            <button type="button" onClick={() => setShowHelp(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
