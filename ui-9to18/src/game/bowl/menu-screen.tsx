interface MenuScreenProps {
  canContinue: boolean
  onNewGame: () => void
  onContinue: () => void
  onSettings: () => void
  onExit: () => void
}

export function MenuScreen({ canContinue, onNewGame, onContinue, onSettings, onExit }: MenuScreenProps) {
  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-menu-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">9to18.ru</span>
        </div>
        <h1 className="bowl-title">Bowl 2D</h1>
        <p className="bowl-subtitle">Собирайте точки, избегайте врагов, следите за весом.</p>

        <div className="bowl-menu-actions">
          <button type="button" className="bowl-btn bowl-btn-primary" onClick={onNewGame}>
            Новая игра
          </button>
          <button
            type="button"
            className="bowl-btn"
            onClick={onContinue}
            disabled={!canContinue}
          >
            Продолжить
          </button>
          <button type="button" className="bowl-btn" onClick={onSettings}>
            Настройки
          </button>
          <button type="button" className="bowl-btn bowl-btn-ghost" onClick={onExit}>
            Выйти
          </button>
        </div>
      </div>
    </div>
  )
}
