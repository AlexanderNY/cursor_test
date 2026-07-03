interface LoadingScreenProps {
  progress: number
  label: string
}

export function LoadingScreen({ progress, label }: LoadingScreenProps) {
  const safeProgress = Math.min(100, Math.max(0, progress))

  return (
    <div className="bowl-screen bowl-loading">
      <div className="bowl-loading-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">9to18.ru</span>
        </div>
        <h1 className="bowl-title">Загрузка игры</h1>
        <p className="bowl-subtitle">{label}</p>
        <div className="bowl-progress-track" role="progressbar" aria-valuenow={safeProgress} aria-valuemin={0} aria-valuemax={100}>
          <div className="bowl-progress-fill" style={{ width: `${safeProgress}%` }} />
        </div>
        <p className="bowl-progress-text">{safeProgress}%</p>
      </div>
    </div>
  )
}
