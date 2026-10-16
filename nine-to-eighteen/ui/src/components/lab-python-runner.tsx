import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  extractPythonBlocks,
  formatRunChannels,
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
      const run = await runPythonInSandbox(blocks[index])
      setOutputs((prev) => ({
        ...prev,
        [index]: formatRunChannels(run),
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
        <div key={index} className="lab-python-block code-ide code-ide--lab">
          <div className="code-ide-titlebar" aria-hidden="true">
            <span className="code-ide-dots">
              <span className="code-ide-dot code-ide-dot--red" />
              <span className="code-ide-dot code-ide-dot--amber" />
              <span className="code-ide-dot code-ide-dot--green" />
            </span>
            <span className="code-ide-title">lab · block_{index + 1}.py</span>
          </div>
          <pre className="lab-python-source">{block}</pre>
          <div className="code-ide-toolbar">
            <div className="code-sandbox-actions">
              <button
                type="button"
                className="code-ide-btn code-ide-btn--run"
                disabled={busyIndex !== null}
                onClick={() => void runBlock(index)}
              >
                {busyIndex === index ? '▶ …' : `▶ Run #${index + 1}`}
              </button>
              <Link
                className="code-ide-btn"
                to={`/game/code?code=${encodeURIComponent(block)}`}
              >
                Open in Code
              </Link>
            </div>
          </div>
          {outputs[index] ? (
            <div className="code-ide-terminal">
              <div className="code-ide-panel-head">
                <span className="code-ide-panel-label">TERMINAL</span>
              </div>
              <pre className="code-sandbox-output" aria-live="polite">
                <span className="code-term-line code-term-line--meta">
                  $ python block_{index + 1}.py
                </span>
                {`\n${outputs[index]}`}
              </pre>
            </div>
          ) : null}
        </div>
      ))}
    </section>
  )
}
