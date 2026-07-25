export default function AnalyticsHeader({ onExportCsv, onExportXlsx, onRefresh }) {
  return (
    <header className="analytics-header">
      <div>
        <h1>Research Analytics</h1>
        <p>Publication impact · funding pipeline · faculty research scores</p>
      </div>
      <div className="header-actions">
        <span className="live-dot">Live · just now</span>
        <select aria-label="Research cycle">
          <option>Latest cycle</option>
          <option>Cycle 2025-26</option>
          <option>Cycle 2024-25</option>
        </select>
        <button type="button" onClick={onRefresh}>Refresh</button>
        <button type="button" title="Export CSV" onClick={onExportCsv}>CSV</button>
        <button type="button" className="primary-action" title="Export Excel" onClick={onExportXlsx}>Excel</button>
      </div>
    </header>
  )
}
