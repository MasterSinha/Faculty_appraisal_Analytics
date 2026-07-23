export default function AnalyticsHeader({ demoMode, onExportCsv, onExportXlsx, onRefresh }) {
  return (
    <header className="analytics-header">
      <div>
        <span className="eyebrow">Faculty Appraisal Management System</span>
        <h1>Research Analytics Dashboard</h1>
        <p>Research papers, indexing, projects, funding, patents, and reviewer score movement.</p>
      </div>
      <div className="header-actions">
        <button type="button" onClick={onRefresh}>Refresh</button>
        <button type="button" disabled={demoMode} title={demoMode ? 'Connect FastAPI to export live records' : 'Export CSV'} onClick={onExportCsv}>CSV</button>
        <button type="button" className="primary-action" disabled={demoMode} title={demoMode ? 'Connect FastAPI to export live records' : 'Export Excel'} onClick={onExportXlsx}>Excel</button>
      </div>
    </header>
  )
}
