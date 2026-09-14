import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  extractPythonBlocks,
  runPythonInSandbox,
} from '@/game/code/sandbox-pyodide'

type LabPythonRunnerProps = {
  labMarkdown: string
}

export function LabPythonRunner({ labMarkdown }: LabPythonRunnerProps) {
  const blocks = useMemo(() => extractPythonBlocks(labMarkdown), [labMarkdown])
  const [outputs, setOutputs] = useState<Record<number, string>>({})
  const [busyIndex, setBusyIndex] = useState<number | null>(null)

  if (blocks.length === 0) {
    return (
      <p className="learn-section-note">
        В лабе нет блоков <code>```python</code>. Откройте{' '}
        <Link to="/game/code">Code</Link> для свободной песочницы.
      </p>
    )
  }

  async function runBlock(index: number) {
    setBusyIndex(index)
    try {
      const { stdout, stderr, result } = await runPythonInSandbox(blocks[index])
      const parts: string[] = []
      if (stdout.trim()) parts.push(stdout.trimEnd())
      if (result.trim()) parts.push(`⟹ ${result}`)
      if (stderr.trim()) parts.push(`Error:\n${stderr.trimEnd()}`)
      setOutputs((prev) => ({
        ...prev,
        [index]: parts.join('\n\n') || '(нет вывода)',
      }))
    } catch (err) {
      setOutputs((prev) => ({
        ...prev,
        [index]: err instanceof Error ? err.message : String(err),
      }))
    } finally {
      setBusyIndex(null)
    }
  }

  return (
    <section className="lab-python-runner" aria-label="Запуск Python из лабы">
      <h2 className="learn-panel-heading">Запустить в браузере</h2>
      <p className="learn-section-note">
        Блоки <code>python</code> из текста лабы · runtime Pyodide ·{' '}
        <Link to="/game/code">полная песочница</Link>
      </p>
      {blocks.map((block, index) => (
        <div key={index} className="lab-python-block">
          <pre className="code-sandbox-output lab-python-source">{block}</pre>
          <div className="code-sandbox-actions">
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busyIndex !== null}
              onClick={() => void runBlock(index)}
            >
              {busyIndex === index ? 'Выполняется…' : `Запустить #${index + 1}`}
            </button>
            <Link
              className="learn-admin-btn"
              to={`/game/code?code=${encodeURIComponent(block)}`}
            >
              Открыть в Code
            </Link>
          </div>
          {outputs[index] ? (
            <pre className="code-sandbox-output" aria-live="polite">
              {outputs[index]}
            </pre>
          ) : null}
        </div>
      ))}
    </section>
  )
}
