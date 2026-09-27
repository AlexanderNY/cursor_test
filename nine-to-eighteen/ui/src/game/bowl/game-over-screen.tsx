interface GameOverScreenProps {
  enemiesEaten?: number
  creditsGained?: number
  score?: number
  highScore?: number
  victory?: boolean
  onBackToMenu: () => void
}

export function GameOverScreen({
  enemiesEaten = 0,
  creditsGained = 0,
  score = 0,
  highScore = 0,
  victory = false,
  onBackToMenu,
}: GameOverScreenProps) {
  return (
    <div className="bowl-overlay">
      <div className="bowl-overlay-card">
        <h2 className="bowl-overlay-title">{victory ? 'Победа!' : 'Game Over'}</h2>
        <p className="bowl-subtitle">
          {victory
            ? 'Вы прошли все пять сеттингов — от унитаза до моря.'
            : 'Вес упал до нуля. Попробуйте ещё раз.'}
        </p>
        <p className="bowl-subtitle">
          Очки: {score}
          {highScore > 0 ? ` · рекорд: ${highScore}` : ''}
        </p>
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
