interface GameOverScreenProps {
  enemiesEaten?: number
  creditsGained?: number
  onBackToMenu: () => void
}

export function GameOverScreen({
  enemiesEaten = 0,
  creditsGained = 0,
  onBackToMenu,
}: GameOverScreenProps) {
  return (
    <div className="bowl-overlay">
      <div className="bowl-overlay-card">
        <h2 className="bowl-overlay-title">Game Over</h2>
        <p className="bowl-subtitle">Вес упал до нуля. Попробуйте ещё раз.</p>
        <p className="bowl-subtitle">
          Съедено врагов: {enemiesEaten}
          {creditsGained > 0 ? ` · +${creditsGained} кредитов на заказы` : ''}
        </p>
        <button type="button" className="bowl-btn bowl-btn-primary" onClick={onBackToMenu}>
          В меню
        </button>
      </div>
    </div>
  )
}
