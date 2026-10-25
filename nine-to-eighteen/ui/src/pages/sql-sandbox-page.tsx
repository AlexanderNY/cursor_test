import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { CodeSandboxEditor } from '@/components/code-sandbox-editor'
import {
  clearSqlDraft,
  loadSqlDraft,
  saveSqlDraft,
} from '@/game/sql/draft-storage'
import { collectLearnSqlSnippets } from '@/game/sql/learn-snippets'
import {
  formatSqlRunChannels,
  loadSandboxSqlJs,
  runSqlInSandbox,
  runSqlWithCheck,
} from '@/game/sql/sandbox-sqlite'
import { schemaForFreeSql } from '@/game/sql/schemas'
import { SQL_TASKS, getSqlTask, type SqlTask } from '@/game/sql/tasks'
import { seedPostsLocal } from '@/data/learn/learn-store'
import { codeFromQuery } from '@/data/safe-url'
import {
  getPublishedPosts,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'

const DEFAULT_SQL = `-- SQL в браузере (SQLite / sql.js)
-- Диалект SQLite: нет GRANT, plpgsql, EXPLAIN ANALYZE как в PostgreSQL.
-- Если свой CREATE TABLE нет, перед запуском уже есть тестовые
-- users, customers, orders, order_items, sizes, colors.
-- У Bob нет заказов; email и middle_name у него NULL.

SELECT o.id AS order_id, u.name, o.total, o.status
FROM orders AS o
INNER JOIN users AS u ON u.id = o.user_id
ORDER BY o.id;
`

type TabId = 'sandbox' | 'tasks'

function formatTaskStarter(task: SqlTask): string {
  const examples = task.examples.map((line) => `-- ${line}`).join('\n')
  return `-- ${task.episode} · ${task.title}\n-- ${task.prompt}\n${examples}\n\n${task.starterSql}`
}

export function SqlSandboxPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { posts, isReady: postsReady } = useLearnPosts()
  const published = useMemo(() => getPublishedPosts(posts), [posts])
  const snippets = useMemo(() => {
    const fromApi = collectLearnSqlSnippets(published)
    const fromSeed = collectLearnSqlSnippets(seedPostsLocal())
    const seen = new Set<string>()
    const merged = [...fromSeed, ...fromApi].filter((snippet) => {
      const key = `${snippet.slug}|${snippet.source}|${snippet.code}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    return merged.sort((a, b) => {
      const ep = a.episode.localeCompare(b.episode, undefined, { numeric: true })
      if (ep !== 0) return ep
      if (a.source !== b.source) return a.source === 'lab' ? -1 : 1
      return a.blockIndex - b.blockIndex
    })
  }, [published])

  const tabParam = searchParams.get('tab')
  const taskId = searchParams.get('task')
  const activeTab: TabId =
    tabParam === 'tasks' || taskId ? 'tasks' : 'sandbox'
  const activeTask = taskId ? getSqlTask(taskId) : undefined

  const [code, setCode] = useState(DEFAULT_SQL)
  const [output, setOutput] = useState('')
  const [checkFeedback, setCheckFeedback] = useState<{
    passed: boolean
    text: string
  } | null>(null)
  const [status, setStatus] = useState('Загрузка sql.js…')
  const [isReady, setIsReady] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [draftLoaded, setDraftLoaded] = useState(false)

  useEffect(() => {
    const fromQuery = codeFromQuery(searchParams.get('code'))
    if (fromQuery) {
      setCode(fromQuery)
      setDraftLoaded(true)
      return
    }
    if (taskId) {
      const task = getSqlTask(taskId)
      if (task) {
        setCode(formatTaskStarter(task))
        setOutput('')
        setCheckFeedback(null)
      }
      setDraftLoaded(true)
      return
    }
    const draft = loadSqlDraft()
    if (draft) {
      setCode(draft)
    }
    setDraftLoaded(true)
  }, [searchParams, taskId])

  useEffect(() => {
    if (!draftLoaded || activeTab !== 'sandbox' || searchParams.get('code')) {
      return
    }
    const handle = window.setTimeout(() => {
      saveSqlDraft(code)
    }, 400)
    return () => window.clearTimeout(handle)
  }, [code, draftLoaded, activeTab, searchParams])

  useEffect(() => {
    let cancelled = false
    void loadSandboxSqlJs((value, label) => {
      if (!cancelled) {
        setStatus(`${label} (${Math.round(value * 100)}%)`)
      }
    })
      .then(() => {
        if (!cancelled) {
          setIsReady(true)
          setStatus(
            'SQLite готов · тестовые orders уже в базе · Ctrl+Enter — запуск',
          )
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus(
            err instanceof Error ? err.message : 'Не удалось загрузить sql.js',
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const onRun = useCallback(async () => {
    setIsRunning(true)
    setOutput('')
    setCheckFeedback(null)
    try {
      const schema =
        activeTab === 'tasks' && activeTask
          ? activeTask.schemaSql
          : schemaForFreeSql(code)
      const run = await runSqlInSandbox(code, schema)
      setOutput(formatSqlRunChannels(run))
    } finally {
      setIsRunning(false)
    }
  }, [activeTab, activeTask, code])

  const onCheckTask = useCallback(async () => {
    if (!activeTask) {
      return
    }
    setIsRunning(true)
    setOutput('')
    setCheckFeedback(null)
    try {
      const run = await runSqlWithCheck(
        code,
        activeTask.schemaSql,
        activeTask.check,
      )
      setOutput(formatSqlRunChannels(run))
      setCheckFeedback({
        passed: run.passed,
        text: run.feedback.replace(/^(PASS|FAIL):\s*/i, ''),
      })
    } finally {
      setIsRunning(false)
    }
  }, [activeTask, code])

  const selectTask = (task: SqlTask) => {
    setSearchParams({ tab: 'tasks', task: task.id })
    setCode(formatTaskStarter(task))
    setOutput('')
    setCheckFeedback(null)
  }

  const openSandboxTab = () => {
    setSearchParams({})
  }

  const applySnippet = (snippetCode: string) => {
    setSearchParams({})
    setCode(snippetCode)
    setOutput('')
    setCheckFeedback(null)
  }

  const copyShareLink = async () => {
    const url = new URL(window.location.href)
    url.search = ''
    url.searchParams.set('code', code)
    const href = url.toString()
    if (href.length > 8000) {
      await navigator.clipboard.writeText(code)
      setStatus('SQL скопирован в буфер (ссылка слишком длинная)')
      return
    }
    await navigator.clipboard.writeText(href)
    setStatus('Ссылка на фрагмент скопирована')
  }

  const fileLabel = activeTask
    ? `${activeTask.id.replace(/-/g, '_')}.sql`
    : 'main.sql'
  const statusTone = !isReady
    ? 'code-ide-status--busy'
    : isRunning
      ? 'code-ide-status--busy'
      : 'code-ide-status--ok'

  return (
    <PageShell content="article">
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">SQL</p>
        <h1 className="learn-title">SQL в браузере</h1>
        <p className="learn-lead">
          Песочница и тренажёр на SQLite (sql.js) — без сервера. В свободном
          режиме уже лежат тестовые users, customers и orders. Диалект SQLite;
          задачи связаны с{' '}
          <Link to="/game/learn">Learn</Link> SQL01–SQL13. PostgreSQL-специфика
          (GRANT, plpgsql, EXPLAIN ANALYZE) — в лекциях.
        </p>
      </header>

      <div className="code-sandbox-layout">
        <div className="code-ide" data-running={isRunning ? 'true' : undefined}>
          <div className="code-ide-titlebar" aria-hidden="true">
            <span className="code-ide-dots">
              <span className="code-ide-dot code-ide-dot--red" />
              <span className="code-ide-dot code-ide-dot--amber" />
              <span className="code-ide-dot code-ide-dot--green" />
            </span>
            <span className="code-ide-title">9to18 · sql — {fileLabel}</span>
            <span className={`code-ide-status ${statusTone}`}>
              {isRunning ? 'running' : isReady ? 'ready' : 'loading'}
            </span>
          </div>

          <div className="code-ide-menubar" role="tablist" aria-label="Режим SQL">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'sandbox'}
              className={`code-ide-tab${activeTab === 'sandbox' ? ' code-ide-tab--active' : ''}`}
              onClick={openSandboxTab}
            >
              sandbox
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'tasks'}
              className={`code-ide-tab${activeTab === 'tasks' ? ' code-ide-tab--active' : ''}`}
              onClick={() => setSearchParams({ tab: 'tasks' })}
            >
              tasks/{SQL_TASKS.length}
            </button>
            <span className="code-ide-menubar-hint">{status}</span>
          </div>

          {activeTab === 'tasks' && (
            <section className="code-task-catalog" aria-label="Каталог задач">
              <div className="code-ide-panel-head">
                <span className="code-ide-panel-label">EXPLORER</span>
                <span className="code-ide-panel-meta">tasks/</span>
              </div>
              <ul className="code-task-list">
                {SQL_TASKS.map((task) => (
                  <li key={task.id}>
                    <button
                      type="button"
                      className={`code-task-item${activeTask?.id === task.id ? ' code-task-item--active' : ''}`}
                      onClick={() => selectTask(task)}
                    >
                      <span className="code-task-ep">{task.episode}</span>
                      <span className="code-task-file">{task.id}.sql</span>
                      <span className="code-task-name">{task.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {activeTask && (
                <div className="code-task-brief">
                  <p className="code-task-brief-prompt">
                    <span className="code-term-prompt">-- </span>
                    {activeTask.prompt}
                  </p>
                  {activeTask.schemaHint ? (
                    <p className="code-side-note">
                      Схема: {activeTask.schemaHint}
                    </p>
                  ) : null}
                  <ul>
                    {activeTask.examples.map((example) => (
                      <li key={example}>
                        <code>{example}</code>
                      </li>
                    ))}
                  </ul>
                  <p>
                    <Link to={`/game/learn/${activeTask.learnSlug}`}>
                      → learn/{activeTask.learnSlug}
                    </Link>
                  </p>
                </div>
              )}
            </section>
          )}

          <div className="code-ide-toolbar">
            <div className="code-ide-filetab" title={fileLabel}>
              <span className="code-ide-filetab-icon" aria-hidden="true">
                sql
              </span>
              {fileLabel}
            </div>
            <div className="code-sandbox-actions">
              <button
                type="button"
                className="code-ide-btn code-ide-btn--run"
                disabled={!isReady || isRunning}
                onClick={() => void onRun()}
              >
                {isRunning ? '▶ …' : '▶ Run'}
              </button>
              {activeTab === 'tasks' && activeTask && (
                <button
                  type="button"
                  className="code-ide-btn code-ide-btn--check"
                  disabled={!isReady || isRunning}
                  onClick={() => void onCheckTask()}
                >
                  ✓ Check
                </button>
              )}
              <button
                type="button"
                className="code-ide-btn"
                onClick={() => {
                  if (activeTask) {
                    setCode(formatTaskStarter(activeTask))
                  } else {
                    setCode(DEFAULT_SQL)
                    clearSqlDraft()
                  }
                  setOutput('')
                  setCheckFeedback(null)
                }}
              >
                Reset
              </button>
              <button
                type="button"
                className="code-ide-btn"
                onClick={() => void copyShareLink()}
              >
                Share
              </button>
            </div>
          </div>

          <label className="sr-only" htmlFor="sql-editor">
            SQL
          </label>
          <CodeSandboxEditor
            key={activeTask?.id ?? (searchParams.get('code') ? 'query' : 'sandbox')}
            id="sql-editor"
            language="sql"
            value={code}
            onChange={setCode}
            onRun={() => {
              if (!isReady || isRunning) return
              if (activeTab === 'tasks' && activeTask) {
                void onCheckTask()
              } else {
                void onRun()
              }
            }}
            disabled={!draftLoaded}
          />

          {checkFeedback && (
            <p
              className={`code-check-banner${checkFeedback.passed ? ' code-check-banner--pass' : ' code-check-banner--fail'}`}
              role="status"
            >
              {checkFeedback.passed ? '✓ PASS' : '✗ FAIL'}: {checkFeedback.text}
            </p>
          )}

          <div className="code-ide-terminal">
            <div className="code-ide-panel-head">
              <span className="code-ide-panel-label">TERMINAL</span>
              <span className="code-ide-panel-meta">sqlite · sql.js</span>
            </div>
            <pre className="code-sandbox-output" aria-live="polite">
              <span className="code-term-line code-term-line--meta">
                $ sqlite3 {fileLabel}
              </span>
              {output ? `\n${output}` : '\n█'}
            </pre>
          </div>
        </div>

        <aside className="code-sandbox-side" aria-label="Заготовки Learn">
          <div className="code-ide-panel-head">
            <span className="code-ide-panel-label">SNIPPETS</span>
            <span className="code-ide-panel-meta">learn/</span>
          </div>
          <p className="code-side-note">
            ```sql из выпусков SQL → в редактор
          </p>
          {!postsReady ? (
            <p className="code-side-note">loading…</p>
          ) : snippets.length === 0 ? (
            <p className="code-side-note">
              нет блоков ·{' '}
              <Link to="/game/learn">/game/learn</Link>
            </p>
          ) : (
            <ul className="code-snippet-list">
              {snippets.map((snippet) => (
                <li key={`${snippet.slug}-${snippet.source}-${snippet.blockIndex}`}>
                  <button
                    type="button"
                    className="code-snippet-item"
                    onClick={() => applySnippet(snippet.code)}
                  >
                    <span className="code-task-ep">{snippet.episode}</span>
                    <span>
                      {snippet.shortTitle}
                      {snippet.source === 'lab' ? '/lab' : '/theory'}
                      {snippet.blockIndex > 0 ? `:${snippet.blockIndex + 1}` : ''}
                    </span>
                  </button>
                  <Link
                    className="code-snippet-learn"
                    to={`/game/learn/${snippet.slug}`}
                  >
                    open
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </PageShell>
  )
}
