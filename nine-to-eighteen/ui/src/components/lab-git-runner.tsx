import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  extractGitBlocks,
  formatGitChannels,
  runGitSandboxScript,
} from '@/game/git/sandbox-git'
import {
  gitTasksForLearnEpisode,
  type GitTask,
} from '@/game/git/tasks'

type LabGitRunnerProps = {
  labMarkdown: string
  episode: string
  slug: string
}

const GIT_TRAINER_SLUGS = new Set([
  'b01-karta',
  'b05-api-check',
  's01e03-git',
  'qa-pytest-ci-git',
])

export function isGitTrainerEpisode(episode: string, slug: string): boolean {
  if (episode.toUpperCase().startsWith('GIT')) return true
  return GIT_TRAINER_SLUGS.has(slug)
}

function TaskLinks({ tasks, related }: { tasks: GitTask[]; related: boolean }) {
  if (tasks.length === 0) {
    return (
      <p className="learn-section-note">
        Для этого выпуска нет отдельных задач Check — откройте{' '}
        <Link to="/game/git">Git-симулятор</Link>.
      </p>
    )
  }
  return (
    <>
      <p className="learn-section-note">
        {related
          ? 'Связанные задачи тренажёра:'
          : 'Задачи тренажёра для этого выпуска:'}
      </p>
      <ul className="code-task-list lab-sql-task-list">
        {tasks.map((task) => (
          <li key={task.id}>
            <Link
              className="code-task-item"
              to={`/game/git?task=${encodeURIComponent(task.id)}`}
            >
              <span className="code-task-ep">{task.episode}</span>
              <span className="code-task-file">{task.id}.sh</span>
              <span className="code-task-name">{task.title}</span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}

export function LabGitRunner({
  labMarkdown,
  episode,
  slug,
}: LabGitRunnerProps) {
  const blocks = useMemo(() => extractGitBlocks(labMarkdown), [labMarkdown])
  const { tasks, related } = useMemo(
    () => gitTasksForLearnEpisode(episode, slug),
    [episode, slug],
  )
  const [outputs, setOutputs] = useState<Record<number, string>>({})
  const [busyIndex, setBusyIndex] = useState<number | null>(null)

  function runBlock(index: number) {
    setBusyIndex(index)
    try {
      const run = runGitSandboxScript(blocks[index])
      setOutputs((prev) => ({
        ...prev,
        [index]: formatGitChannels(run),
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
    <section className="lab-python-runner" aria-label="Git из лабы">
      <h2 className="learn-panel-heading">Тренажёр Git</h2>
      <p className="learn-section-note">
        Симулятор команд в браузере · <Link to="/game/git">полная песочница</Link>
        {tasks.length > 0 ? (
          <>
            {' '}
            · <Link to="/game/git?tab=tasks">все задачи</Link>
          </>
        ) : null}
      </p>

      <TaskLinks tasks={tasks} related={related} />

      {blocks.length === 0 ? (
        <p className="learn-section-note">
          В тексте лабы нет блоков <code>```bash</code> с git — выполняйте шаги в{' '}
          <Link to="/game/git">/game/git</Link> или по ссылкам задач выше.
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
                <span className="code-ide-title">lab · block_{index + 1}.sh</span>
              </div>
              <pre className="lab-python-source">{block}</pre>
              <div className="code-ide-toolbar">
                <div className="code-sandbox-actions">
                  <button
                    type="button"
                    className="code-ide-btn code-ide-btn--run"
                    disabled={busyIndex !== null}
                    onClick={() => runBlock(index)}
                  >
                    {busyIndex === index ? '▶ …' : `▶ Run #${index + 1}`}
                  </button>
                  <Link
                    className="code-ide-btn"
                    to={`/game/git?code=${encodeURIComponent(block)}`}
                  >
                    Open in Git
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
                      $ sh block_{index + 1}.sh
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
