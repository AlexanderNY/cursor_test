import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  filterAnkiCards,
  type AnkiCard,
} from '@/data/learning-map/anki-cards'
import { normalizeTag, resolveTagColor } from '@/data/learning-map/tag-style'

export type AnkiTopicOption = {
  id: string
  title: string
  count: number
}

type AnkiStudyProps = {
  cards: AnkiCard[]
  topics: AnkiTopicOption[]
  allTags: string[]
  tagColors?: Record<string, string>
  initialBranchIds?: string[]
  initialTags?: string[]
  onClose: () => void
  onReview?: (card: AnkiCard, ease: 1 | 2 | 3 | 4) => void | Promise<void>
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

export function AnkiStudy({
  cards,
  topics,
  allTags,
  tagColors = {},
  initialBranchIds = [],
  initialTags = [],
  onClose,
  onReview,
}: AnkiStudyProps) {
  const [phase, setPhase] = useState<Phase>('setup')
  const [selectedBranches, setSelectedBranches] = useState<string[]>(() =>
    initialBranchIds.filter((id) => topics.some((topic) => topic.id === id)),
  )
  const [selectedTags, setSelectedTags] = useState<string[]>(() =>
    initialTags.map(normalizeTag).filter((tag) => allTags.includes(tag)),
  )
  const [shuffleOnStart, setShuffleOnStart] = useState(true)
  const [deck, setDeck] = useState<AnkiCard[]>([])
  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)

  const previewCount = useMemo(
    () =>
      filterAnkiCards(cards, {
        branchIds: selectedBranches,
        tags: selectedTags,
      }).length,
    [cards, selectedBranches, selectedTags],
  )

  const card = deck[index] || null
  const total = deck.length

  useEffect(() => {
    setIndex(0)
    setRevealed(false)
  }, [deck])

  useEffect(() => {
    if (phase !== 'study') {
      return
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setPhase('setup')
        return
      }
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault()
        setRevealed((prev) => !prev)
        return
      }
      if (event.key === 'ArrowRight' || event.key === 'j') {
        setIndex((prev) => Math.min(total - 1, prev + 1))
        setRevealed(false)
        return
      }
      if (event.key === 'ArrowLeft' || event.key === 'k') {
        setIndex((prev) => Math.max(0, prev - 1))
        setRevealed(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, total])

  const toggleBranch = (id: string) => {
    setSelectedBranches((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  const toggleTag = (tag: string) => {
    const key = normalizeTag(tag)
    setSelectedTags((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key],
    )
  }

  const startStudy = () => {
    const filtered = filterAnkiCards(cards, {
      branchIds: selectedBranches,
      tags: selectedTags,
    })
    if (filtered.length === 0) {
      return
    }
    setDeck(shuffleOnStart ? shuffle(filtered) : filtered)
    setPhase('study')
    setIndex(0)
    setRevealed(false)
  }

  if (phase === 'setup') {
    return (
      <div className="lm-anki-overlay" role="dialog" aria-modal="true" aria-label="Настройка Anki">
        <div className="lm-anki-dialog lm-anki-dialog-wide">
          <header className="lm-anki-head">
            <div>
              <p className="lm-panel-eyebrow">Anki · настройка</p>
              <p className="lm-anki-meta">
                Выберите темы и/или теги · в колоде будет {previewCount} из {cards.length}
              </p>
            </div>
            <button type="button" className="lm-btn" onClick={onClose}>
              Закрыть
            </button>
          </header>

          {cards.length === 0 ? (
            <p className="lm-detail-empty">
              Нет карт с ответом. Сохраните краткий ответ у листьев карты.
            </p>
          ) : (
            <>
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
                <p className="lm-viewport-hint">Пустой выбор тем = все ветки</p>
              </section>

              <section className="lm-anki-setup-block">
                <div className="lm-branches-head">
                  <h3 className="lm-learn-subtitle">Теги</h3>
                  {selectedTags.length > 0 ? (
                    <button type="button" className="lm-btn" onClick={() => setSelectedTags([])}>
                      Сбросить теги
                    </button>
                  ) : null}
                </div>
                {allTags.length === 0 ? (
                  <p className="lm-detail-empty">Тегов пока нет</p>
                ) : (
                  <ul className="lm-tag-filter-list">
                    {allTags.map((tag) => {
                      const color = resolveTagColor(tag, tagColors)
                      const isOn = selectedTags.includes(tag)
                      return (
                        <li key={tag}>
                          <button
                            type="button"
                            className={`lm-tag-filter-chip${isOn ? ' is-active' : ''}`}
                            style={{
                              borderColor: color,
                              background: isOn ? `${color}33` : undefined,
                              color: isOn ? color : undefined,
                            }}
                            aria-pressed={isOn}
                            onClick={() => toggleTag(tag)}
                          >
                            #{tag}
                          </button>
                        </li>
                      )
                    })}
                  </ul>
                )}
                <p className="lm-viewport-hint">Пустой выбор тегов = без фильтра по тегам</p>
              </section>

              <label className="lm-anki-check lm-anki-shuffle">
                <input
                  type="checkbox"
                  checked={shuffleOnStart}
                  onChange={(event) => setShuffleOnStart(event.target.checked)}
                />
                <span>Перемешать карты</span>
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
              Начать · {previewCount}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (total === 0) {
    return (
      <div className="lm-anki-overlay" role="dialog" aria-modal="true" aria-label="Anki">
        <div className="lm-anki-dialog">
          <p className="lm-detail-empty">Нет карт по выбранным фильтрам.</p>
          <button type="button" className="lm-btn" onClick={() => setPhase('setup')}>
            Назад к выбору
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="lm-anki-overlay" role="dialog" aria-modal="true" aria-label="Повторение Anki">
      <div className="lm-anki-dialog lm-anki-dialog-wide">
        <header className="lm-anki-head">
          <div>
            <p className="lm-panel-eyebrow">Anki · повторение</p>
            <p className="lm-anki-meta">
              {index + 1} / {total}
              {card?.branch ? ` · ${card.branch}` : ''}
            </p>
          </div>
          <div className="lm-anki-head-actions">
            <button type="button" className="lm-btn" onClick={() => setPhase('setup')}>
              Фильтры
            </button>
            <button type="button" className="lm-btn" onClick={onClose}>
              Закрыть
            </button>
          </div>
        </header>

        <button
          type="button"
          className={`lm-anki-card${revealed ? ' is-revealed' : ''}`}
          onClick={() => setRevealed((prev) => !prev)}
        >
          <span className="lm-anki-side-label">{revealed ? 'Ответ' : 'Тема'}</span>
          <span className="lm-anki-side-text">{revealed ? card?.back : card?.front}</span>
          {!revealed ? (
            <span className="lm-anki-hint">Нажмите, чтобы показать ответ</span>
          ) : null}
        </button>

        {revealed && card?.learn ? (
          <aside className="lm-anki-learn">
            <p className="lm-anki-side-label">Конспект Learn</p>
            <p className="lm-anki-learn-meta">
              {card.learn.episode} · {card.learn.title}
            </p>
            <p className="lm-anki-learn-excerpt">{card.learn.excerpt}</p>
            <Link
              to={card.learn.href}
              className="lm-btn is-active"
              onClick={(event) => event.stopPropagation()}
            >
              Открыть статью →
            </Link>
          </aside>
        ) : null}

        {revealed && !card?.learn ? (
          <p className="lm-detail-empty">
            Для этой ветки пока нет статьи Learn — опирайтесь на краткий ответ карты.
          </p>
        ) : null}

        <div className="lm-anki-actions">
          <button
            type="button"
            className="lm-btn"
            disabled={index <= 0}
            onClick={() => {
              setIndex((prev) => Math.max(0, prev - 1))
              setRevealed(false)
            }}
          >
            ← Назад
          </button>
          <button
            type="button"
            className="lm-btn is-active"
            onClick={() => setRevealed((prev) => !prev)}
          >
            {revealed ? 'Скрыть ответ' : 'Показать ответ'}
          </button>
          {revealed && onReview && card ? (
            <>
              <button
                type="button"
                className="lm-btn"
                onClick={() => {
                  void onReview(card, 1)
                  setIndex((prev) => Math.min(prev + 1, total - 1))
                  setRevealed(false)
                }}
              >
                Снова
              </button>
              <button
                type="button"
                className="lm-btn is-active"
                onClick={() => {
                  void onReview(card, 3)
                  setIndex((prev) => Math.min(prev + 1, total - 1))
                  setRevealed(false)
                }}
              >
                Хорошо
              </button>
            </>
          ) : (
            <button
              type="button"
              className="lm-btn"
              disabled={index >= total - 1}
              onClick={() => {
                setIndex((prev) => Math.min(total - 1, prev + 1))
                setRevealed(false)
              }}
            >
              Далее →
            </button>
          )}
        </div>
        <p className="lm-viewport-hint">Пробел — ответ · ← → — карты · Esc — к фильтрам</p>
      </div>
    </div>
  )
}
