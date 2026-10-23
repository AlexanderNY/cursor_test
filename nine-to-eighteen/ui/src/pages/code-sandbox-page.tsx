import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { CodeSandboxEditor } from '@/components/code-sandbox-editor'
import {
  clearCodeDraft,
  loadCodeDraft,
  saveCodeDraft,
} from '@/game/code/draft-storage'
import { collectLearnPythonSnippets } from '@/game/code/learn-snippets'
import {
  formatRunChannels,
  loadSandboxPyodide,
  runPythonInSandbox,
  runPythonWithChecker,
} from '@/game/code/sandbox-pyodide'
import { CODE_TASKS, getCodeTask, type CodeTask } from '@/game/code/tasks'
import { seedPostsLocal } from '@/data/learn/learn-store'
import { codeFromQuery } from '@/data/safe-url'
import {
  getPublishedPosts,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'

const DEFAULT_CODE = `# Python в браузере (Pyodide)
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("9to18"))
sum(range(10))
`

type TabId = 'sandbox' | 'tasks'

function formatTaskStarter(task: CodeTask): string {
  const examples = task.examples.map((line) => `# ${line}`).join('\n')
  return `# ${task.episode} · ${task.title}\n# ${task.prompt}\n${examples}\n\n${task.starterCode}`
}

export function CodeSandboxPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { posts, isReady: postsReady } = useLearnPosts()
  const published = useMemo(() => getPublishedPosts(posts), [posts])
  const snippets = useMemo(() => {
    // Bundled seed may be newer than a live API catalog that still has old labs.
    const fromApi = collectLearnPythonSnippets(published)
    const fromSeed = collectLearnPythonSnippets(seedPostsLocal())
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
  const activeTask = taskId ? getCodeTask(taskId) : undefined

  const [code, setCode] = useState(DEFAULT_CODE)
  const [output, setOutput] = useState('')
  const [checkFeedback, setCheckFeedback] = useState<{
    passed: boolean
    text: string
  } | null>(null)
  const [status, setStatus] = useState('Загрузка runtime…')
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
      const task = getCodeTask(taskId)
      if (task) {
        setCode(formatTaskStarter(task))
        setOutput('')
        setCheckFeedback(null)
      }
      setDraftLoaded(true)
      return
    }
    const draft = loadCodeDraft()
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
      saveCodeDraft(code)
    }, 400)
    return () => window.clearTimeout(handle)
  }, [code, draftLoaded, activeTab, searchParams])

  useEffect(() => {
    let cancelled = false
    void loadSandboxPyodide((value, label) => {
      if (!cancelled) {
        setStatus(`${label} (${Math.round(value * 100)}%)`)
      }
    })
      .then(() => {
        if (!cancelled) {
          setIsReady(true)
          setStatus('Runtime готов · Ctrl+Enter — запуск · каждый запуск в чистом namespace')
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus(
            err instanceof Error ? err.message : 'Не удалось загрузить Pyodide',
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
      const run = await runPythonInSandbox(code)
      setOutput(formatRunChannels(run))
    } finally {
      setIsRunning(false)
    }
  }, [code])

  const onCheckTask = useCallback(async () => {
    if (!activeTask) {
      return
    }
    setIsRunning(true)
    setOutput('')
    setCheckFeedback(null)
    try {
      const run = await runPythonWithChecker(code, activeTask.checker)
      setOutput(formatRunChannels(run))
      setCheckFeedback({ passed: run.passed, text: run.feedback })
    } finally {
      setIsRunning(false)
    }
  }, [activeTask, code])

  const selectTask = (task: CodeTask) => {
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
      setStatus('Код скопирован в буфер (ссылка слишком длинная)')
      return
    }
    await navigator.clipboard.writeText(href)
    setStatus('Ссылка на фрагмент скопирована')
  }

  const fileLabel = activeTask
    ? `${activeTask.id.replace(/-/g, '_')}.py`
    : 'main.py'
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
        <p className="learn-eyebrow">Code</p>
        <h1 className="learn-title">Python в браузере</h1>
        <p className="learn-lead">
          Песочница и тренажёр на Pyodide — без сервера. Задачи junior связаны с{' '}
          <Link to="/game/learn">Learn</Link> PY02–PY08.
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
            <span className="code-ide-title">9to18 · code — {fileLabel}</span>
            <span className={`code-ide-status ${statusTone}`}>
              {isRunning ? 'running' : isReady ? 'ready' : 'loading'}
            </span>
          </div>

          <div className="code-ide-menubar" role="tablist" aria-label="Режим Code">
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
              tasks/{CODE_TASKS.length}
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
                {CODE_TASKS.map((task) => (
                  <li key={task.id}>
                    <button
                      type="button"
                      className={`code-task-item${activeTask?.id === task.id ? ' code-task-item--active' : ''}`}
                      onClick={() => selectTask(task)}
                    >
                      <span className="code-task-ep">{task.episode}</span>
                      <span className="code-task-file">{task.id}.py</span>
                      <span className="code-task-name">{task.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {activeTask && (
                <div className="code-task-brief">
                  <p className="code-task-brief-prompt">
                    <span className="code-term-prompt"># </span>
                    {activeTask.prompt}
                  </p>
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
                py
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
                    setCode(DEFAULT_CODE)
                    clearCodeDraft()
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

          <label className="sr-only" htmlFor="code-editor">
            Код
          </label>
          <CodeSandboxEditor
            key={activeTask?.id ?? (searchParams.get('code') ? 'query' : 'sandbox')}
            id="code-editor"
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
              <span className="code-ide-panel-meta">python · pyodide</span>
            </div>
            <pre className="code-sandbox-output" aria-live="polite">
              <span className="code-term-line code-term-line--meta">
                $ python {fileLabel}
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
            ```python из выпусков PY → в редактор
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
