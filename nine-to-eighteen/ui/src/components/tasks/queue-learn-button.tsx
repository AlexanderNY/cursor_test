type QueueLearnButtonProps = {
  queued: boolean
  busy: boolean
  onQueue: () => void
}

export function QueueLearnButton({ queued, busy, onQueue }: QueueLearnButtonProps) {
  if (queued) {
    return <span className="learn-badge">В задачах</span>
  }
  return (
    <button
      type="button"
      className="learn-admin-btn tasks-queue-btn"
      disabled={busy}
      onClick={onQueue}
    >
      {busy ? 'Добавляю…' : 'В задачи'}
    </button>
  )
}
