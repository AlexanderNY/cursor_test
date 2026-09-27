import { BOWL_STAGES, type BowlStageId } from './stages'

interface MenuScreenProps {
  canContinue: boolean
  highScore?: number
  selectedStage: BowlStageId
  onSelectStage: (stage: BowlStageId) => void
  onNewGame: () => void
  onContinue: () => void
  onGuide: () => void
  onCharacterEditor: () => void
  onOrders: () => void
  onSettings: () => void
  onExit: () => void
}

export function MenuScreen({
  canContinue,
  highScore = 0,
  selectedStage,
  onSelectStage,
  onNewGame,
  onContinue,
  onGuide,
  onCharacterEditor,
  onOrders,
  onSettings,
  onExit,
}: MenuScreenProps) {
  const selected = BOWL_STAGES.find((stage) => stage.id === selectedStage) ?? BOWL_STAGES[0]

  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-menu-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">9to18.ru</span>
        </div>
        <h1 className="bowl-title">Bowl 2D</h1>
        <p className="bowl-subtitle">
          Пять этапов: унитаз, канализация, ручей, очистные и море. Собирайте очки, перки и заказы.
        </p>
        {highScore > 0 ? <p className="bowl-subtitle">Рекорд: {highScore}</p> : null}

        <div className="bowl-stage-test">
          <p className="bowl-stage-test-label">Тест: старт с этапа</p>
          <div className="bowl-stage-grid" role="group" aria-label="Выбор этапа для теста">
            {BOWL_STAGES.map((stage) => {
              const isActive = stage.id === selectedStage
              return (
                <button
                  key={stage.id}
                  type="button"
                  className={`bowl-stage-option${isActive ? ' bowl-stage-option-active' : ''}`}
                  aria-pressed={isActive}
                  onClick={() => onSelectStage(stage.id)}
                >
                  <span className="bowl-stage-option-num">{stage.id}</span>
                  <span className="bowl-stage-option-title">{stage.title}</span>
                </button>
              )
            })}
          </div>
          <p className="bowl-stage-test-hint">
            Выбрано: {selected.id}. {selected.title} · событие «{selected.hazard}»
          </p>
        </div>

        <div className="bowl-menu-actions">
          <button type="button" className="bowl-btn bowl-btn-primary" onClick={onNewGame}>
            {selectedStage === 1 ? 'Новая игра' : `Старт с этапа ${selectedStage}`}
          </button>
          <button
            type="button"
            className="bowl-btn"
            onClick={onContinue}
            disabled={!canContinue}
          >
            Продолжить
          </button>
          <button type="button" className="bowl-btn" onClick={onOrders}>
            Заказы
          </button>
          <button type="button" className="bowl-btn" onClick={onGuide}>
            Справочник
          </button>
          <button type="button" className="bowl-btn" onClick={onCharacterEditor}>
            Редактор (тест)
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
