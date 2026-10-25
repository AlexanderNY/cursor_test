import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { CodeSandboxEditor } from '@/components/code-sandbox-editor'
import {
  clearGitDraft,
  loadGitDraft,
  saveGitDraft,
} from '@/game/git/draft-storage'
import { collectLearnGitSnippets } from '@/game/git/learn-snippets'
import {
  formatGitChannels,
  runGitSandboxScript,
  runGitScript,
  runGitWithCheck,
  snapshotPanel,
} from '@/game/git/sandbox-git'
import { GIT_TASKS, getGitTask, type GitTask } from '@/game/git/tasks'
import { seedPostsLocal } from '@/data/learn/learn-store'
import { codeFromQuery } from '@/data/safe-url'
import {
  getPublishedPosts,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'

const DEFAULT_SCRIPT = `# Git-симулятор в браузере (без настоящего .git на диске)
# Вспомогательные команды: write <path> <text>, rmfile <path>
# Если в скрипте нет git init, перед запуском уже есть учебный репозиторий:
# README.md, file.txt (незакоммиченная правка), commit «add extra».

git init
write README.md hello-9to18
git add README.md
git commit -m "init: sandbox"
git status
git log --oneline
`

type TabId = 'sandbox' | 'tasks'

function formatTaskStarter(task: GitTask): string {
  const examples = task.examples.map((line) => `# ${line}`).join('\n')
  return `# ${task.episode} · ${task.title}\n# ${task.prompt}\n${examples}\n\n${task.starterCommands}`
}

export function GitSandboxPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { posts, isReady: postsReady } = useLearnPosts()
  const published = useMemo(() => getPublishedPosts(posts), [posts])
  const snippets = useMemo(() => {
    const fromApi = collectLearnGitSnippets(published)
    const fromSeed = collectLearnGitSnippets(seedPostsLocal())
    const seen = new Set<string>()
    return [...fromSeed, ...fromApi]
      .filter((snippet) => {
        const key = `${snippet.slug}|${snippet.source}|${snippet.code}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      .sort((a, b) => {
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
  const activeTask = taskId ? getGitTask(taskId) : undefined

  const [code, setCode] = useState(DEFAULT_SCRIPT)
  const [output, setOutput] = useState('')
  const [panel, setPanel] = useState('')
  const [checkFeedback, setCheckFeedback] = useState<{
    passed: boolean
    text: string
  } | null>(null)
  const [status, setStatus] = useState(
    'Симулятор готов · без git init подставится учебный репозиторий · Ctrl+Enter — запуск',
  )
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
      const task = getGitTask(taskId)
      if (task) {
        setCode(formatTaskStarter(task))
        setOutput('')
        setPanel('')
        setCheckFeedback(null)
      }
      setDraftLoaded(true)
      return
    }
    const draft = loadGitDraft()
    if (draft) setCode(draft)
    setDraftLoaded(true)
  }, [searchParams, taskId])

  useEffect(() => {
    if (!draftLoaded || activeTab !== 'sandbox' || searchParams.get('code')) {
      return
    }
    const handle = window.setTimeout(() => saveGitDraft(code), 400)
    return () => window.clearTimeout(handle)
  }, [code, draftLoaded, activeTab, searchParams])

  const onRun = useCallback(() => {
    setIsRunning(true)
    setOutput('')
    setCheckFeedback(null)
    try {
      if (activeTab === 'tasks' && activeTask) {
        const seeded = runGitScript(activeTask.seedCommands)
        const run = runGitScript(code, seeded.state)
        setOutput(formatGitChannels(run))
        setPanel(snapshotPanel(run.state))
      } else {
        const run = runGitSandboxScript(code)
        setOutput(formatGitChannels(run))
        setPanel(snapshotPanel(run.state))
      }
    } finally {
      setIsRunning(false)
    }
  }, [activeTab, activeTask, code])

  const onCheckTask = useCallback(() => {
    if (!activeTask) return
    setIsRunning(true)
    setOutput('')
    setCheckFeedback(null)
    try {
      const run = runGitWithCheck(
        code,
        activeTask.seedCommands,
        activeTask.check,
      )
      setOutput(formatGitChannels(run))
      setPanel(snapshotPanel(run.state))
      setCheckFeedback({
        passed: run.passed,
        text: run.feedback.replace(/^(PASS|FAIL):\s*/i, ''),
      })
    } finally {
      setIsRunning(false)
    }
  }, [activeTask, code])

  const selectTask = (task: GitTask) => {
    setSearchParams({ tab: 'tasks', task: task.id })
    setCode(formatTaskStarter(task))
    setOutput('')
    setPanel('')
    setCheckFeedback(null)
  }

  const fileLabel = activeTask
    ? `${activeTask.id.replace(/-/g, '_')}.sh`
    : 'commands.sh'
  const statusTone = isRunning
    ? 'code-ide-status--busy'
    : 'code-ide-status--ok'

  return (
    <PageShell content="article">
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Git</p>
        <h1 className="learn-title">Git в браузере</h1>
        <p className="learn-lead">
          Симулятор команд (без диска и GitHub). Задачи связаны с{' '}
          <Link to="/game/learn">Learn</Link> B02 / B06 / S01E03 и серией GIT01–GIT06.
          Полный <code>rebase -i</code> и живые hooks — в лекциях, не здесь.
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
            <span className="code-ide-title">9to18 · git — {fileLabel}</span>
            <span className={`code-ide-status ${statusTone}`}>
              {isRunning ? 'running' : 'ready'}
            </span>
          </div>

          <div className="code-ide-menubar" role="tablist" aria-label="Режим Git">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === 'sandbox'}
              className={`code-ide-tab${activeTab === 'sandbox' ? ' code-ide-tab--active' : ''}`}
              onClick={() => setSearchParams({})}
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
              tasks/{GIT_TASKS.length}
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
                {GIT_TASKS.map((task) => (
                  <li key={task.id}>
                    <button
                      type="button"
                      className={`code-task-item${activeTask?.id === task.id ? ' code-task-item--active' : ''}`}
                      onClick={() => selectTask(task)}
                    >
                      <span className="code-task-ep">{task.episode}</span>
                      <span className="code-task-file">{task.id}.sh</span>
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
                sh
              </span>
              {fileLabel}
            </div>
            <div className="code-sandbox-actions">
              <button
                type="button"
                className="code-ide-btn code-ide-btn--run"
                disabled={isRunning}
                onClick={() => onRun()}
              >
                {isRunning ? '▶ …' : '▶ Run'}
              </button>
              {activeTab === 'tasks' && activeTask && (
                <button
                  type="button"
                  className="code-ide-btn code-ide-btn--check"
                  disabled={isRunning}
                  onClick={() => onCheckTask()}
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
                    setCode(DEFAULT_SCRIPT)
                    clearGitDraft()
                  }
                  setOutput('')
                  setPanel('')
                  setCheckFeedback(null)
                }}
              >
                Reset
              </button>
              <button
                type="button"
                className="code-ide-btn"
                onClick={() => {
                  void (async () => {
                    const url = new URL(window.location.href)
                    url.search = ''
                    url.searchParams.set('code', code)
                    const href = url.toString()
                    if (href.length > 8000) {
                      await navigator.clipboard.writeText(code)
                      setStatus('Скрипт скопирован (ссылка слишком длинная)')
                      return
                    }
                    await navigator.clipboard.writeText(href)
                    setStatus('Ссылка на скрипт скопирована')
                  })()
                }}
              >
                Share
              </button>
            </div>
          </div>

          <label className="sr-only" htmlFor="git-editor">
            Команды
          </label>
          <CodeSandboxEditor
            key={activeTask?.id ?? (searchParams.get('code') ? 'query' : 'sandbox')}
            id="git-editor"
            language="shell"
            value={code}
            onChange={setCode}
            onRun={() => {
              if (isRunning) return
              if (activeTab === 'tasks' && activeTask) onCheckTask()
              else onRun()
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
              <span className="code-ide-panel-meta">git · simulator</span>
            </div>
            <pre className="code-sandbox-output" aria-live="polite">
              <span className="code-term-line code-term-line--meta">
                $ sh {fileLabel}
              </span>
              {output ? `\n${output}` : '\n█'}
            </pre>
          </div>

          {panel ? (
            <div className="code-ide-terminal">
              <div className="code-ide-panel-head">
                <span className="code-ide-panel-label">LOG</span>
                <span className="code-ide-panel-meta">oneline</span>
              </div>
              <pre className="code-sandbox-output">{panel}</pre>
            </div>
          ) : null}
        </div>

        <aside className="code-sandbox-side" aria-label="Заготовки Learn">
          <div className="code-ide-panel-head">
            <span className="code-ide-panel-label">SNIPPETS</span>
            <span className="code-ide-panel-meta">learn/</span>
          </div>
          <p className="code-side-note">```bash с git из Learn → в редактор</p>
          {!postsReady ? (
            <p className="code-side-note">loading…</p>
          ) : snippets.length === 0 ? (
            <p className="code-side-note">
              нет блоков · <Link to="/game/learn">/game/learn</Link>
            </p>
          ) : (
            <ul className="code-snippet-list">
              {snippets.map((snippet) => (
                <li key={`${snippet.slug}-${snippet.source}-${snippet.blockIndex}`}>
                  <button
                    type="button"
                    className="code-snippet-item"
                    onClick={() => {
                      setSearchParams({})
                      setCode(snippet.code)
                      setOutput('')
                      setCheckFeedback(null)
                    }}
                  >
                    <span className="code-task-ep">{snippet.episode}</span>
                    <span>
                      {snippet.shortTitle}
                      {snippet.source === 'lab' ? '/lab' : '/theory'}
                      {snippet.blockIndex > 0
                        ? `:${snippet.blockIndex + 1}`
                        : ''}
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
