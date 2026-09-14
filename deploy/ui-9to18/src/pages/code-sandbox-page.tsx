import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  loadSandboxPyodide,
  runPythonInSandbox,
} from '@/game/code/sandbox-pyodide'

const DEFAULT_CODE = `# Python в браузере (Pyodide)
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("9to18"))
sum(range(10))
`

export function CodeSandboxPage() {
  const [searchParams] = useSearchParams()
  const [code, setCode] = useState(DEFAULT_CODE)
  const [output, setOutput] = useState('')
  const [status, setStatus] = useState('Загрузка runtime…')
  const [isReady, setIsReady] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    const fromQuery = searchParams.get('code')
    if (fromQuery) {
      try {
        setCode(decodeURIComponent(fromQuery))
      } catch {
        setCode(fromQuery)
      }
    }
  }, [searchParams])

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
          setStatus('Runtime готов')
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus(err instanceof Error ? err.message : 'Не удалось загрузить Pyodide')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const onRun = useCallback(async () => {
    setIsRunning(true)
    setOutput('')
    try {
      const { stdout, stderr, result } = await runPythonInSandbox(code)
      const parts: string[] = []
      if (stdout.trim()) {
        parts.push(stdout.trimEnd())
      }
      if (result.trim()) {
        parts.push(`⟹ ${result}`)
      }
      if (stderr.trim()) {
        parts.push(`Error:\n${stderr.trimEnd()}`)
      }
      setOutput(parts.join('\n\n') || '(нет вывода)')
    } finally {
      setIsRunning(false)
    }
  }, [code])

  return (
    <PageShell content="article">
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Code</p>
        <h1 className="learn-title">Python в браузере</h1>
        <p className="learn-lead">
          Песочница на Pyodide — без сервера и установки. Подходит для коротких упражнений из{' '}
          <Link to="/game/learn">Learn</Link>.
        </p>
        <p className="learn-section-note">{status}</p>
      </header>

      <div className="code-sandbox">
        <label className="code-sandbox-label" htmlFor="code-editor">
          Код
        </label>
        <textarea
          id="code-editor"
          className="code-sandbox-editor"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          spellCheck={false}
          rows={16}
        />
        <div className="code-sandbox-actions">
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={!isReady || isRunning}
            onClick={() => void onRun()}
          >
            {isRunning ? 'Выполняется…' : 'Запустить'}
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() => {
              setCode(DEFAULT_CODE)
              setOutput('')
            }}
          >
            Сбросить
          </button>
        </div>
        <h2 className="learn-panel-heading">Вывод</h2>
        <pre className="code-sandbox-output" aria-live="polite">
          {output || '—'}
        </pre>
      </div>
    </PageShell>
  )
}
