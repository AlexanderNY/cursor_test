type QueueLearnButtonProps = {
  queued: boolean
  busy: boolean
  label?: string
  queuedLabel?: string
  onQueue: () => void
}

export function QueueLearnButton({
  queued,
  busy,
  label = 'В задачи',
  queuedLabel = 'В списке',
  onQueue,
}: QueueLearnButtonProps) {
  if (queued) {
    return <span className="learn-badge">{queuedLabel}</span>
  }
  return (
    <button
      type="button"
      className="learn-admin-btn tasks-queue-btn"
      disabled={busy}
      onClick={onQueue}
    >
      {busy ? 'Добавляю…' : label}
    </button>
  )
}
