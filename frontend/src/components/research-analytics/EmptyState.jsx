export default function EmptyState({ title = 'No records found', message = 'Try changing filters or confirm the backend is connected.' }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  )
}

