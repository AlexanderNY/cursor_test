import { getUpgradeOptions, type PerkId, type PerkLevels } from './perks'

interface PerkSelectScreenProps {
  level: number
  perkLevels?: PerkLevels
  onSelect: (perk: PerkId) => void
  onSkip?: () => void
  onBack?: () => void
  overlay?: boolean
}

export function PerkSelectScreen({
  level,
  perkLevels = {},
  onSelect,
  onSkip,
  onBack,
  overlay = false,
}: PerkSelectScreenProps) {
  const available = getUpgradeOptions(perkLevels)

  return (
    <div className={`bowl-screen bowl-perk-select${overlay ? ' bowl-perk-overlay' : ''}`}>
      <div className="bowl-perk-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">Уровень {level}</span>
        </div>
        <h1 className="bowl-title">{overlay ? 'Новый перк!' : 'Выберите перк'}</h1>
        <p className="bowl-subtitle">
          {overlay
            ? 'Съедено 10 врагов — выберите улучшение или новый перк.'
            : 'Один бонус на старт. Чаша унитаза ждёт.'}
        </p>

        {available.length === 0 ? (
          <>
            <p className="bowl-subtitle">Все перки максимального уровня.</p>
            {onSkip && (
              <button type="button" className="bowl-btn bowl-btn-primary" onClick={onSkip}>
                Продолжить
              </button>
            )}
          </>
        ) : (
          <div className="bowl-perk-grid">
            {available.map((perk) => (
              <button
                key={`${perk.id}-${perk.nextLevel}`}
                type="button"
                className="bowl-perk-option"
                onClick={() => onSelect(perk.id)}
              >
                <span className="bowl-perk-emoji" aria-hidden>{perk.emoji}</span>
                <span className="bowl-perk-title">{perk.title}</span>
                <span className="bowl-perk-desc">{perk.description}</span>
              </button>
            ))}
          </div>
        )}

        {onBack && !overlay && (
          <button type="button" className="bowl-btn bowl-btn-ghost bowl-perk-back" onClick={onBack}>
            ← Назад
          </button>
        )}
      </div>
    </div>
  )
}
