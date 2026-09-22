import { useState } from 'react'
import { DEFAULT_HERO_COLOR, HERO_COLORS } from './hero-colors'
import { HeroPreview } from './hero-preview'

interface HeroColorScreenProps {
  onContinue: (color: string) => void
  onBack: () => void
}

export function HeroColorScreen({ onContinue, onBack }: HeroColorScreenProps) {
  const [selected, setSelected] = useState(DEFAULT_HERO_COLOR)

  return (
    <div className="bowl-screen bowl-perk-select">
      <div className="bowl-perk-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">Новая игра</span>
        </div>
        <h1 className="bowl-title">Цвет героя</h1>
        <p className="bowl-subtitle">Выберите цвет вашей точки перед стартом.</p>

        <div className="bowl-hero-preview" aria-hidden>
          <HeroPreview color={selected} />
        </div>

        <div className="bowl-color-grid">
          {HERO_COLORS.map((option) => {
            const isActive = selected === option.fill
            return (
              <button
                key={option.id}
                type="button"
                className={`bowl-color-option${isActive ? ' bowl-color-option-active' : ''}`}
                onClick={() => setSelected(option.fill)}
                aria-pressed={isActive}
                aria-label={option.label}
              >
                <span className="bowl-color-swatch" style={{ background: option.fill }} />
                <span className="bowl-color-label">{option.label}</span>
              </button>
            )
          })}
        </div>

        <div className="bowl-color-actions">
          <button type="button" className="bowl-btn bowl-btn-primary" onClick={() => onContinue(selected)}>
            Далее — выбор перка
          </button>
          <button type="button" className="bowl-btn bowl-btn-ghost bowl-perk-back" onClick={onBack}>
            ← Назад
          </button>
        </div>
      </div>
    </div>
  )
}
