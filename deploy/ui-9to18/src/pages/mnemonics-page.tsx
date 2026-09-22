import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { MnemonicDrill } from '@/components/mnemonic-drill'
import { PageShell } from '@/components/page-shell'
import {
  collectMnemonicDrillsFromPosts,
  filterMnemonicDrills,
  markMnemonicDone,
  withSeedMnemonicDrills,
} from '@/data/mnemonics/collect'
import { loadCustomMnemonicDrills } from '@/data/mnemonics/custom-drills'
import {
  MNEMONIC_TECHNIQUE_META,
  type MnemonicTechniqueId,
} from '@/data/mnemonics/types'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'
import { isMnemonicTechniqueId } from '@/data/site/structured-post'

const SESSION_SIZE = 10

function shuffle<T>(items: T[]): T[] {
  const next = [...items]
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j], next[i]]
  }
  return next
}

export function MnemonicsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') === 'learn' ? 'learn' : 'trainers'
  const techParam = searchParams.get('tech') || ''
  const initialTech = isMnemonicTechniqueId(techParam) ? techParam : null

  const { posts, isReady } = useLearnPosts()
  const published = getPublishedPosts(posts)
  const allCards = useMemo(
    () => withSeedMnemonicDrills(collectMnemonicDrillsFromPosts(published)),
    [published],
  )
  const [selectedTechniques, setSelectedTechniques] = useState<MnemonicTechniqueId[]>(() =>
    initialTech ? [initialTech] : [],
  )
  const [session, setSession] = useState<typeof allCards>([])
  const [index, setIndex] = useState(0)
  const [customCount, setCustomCount] = useState(() => loadCustomMnemonicDrills().length)

  useEffect(() => {
    if (tab === 'trainers') {
      setCustomCount(loadCustomMnemonicDrills().length)
    }
  }, [tab])

  const filtered = useMemo(
    () => filterMnemonicDrills(allCards, { techniques: selectedTechniques }),
    [allCards, selectedTechniques],
  )

  const active = session[index] || null

  function setTab(next: 'trainers' | 'learn') {
    const params = new URLSearchParams(searchParams)
    if (next === 'learn') {
      params.set('tab', 'learn')
    } else {
      params.delete('tab')
    }
    setSearchParams(params, { replace: true })
  }

  function toggleTechnique(id: MnemonicTechniqueId) {
    setSelectedTechniques((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  function startSession() {
    const deck = shuffle(filtered).slice(0, Math.min(SESSION_SIZE, filtered.length))
    setSession(deck)
    setIndex(0)
  }

  return (
    <PageShell content="article">
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Мнемотехники</p>
        <h1 className="learn-title">Тренажёры кодирования</h1>
        <p className="learn-lead">
          Отдельный интерфейс под каждую технику: введите свой список, число или термин и
          потренируйтесь. Anki по-прежнему отвечает за повторение.
        </p>
      </header>

      <div className="mnemonic-tabs" role="tablist" aria-label="Разделы мнемотехник">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'trainers'}
          className={`mnemonic-tab${tab === 'trainers' ? ' is-active' : ''}`}
          onClick={() => setTab('trainers')}
        >
          Мои тренажёры
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'learn'}
          className={`mnemonic-tab${tab === 'learn' ? ' is-active' : ''}`}
          onClick={() => setTab('learn')}
        >
          Сессия из Learn
        </button>
      </div>

      {tab === 'trainers' ? (
        <>
          <p className="learn-section-note">
            Выберите технику — откроется форма для своих данных
            {customCount > 0 ? ` · сохранено дриллов: ${customCount}` : ''}.
          </p>
          <div className="mnemonic-hub-grid">
            {MNEMONIC_TECHNIQUE_META.map((meta) => (
              <Link
                key={meta.id}
                to={`/game/mnemonics/${meta.id}`}
                className="mnemonic-hub-card"
              >
                <span className="mnemonic-hub-id">{meta.id}</span>
                <strong>{meta.title}</strong>
                <span>{meta.subtitle}</span>
                <span className="mnemonic-hub-cta">Открыть →</span>
              </Link>
            ))}
          </div>
          <p className="learn-section-note">
            Также: <Link to="/game/learn">Learn</Link> ·{' '}
            <Link to="/game/learning-map">карта знаний</Link>
          </p>
        </>
      ) : (
        <>
          <p className="learn-section-note">
            Дриллы из раздела «Мнемоника» статей Learn (если пусто — демо-набор).
          </p>
          <div className="mnemonic-technique-grid" role="group" aria-label="Фильтр техник">
            {MNEMONIC_TECHNIQUE_META.filter((meta) => meta.wave1).map((meta) => {
              const isOn = selectedTechniques.includes(meta.id)
              return (
                <button
                  key={meta.id}
                  type="button"
                  className={`mnemonic-technique-chip${isOn ? ' is-active' : ''}`}
                  aria-pressed={isOn}
                  onClick={() => toggleTechnique(meta.id)}
                >
                  <strong>{meta.title}</strong>
                  <span>{meta.subtitle}</span>
                </button>
              )
            })}
          </div>
          <p className="learn-section-note">
            Доступно дриллов: {filtered.length}
            {selectedTechniques.length === 0 ? ' (все техники)' : ''}.
          </p>
          <div className="mnemonic-chip-row" style={{ marginBottom: '1rem' }}>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={!isReady || filtered.length === 0}
              onClick={startSession}
            >
              Начать сессию ({Math.min(SESSION_SIZE, filtered.length)})
            </button>
          </div>

          {!isReady ? <p className="home-subtitle">Загрузка дриллов…</p> : null}

          {active ? (
            <section className="structured-block" aria-labelledby="mnemonic-session">
              <h2 id="mnemonic-session" className="learn-section-title">
                Сессия {index + 1} / {session.length}
              </h2>
              <p className="learn-section-note">
                {active.episode} · <Link to={active.learnHref}>{active.learnTitle}</Link>
              </p>
              <MnemonicDrill
                key={active.id}
                drill={active}
                onComplete={() => markMnemonicDone(active.id)}
              />
              <div className="mnemonic-chip-row">
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={index <= 0}
                  onClick={() => setIndex((prev) => Math.max(0, prev - 1))}
                >
                  ← Назад
                </button>
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={index >= session.length - 1}
                  onClick={() => setIndex((prev) => Math.min(session.length - 1, prev + 1))}
                >
                  Далее →
                </button>
              </div>
            </section>
          ) : (
            <p className="learn-section-note">
              Или откройте{' '}
              <button type="button" className="learn-admin-link" onClick={() => setTab('trainers')}>
                свой тренажёр
              </button>{' '}
              и введите материал вручную.
            </p>
          )}
        </>
      )}
    </PageShell>
  )
}
