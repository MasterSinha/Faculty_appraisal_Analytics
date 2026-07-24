import { useState } from 'react'

export default function PageHeader({ title, description, lastRefreshed, onRefresh, onExportCsv, onExportXlsx, onMobileMenuToggle }) {
  const [showHelp, setShowHelp] = useState(false)

  return (
    <header className="page-header">
      <div className="header-left">
        <button className="mobile-toggle" type="button" onClick={onMobileMenuToggle} aria-label="Open menu">
          ☰
        </button>
        <div>
          <span className="eyebrow">Faculty Appraisal System</span>
          <h1>{title}</h1>
          <p className="description">{description}</p>
        </div>
      </div>

      <div className="header-actions">
        <span className="last-refreshed">Refreshed: {lastRefreshed || 'Just now'}</span>

        <button type="button" className="btn-secondary" onClick={onRefresh} title="Refresh data from database">
          ↻ Refresh
        </button>
        <button type="button" className="btn-secondary" onClick={onExportCsv} title="Export CSV data">
          ↓ CSV
        </button>
        <button type="button" className="btn-primary" onClick={onExportXlsx} title="Export Excel Report">
          ↓ Excel
        </button>
        <button type="button" className="btn-help" onClick={() => setShowHelp(!showHelp)} title="Metric Definitions">
          ? Help
        </button>
      </div>

      {showHelp && (
        <div className="metric-help-dialog" role="dialog" aria-modal="true" aria-label="Metric Definitions">
          <div className="help-content">
            <h3>Metric Definitions &amp; Guidance</h3>
            <ul>
              <li><strong>Publication Participation Rate:</strong> Percentage of active faculty with at least 1 valid journal publication.</li>
              <li><strong>Papers per Active Faculty:</strong> Total valid journal papers divided by total active faculty.</li>
              <li><strong>Research Diversity Score:</strong> Count of distinct research categories contributed by a faculty member.</li>
              <li><strong>Validation Ratio:</strong> Final approved VC Score as a percentage of self-reported score.</li>
            </ul>
            <button type="button" onClick={() => setShowHelp(false)}>Close</button>
          </div>
        </div>
      )}
    </header>
  )
}
