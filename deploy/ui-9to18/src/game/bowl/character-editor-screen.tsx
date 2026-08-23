import { useMemo, useState } from 'react'
import {
  loadCharacterEditorDraft,
  maxAllPerks,
  saveCharacterEditorDraft,
  setPerkLevel,
} from './character-editor-storage'
import { HeroPreview } from './hero-preview'
import { DEFAULT_HERO_COLOR, HERO_COLORS } from './hero-colors'
import {
  defaultPerkLevels,
  formatPerkLevels,
  getPerkLevel,
  PERK_DEFINITIONS,
  PERK_IDS,
  type PerkId,
  type PerkLevels,
} from './perks'

interface CharacterEditorScreenProps {
  onStart: (color: string, perkLevels: PerkLevels) => void
  onBack: () => void
}

export function CharacterEditorScreen({ onStart, onBack }: CharacterEditorScreenProps) {
  const initial = useMemo(() => loadCharacterEditorDraft(), [])
  const [color, setColor] = useState(initial.color || DEFAULT_HERO_COLOR)
  const [perkLevels, setPerkLevels] = useState<PerkLevels>(initial.perkLevels)

  const summary = formatPerkLevels(perkLevels)

  const updateLevel = (perkId: PerkId, delta: number) => {
    const maxLevel = PERK_DEFINITIONS[perkId].max_level
    const current = getPerkLevel(perkLevels, perkId)
    setPerkLevels(setPerkLevel(perkLevels, perkId, current + delta, maxLevel))
  }

  const handleStart = () => {
    const draft = { color, perkLevels }
    saveCharacterEditorDraft(draft)
    onStart(color, perkLevels)
  }

  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-guide-card bowl-editor-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">Тест</span>
        </div>
        <h1 className="bowl-title">Редактор персонажа</h1>
        <p className="bowl-subtitle bowl-guide-subtitle">
          Настройте цвет и перки перед стартом. Сохраняется локально для следующих тестов.
        </p>

        <div className="bowl-guide-scroll">
          <section className="bowl-guide-section">
            <h2 className="bowl-settings-group-title">Цвет героя</h2>
            <div className="bowl-editor-preview">
              <HeroPreview color={color} />
              <span className="bowl-editor-preview-text">{summary}</span>
            </div>
            <div className="bowl-color-grid bowl-editor-colors">
              {HERO_COLORS.map((option) => {
                const isActive = color === option.fill
                return (
                  <button
                    key={option.id}
                    type="button"
                    className={`bowl-color-option${isActive ? ' bowl-color-option-active' : ''}`}
                    onClick={() => setColor(option.fill)}
                    aria-pressed={isActive}
                    aria-label={option.label}
                  >
                    <span className="bowl-color-swatch" style={{ background: option.fill }} />
                    <span className="bowl-color-label">{option.label}</span>
                  </button>
                )
              })}
            </div>
          </section>

          <section className="bowl-guide-section">
            <div className="bowl-editor-section-head">
              <h2 className="bowl-settings-group-title">Перки</h2>
              <div className="bowl-editor-quick">
                <button
                  type="button"
                  className="bowl-editor-quick-btn"
                  onClick={() => setPerkLevels(maxAllPerks())}
                >
                  Все MAX
                </button>
                <button
                  type="button"
                  className="bowl-editor-quick-btn"
                  onClick={() => setPerkLevels(defaultPerkLevels())}
                >
                  Сброс
                </button>
              </div>
            </div>

            {PERK_IDS.map((perkId) => {
              const def = PERK_DEFINITIONS[perkId]
              const level = getPerkLevel(perkLevels, perkId)
              const levelDesc = def.levels[String(level)]?.description ?? def.title

              return (
                <article key={perkId} className="bowl-editor-perk">
                  <div className="bowl-editor-perk-main">
                    <span className="bowl-editor-perk-toggle">
                      <span className="bowl-editor-perk-emoji" aria-hidden>
                        {def.emoji}
                      </span>
                      <span className="bowl-editor-perk-name">{def.title}</span>
                    </span>
                    <div className="bowl-editor-level">
                      <button
                        type="button"
                        className="bowl-editor-level-btn"
                        disabled={level <= 0}
                        onClick={() => updateLevel(perkId, -1)}
                        aria-label={`Уменьшить ${def.title}`}
                      >
                        −
                      </button>
                      <span className="bowl-editor-level-value">
                        {level}/{def.max_level}
                      </span>
                      <button
                        type="button"
                        className="bowl-editor-level-btn"
                        disabled={level >= def.max_level}
                        onClick={() => updateLevel(perkId, 1)}
                        aria-label={`Увеличить ${def.title}`}
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <p className="bowl-editor-perk-desc">{levelDesc}</p>
                </article>
              )
            })}
          </section>
        </div>

        <div className="bowl-settings-actions">
          <button type="button" className="bowl-btn bowl-btn-primary" onClick={handleStart}>
            Начать тест
          </button>
          <button type="button" className="bowl-btn bowl-btn-ghost" onClick={onBack}>
            ← Назад в меню
          </button>
        </div>
      </div>
    </div>
  )
}
