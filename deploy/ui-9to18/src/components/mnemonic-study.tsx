import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { MnemonicDrill } from '@/components/mnemonic-drill'
import {
  filterMnemonicDrills,
  markMnemonicDone,
} from '@/data/mnemonics/collect'
import {
  MNEMONIC_TECHNIQUE_META,
  type MnemonicDrillCard,
  type MnemonicTechniqueId,
} from '@/data/mnemonics/types'

type MnemonicStudyProps = {
  cards: MnemonicDrillCard[]
  topics?: Array<{ id: string; title: string; count: number }>
  initialBranchIds?: string[]
  initialTechniques?: MnemonicTechniqueId[]
  onClose: () => void
}

type Phase = 'setup' | 'study'

function shuffle<T>(items: T[]): T[] {
  const next = [...items]
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j], next[i]]
  }
  return next
}

export function MnemonicStudy({
  cards,
  topics = [],
  initialBranchIds = [],
  initialTechniques = [],
  onClose,
}: MnemonicStudyProps) {
  const [phase, setPhase] = useState<Phase>('setup')
  const [selectedBranches, setSelectedBranches] = useState<string[]>(() =>
    initialBranchIds.filter((id) => topics.some((topic) => topic.id === id)),
  )
  const [selectedTechniques, setSelectedTechniques] = useState<MnemonicTechniqueId[]>(
    () => initialTechniques,
  )
  const [shuffleOnStart, setShuffleOnStart] = useState(true)
  const [deck, setDeck] = useState<MnemonicDrillCard[]>([])
  const [index, setIndex] = useState(0)

  const previewCount = useMemo(
    () =>
      filterMnemonicDrills(cards, {
        branchIds: selectedBranches,
        techniques: selectedTechniques,
      }).length,
    [cards, selectedBranches, selectedTechniques],
  )

  const card = deck[index] || null
  const total = deck.length

  const techniqueOptions = useMemo(() => {
    const present = new Set(cards.map((item) => item.technique))
    return MNEMONIC_TECHNIQUE_META.filter((meta) => present.has(meta.id))
  }, [cards])

  function toggleTechnique(id: MnemonicTechniqueId) {
    setSelectedTechniques((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function toggleBranch(id: string) {
    setSelectedBranches((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function startStudy() {
    const filtered = filterMnemonicDrills(cards, {
      branchIds: selectedBranches,
      techniques: selectedTechniques,
    })
    if (filtered.length === 0) {
      return
    }
    const capped = (shuffleOnStart ? shuffle(filtered) : filtered).slice(0, 12)
    setDeck(capped)
    setIndex(0)
    setPhase('study')
  }

  if (phase === 'setup') {
    return (
      <div
        className="lm-anki-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="Настройка мнемотехник"
      >
        <div className="lm-anki-dialog lm-anki-dialog-wide">
          <header className="lm-anki-head">
            <div>
              <p className="lm-panel-eyebrow">Мнемоника · настройка</p>
              <p className="lm-anki-meta">
                Выберите техники и темы · в сессии будет {Math.min(12, previewCount)} из{' '}
                {cards.length}
              </p>
            </div>
            <button type="button" className="lm-btn" onClick={onClose}>
              Закрыть
            </button>
          </header>

          {cards.length === 0 ? (
            <p className="lm-detail-empty">
              Нет дриллов. Добавьте раздел «Мнемоника» в статью Learn.
            </p>
          ) : (
            <>
              <section className="lm-anki-setup-block">
                <h3 className="lm-learn-subtitle">Техники</h3>
                <ul className="lm-anki-check-list">
                  {techniqueOptions.map((meta) => {
                    const checked = selectedTechniques.includes(meta.id)
                    return (
                      <li key={meta.id}>
                        <label className={`lm-anki-check${checked ? ' is-on' : ''}`}>
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleTechnique(meta.id)}
                          />
                          <span>
                            {meta.title}
                            <span className="lm-tree-count">{meta.subtitle}</span>
                          </span>
                        </label>
                      </li>
                    )
                  })}
                </ul>
                <p className="lm-viewport-hint">Пустой выбор = все техники</p>
              </section>

              {topics.length > 0 ? (
                <section className="lm-anki-setup-block">
                  <div className="lm-branches-head">
                    <h3 className="lm-learn-subtitle">Темы (ветки)</h3>
                    <button
                      type="button"
                      className="lm-btn"
                      onClick={() =>
                        setSelectedBranches(
                          selectedBranches.length === topics.length
                            ? []
                            : topics.map((topic) => topic.id),
                        )
                      }
                    >
                      {selectedBranches.length === topics.length ? 'Снять все' : 'Все темы'}
                    </button>
                  </div>
                  <ul className="lm-anki-check-list">
                    {topics.map((topic) => {
                      const checked = selectedBranches.includes(topic.id)
                      return (
                        <li key={topic.id}>
                          <label className={`lm-anki-check${checked ? ' is-on' : ''}`}>
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleBranch(topic.id)}
                            />
                            <span>{topic.title}</span>
                            <span className="lm-tree-count">{topic.count}</span>
                          </label>
                        </li>
                      )
                    })}
                  </ul>
                </section>
              ) : null}

              <label className="lm-anki-check lm-anki-shuffle">
                <input
                  type="checkbox"
                  checked={shuffleOnStart}
                  onChange={(event) => setShuffleOnStart(event.target.checked)}
                />
                <span>Перемешать дриллы</span>
              </label>
            </>
          )}

          <div className="lm-anki-actions">
            <button type="button" className="lm-btn" onClick={onClose}>
              Отмена
            </button>
            <button
              type="button"
              className="lm-btn is-active"
              disabled={previewCount === 0}
              onClick={startStudy}
            >
              Начать · {Math.min(12, previewCount)}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!card || total === 0) {
    return (
      <div className="lm-anki-overlay" role="dialog" aria-modal="true" aria-label="Мнемоника">
        <div className="lm-anki-dialog">
          <p className="lm-detail-empty">Нет дриллов по фильтрам.</p>
          <button type="button" className="lm-btn" onClick={() => setPhase('setup')}>
            Назад к выбору
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className="lm-anki-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Тренажёр мнемотехник"
    >
      <div className="lm-anki-dialog lm-anki-dialog-wide">
        <header className="lm-anki-head">
          <div>
            <p className="lm-panel-eyebrow">Мнемоника · сессия</p>
            <p className="lm-anki-meta">
              {index + 1} / {total} · {card.episode} · {card.learnTitle}
            </p>
          </div>
          <div className="mnemonic-chip-row">
            <button type="button" className="lm-btn" onClick={() => setPhase('setup')}>
              Настройка
            </button>
            <button type="button" className="lm-btn" onClick={onClose}>
              Закрыть
            </button>
          </div>
        </header>

        <MnemonicDrill
          drill={card}
          onComplete={() => markMnemonicDone(card.id)}
        />

        <div className="lm-anki-actions">
          <button
            type="button"
            className="lm-btn"
            disabled={index <= 0}
            onClick={() => setIndex((prev) => Math.max(0, prev - 1))}
          >
            ← Назад
          </button>
          <Link to={card.learnHref} className="lm-btn">
            Статья →
          </Link>
          <button
            type="button"
            className="lm-btn is-active"
            disabled={index >= total - 1}
            onClick={() => setIndex((prev) => Math.min(total - 1, prev + 1))}
          >
            Далее →
          </button>
        </div>
      </div>
    </div>
  )
}
