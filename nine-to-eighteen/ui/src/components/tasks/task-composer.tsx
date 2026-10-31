import { FormEvent, useMemo, useState } from 'react'
import {
  learnTaskKey,
  postHasQuiz,
  type LearnTaskKind,
} from '@/components/tasks/learn-link'
import type { LearnPost } from '@/data/learn/learn-store'

const RESULT_LIMIT = 12

type ComposerMode = 'wording' | 'article' | 'quiz'

const MODES: { id: ComposerMode; label: string }[] = [
  { id: 'wording', label: 'Своя формулировка' },
  { id: 'article', label: 'Статья' },
  { id: 'quiz', label: 'Тест' },
]

type TaskComposerProps = {
  posts: LearnPost[]
  postsReady: boolean
  queuedKeys: ReadonlySet<string>
  busyKey: string
  error: string
  onAddWording: (title: string) => Promise<void>
  onAddLearn: (post: LearnPost, kind: LearnTaskKind) => Promise<void>
}

export function TaskComposer({
  posts,
  postsReady,
  queuedKeys,
  busyKey,
  error,
  onAddWording,
  onAddLearn,
}: TaskComposerProps) {
  const [mode, setMode] = useState<ComposerMode>('wording')
  const [title, setTitle] = useState('')
  const [query, setQuery] = useState('')

  const catalog = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const source =
      mode === 'quiz' ? posts.filter((post) => postHasQuiz(post)) : posts
    const matched = needle
      ? source.filter((post) => {
          const hay = [post.episode, post.title, post.shortTitle, ...(post.tags || [])]
            .join(' ')
            .toLowerCase()
          return hay.includes(needle)
        })
      : source
    return {
      total: matched.length,
      rows: matched.slice(0, RESULT_LIMIT),
    }
  }, [mode, posts, query])

  async function handleWording(event: FormEvent) {
    event.preventDefault()
    const next = title.trim()
    if (!next || busyKey) {
      return
    }
    await onAddWording(next)
    setTitle('')
  }

  return (
    <section className="tasks-composer" aria-labelledby="tasks-composer-title">
      <div className="tasks-composer-head">
        <h2 id="tasks-composer-title" className="learn-section-title">
          Добавить в список
        </h2>
        <p className="learn-section-note">
          Своя формулировка, любая статья или любой тест. Новая задача попадает на сегодня.
        </p>
      </div>
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
            {busyKey === 'wording' ? 'Добавляю…' : 'В список'}
          </button>
        </form>
      ) : (
        <div className="tasks-pick">
          <input
            className="tasks-quick-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={
              mode === 'quiz'
                ? 'Найти тест: название или код выпуска'
                : 'Найти статью: название или код выпуска'
            }
            aria-label={mode === 'quiz' ? 'Поиск теста' : 'Поиск статьи'}
          />
          {!postsReady ? (
            <p className="learn-section-note">Загрузка каталога…</p>
          ) : catalog.total === 0 ? (
            <p className="learn-section-note">
              {mode === 'quiz' ? 'Тестов по этому запросу нет.' : 'Статей по этому запросу нет.'}
            </p>
          ) : (
            <>
              <ul className="tasks-pick-list">
                {catalog.rows.map((post) => {
                  const kind: LearnTaskKind = mode === 'quiz' ? 'quiz' : 'article'
                  const key = learnTaskKey(post.slug, kind)
                  const queued = queuedKeys.has(key)
                  const busy = busyKey === key
                  return (
                    <li key={key} className="tasks-pick-row">
                      <span className="tasks-pick-title">
                        {post.episode} · {post.shortTitle || post.title}
                      </span>
                      {queued ? (
                        <span className="learn-badge">В списке</span>
                      ) : (
                        <button
                          type="button"
                          className="learn-admin-btn learn-admin-btn-primary"
                          disabled={Boolean(busyKey)}
                          onClick={() => void onAddLearn(post, kind)}
                        >
                          {busy ? 'Добавляю…' : 'В список'}
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
