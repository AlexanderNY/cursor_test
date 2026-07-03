interface GameOverScreenProps {
  onBackToMenu: () => void
}

export function GameOverScreen({ onBackToMenu }: GameOverScreenProps) {
  return (
    <div className="bowl-overlay">
      <div className="bowl-overlay-card">
        <h2 className="bowl-overlay-title">Game Over</h2>
        <p className="bowl-subtitle">Вес упал до нуля. Попробуйте ещё раз.</p>
        <button type="button" className="bowl-btn bowl-btn-primary" onClick={onBackToMenu}>
          В меню
        </button>
      </div>
    </div>
  )
}
