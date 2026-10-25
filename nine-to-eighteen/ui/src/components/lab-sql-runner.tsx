import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  extractSqlBlocks,
  formatSqlRunChannels,
  runSqlInSandbox,
} from '@/game/sql/sandbox-sqlite'
import { schemaForFreeSql } from '@/game/sql/schemas'
import {
  sqlTasksForLearnEpisode,
  type SqlTask,
} from '@/game/sql/tasks'

type LabSqlRunnerProps = {
  labMarkdown: string
  episode: string
}

function TaskLinks({ tasks, related }: { tasks: SqlTask[]; related: boolean }) {
  if (tasks.length === 0) {
    return (
      <p className="learn-section-note">
        Для этого выпуска нет отдельных задач Check — откройте{' '}
        <Link to="/game/sql">SQL-песочницу</Link>.
      </p>
    )
  }
  return (
    <>
      <p className="learn-section-note">
        {related
          ? 'Связанные задачи тренажёра (эпизод без своих Check-задач):'
          : 'Задачи тренажёра для этого выпуска:'}
      </p>
      <ul className="code-task-list lab-sql-task-list">
        {tasks.map((task) => (
          <li key={task.id}>
            <Link
              className="code-task-item"
              to={`/game/sql?task=${encodeURIComponent(task.id)}`}
            >
              <span className="code-task-ep">{task.episode}</span>
              <span className="code-task-file">{task.id}.sql</span>
              <span className="code-task-name">{task.title}</span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}

export function LabSqlRunner({ labMarkdown, episode }: LabSqlRunnerProps) {
  const blocks = useMemo(() => extractSqlBlocks(labMarkdown), [labMarkdown])
  const { tasks, related } = useMemo(
    () => sqlTasksForLearnEpisode(episode),
    [episode],
  )
  const [outputs, setOutputs] = useState<Record<number, string>>({})
  const [busyIndex, setBusyIndex] = useState<number | null>(null)

  async function runBlock(index: number) {
    setBusyIndex(index)
    try {
      const run = await runSqlInSandbox(
        blocks[index],
        schemaForFreeSql(blocks[index]),
      )
      setOutputs((prev) => ({
        ...prev,
        [index]: formatSqlRunChannels(run),
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
    <section className="lab-python-runner" aria-label="SQL из лабы">
      <h2 className="learn-panel-heading">Тренажёр SQL</h2>
      <p className="learn-section-note">
        Runtime SQLite (sql.js) в браузере ·{' '}
        <Link to="/game/sql">полная песочница</Link>
        {tasks.length > 0 ? (
          <>
            {' '}
            · <Link to="/game/sql?tab=tasks">все задачи</Link>
          </>
        ) : null}
      </p>

      <TaskLinks tasks={tasks} related={related} />

      {blocks.length === 0 ? (
        <p className="learn-section-note">
          В тексте лабы нет блоков <code>```sql</code> — выполняйте шаги в{' '}
          <Link to="/game/sql">/game/sql</Link> или по ссылкам задач выше.
        </p>
      ) : (
        <>
          <h3 className="learn-panel-heading">Запустить блоки из лабы</h3>
          {blocks.map((block, index) => (
            <div key={index} className="lab-python-block code-ide code-ide--lab">
              <div className="code-ide-titlebar" aria-hidden="true">
                <span className="code-ide-dots">
                  <span className="code-ide-dot code-ide-dot--red" />
                  <span className="code-ide-dot code-ide-dot--amber" />
                  <span className="code-ide-dot code-ide-dot--green" />
                </span>
                <span className="code-ide-title">lab · block_{index + 1}.sql</span>
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
                    to={`/game/sql?code=${encodeURIComponent(block)}`}
                  >
                    Open in SQL
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
                      $ sqlite3 block_{index + 1}.sql
                    </span>
                    {`\n${outputs[index]}`}
                  </pre>
                </div>
              ) : null}
            </div>
          ))}
        </>
      )}
    </section>
  )
}
