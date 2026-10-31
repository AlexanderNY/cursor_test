import { FormEvent, useMemo, useState } from 'react'
import {
  learnSlugQueued,
  learnTaskKey,
  postHasLab,
  postHasQuiz,
} from '@/components/tasks/learn-link'
import type { LearnPost } from '@/data/learn/learn-store'

const RESULT_LIMIT = 12

type ComposerMode = 'wording' | 'episode'

const MODES: { id: ComposerMode; label: string }[] = [
  { id: 'wording', label: 'Своя формулировка' },
  { id: 'episode', label: 'Выпуск' },
]

type TaskComposerProps = {
  posts: LearnPost[]
  postsReady: boolean
  queuedKeys: ReadonlySet<string>
  busyKey: string
  error: string
  planNote: string
  onAddWording: (title: string) => Promise<void>
  onAddEpisode: (post: LearnPost) => Promise<void>
  onPlan: (minutes: number) => Promise<void>
}

export function TaskComposer({
  posts,
  postsReady,
  queuedKeys,
  busyKey,
  error,
  planNote,
  onAddWording,
  onAddEpisode,
  onPlan,
}: TaskComposerProps) {
  const [mode, setMode] = useState<ComposerMode>('wording')
  const [title, setTitle] = useState('')
  const [query, setQuery] = useState('')
  const [minutes, setMinutes] = useState(40)

  const catalog = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const matched = needle
      ? posts.filter((post) => {
          const hay = [post.episode, post.title, post.shortTitle, ...(post.tags || [])]
            .join(' ')
            .toLowerCase()
          return hay.includes(needle)
        })
      : posts
    return {
      total: matched.length,
      rows: matched.slice(0, RESULT_LIMIT),
    }
  }, [posts, query])

  async function handleWording(event: FormEvent) {
    event.preventDefault()
    const next = title.trim()
    if (!next || busyKey) {
      return
    }
    await onAddWording(next)
    setTitle('')
  }

  async function handlePlan(event: FormEvent) {
    event.preventDefault()
    if (busyKey || minutes < 5) {
      return
    }
    await onPlan(minutes)
  }

  return (
    <section className="tasks-composer" aria-labelledby="tasks-composer-title">
      <div className="tasks-composer-head">
        <h2 id="tasks-composer-title" className="learn-section-title">
          Добавить в список
        </h2>
        <p className="learn-section-note">
          Своя формулировка и выпуск попадают в «Разобрать». У выпуска шаги: прочитать,
          лаба и тест. План по минутам сразу кладёт выпуски на сегодня.
        </p>
      </div>
      <form className="tasks-plan" onSubmit={(event) => void handlePlan(event)}>
        <label className="tasks-plan-field">
          <span>Есть</span>
          <input
            type="number"
            min={5}
            max={480}
            step={5}
            value={minutes}
            disabled={Boolean(busyKey)}
            onChange={(event) => setMinutes(Number(event.target.value) || 0)}
            aria-label="Минут на учёбу"
          />
          <span>минут</span>
        </label>
        <button
          type="submit"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={Boolean(busyKey) || minutes < 5}
        >
          {busyKey === 'plan' ? 'Собираю…' : 'Собрать на сегодня'}
        </button>
      </form>
      {planNote ? <p className="learn-section-note">{planNote}</p> : null}

      <div className="tasks-composer-modes" role="tablist" aria-label="Что добавить">
        {MODES.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={mode === item.id}
            className={
              mode === item.id ? 'tasks-composer-mode is-active' : 'tasks-composer-mode'
            }
            onClick={() => {
              setMode(item.id)
              setQuery('')
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {mode === 'wording' ? (
        <form className="tasks-quick-row" onSubmit={(event) => void handleWording(event)}>
          <input
            className="tasks-quick-input"
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Что сделать…"
            maxLength={512}
            disabled={Boolean(busyKey)}
            aria-label="Своя формулировка"
          />
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={Boolean(busyKey) || !title.trim()}
          >
            {busyKey === 'wording' ? 'Добавляю…' : 'В разобрать'}
          </button>
        </form>
      ) : (
        <div className="tasks-pick">
          <input
            className="tasks-quick-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Найти выпуск: название или код"
            aria-label="Поиск выпуска"
          />
          {!postsReady ? (
            <p className="learn-section-note">Загрузка каталога…</p>
          ) : catalog.total === 0 ? (
            <p className="learn-section-note">Выпусков по этому запросу нет.</p>
          ) : (
            <>
              <ul className="tasks-pick-list">
                {catalog.rows.map((post) => {
                  const key = learnTaskKey(post.slug, 'article')
                  const queued = learnSlugQueued(queuedKeys, post.slug)
                  const busy = busyKey === key
                  return (
                    <li key={key} className="tasks-pick-row">
                      <span className="tasks-pick-title">
                        {post.episode} · {post.shortTitle || post.title}
                        <span className="tasks-pick-steps">
                          <span className="learn-badge">Прочитать</span>
                          {postHasLab(post) ? <span className="learn-badge">Лаба</span> : null}
                          {postHasQuiz(post) ? <span className="learn-badge">Тест</span> : null}
                          {post.durationMin > 0 ? (
                            <span className="learn-badge">{post.durationMin} мин</span>
                          ) : null}
                        </span>
                      </span>
                      {queued ? (
                        <span className="learn-badge">В списке</span>
                      ) : (
                        <button
                          type="button"
                          className="learn-admin-btn learn-admin-btn-primary"
                          disabled={Boolean(busyKey)}
                          onClick={() => void onAddEpisode(post)}
                        >
                          {busy ? 'Добавляю…' : 'В разобрать'}
                        </button>
                      )}
                    </li>
                  )
                })}
              </ul>
              {catalog.total > catalog.rows.length ? (
                <p className="learn-section-note">
                  Показаны {catalog.rows.length} из {catalog.total}. Уточните поиск.
                </p>
              ) : null}
            </>
          )}
        </div>
      )}
      {error ? <p className="tasks-personal-error">{error}</p> : null}
    </section>
  )
}
