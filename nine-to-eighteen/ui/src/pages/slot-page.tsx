import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { postsWithBundledEpisodes } from '@/data/learn/learn-store'
import {
  LEARN_LEVELS,
  isLearnLevelId,
  isLearnProfileId,
  profileLabel,
} from '@/data/learn/labels'
import { LEARN_LEVEL_FILTER_KEY, LEARN_PROFILE_FILTER_KEY, writeRecallMark, type RecallMark } from '@/data/learn/recall'
import {
  createSlotRun,
  formatSlotLeft,
  readSlotRun,
  slotStepKey,
  writeSlotRun,
  type SlotRun,
} from '@/data/learn/slot'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'

const MARKS: Array<{ id: RecallMark; label: string }> = [
  { id: 'missed', label: 'Не знал' },
  { id: 'stumbled', label: 'Запнулся' },
  { id: 'said', label: 'Сказал' },
]

function words(value: string): number {
  return value.trim().split(/\s+/).filter(Boolean).length
}

export function SlotPage() {
  const { posts, isReady } = useLearnPosts()
  const published = postsWithBundledEpisodes(getPublishedPosts(posts))
  const [run, setRun] = useState<SlotRun | null>(() => readSlotRun())
  const [now, setNow] = useState(() => Date.now())
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (run || !isReady) {
      return
    }
    const profile = window.localStorage.getItem(LEARN_PROFILE_FILTER_KEY) || ''
    const level = window.localStorage.getItem(LEARN_LEVEL_FILTER_KEY) || ''
    const next = createSlotRun(
      published,
      isLearnProfileId(profile) ? profile : '',
      isLearnLevelId(level) ? level : '',
    )
    writeSlotRun(next)
    setRun(next)
  }, [run, isReady, published])

  function save(next: SlotRun) {
    writeSlotRun(next)
    setRun(next)
  }

  function restart() {
    const profile = window.localStorage.getItem(LEARN_PROFILE_FILTER_KEY) || ''
    const level = window.localStorage.getItem(LEARN_LEVEL_FILTER_KEY) || ''
    const next = createSlotRun(
      published,
      isLearnProfileId(profile) ? profile : '',
      isLearnLevelId(level) ? level : '',
    )
    writeSlotRun(next)
    setOpen(false)
    setRun(next)
  }

  if (!run) {
    return (
      <PageShell content="article">
        <p className="learn-section-note">Собираем слот…</p>
      </PageShell>
    )
  }

  const step = run.steps[run.index]
  const left = run.endsAt - now
  const profileName = isLearnProfileId(run.profile) ? profileLabel(run.profile) : 'все специальности'
  const levelName = LEARN_LEVELS.find((item) => item.id === run.level)?.label

  return (
    <PageShell content="article">
      <Link to="/game/interview" className="back-link">
        ← Лента
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Слот · {formatSlotLeft(left)}</p>
        <h1 className="learn-title">25 минут</h1>
        <p className="learn-lead">
          STAR, три вопроса из сегодняшней очереди и одна задача. Статья открывается после своей
          попытки. Отметки вопросов попадают в ту же очередь: «не знал» завтра, «запнулся» через 3
          дня, «сказал» через 7. Сейчас: {profileName}
          {levelName ? `, ${levelName}` : ''}.
        </p>
      </header>
      <p className="learn-section-note">
        Шаг {Math.min(run.index + 1, run.steps.length)} из {run.steps.length}
        {left <= 0 ? '. Время слота вышло, отметки всё ещё можно поставить.' : ''}
      </p>
      {!step ? (
        <section className="quiz-question">
          <h2 className="quiz-setup-title">Слот закрыт</h2>
          <p className="learn-lead">
            Вопросы с отметками уже в ленте. Завтра сессия начнётся с «не знал».
          </p>
          <p className="learn-admin-actions">
            <Link to="/game/interview" className="learn-admin-btn learn-admin-btn-primary">
              К очереди
            </Link>
            <button type="button" className="learn-admin-btn" onClick={restart}>
              Новый слот
            </button>
          </p>
        </section>
      ) : step.kind === 'star' ? (
        <StarStep
          attempted={run.attempted.includes('star')}
          onAttempt={() => {
            if (!run.attempted.includes('star')) {
              save({ ...run, attempted: [...run.attempted, 'star'] })
            }
          }}
          onNext={() => {
            setOpen(false)
            save({ ...run, index: run.index + 1 })
          }}
        />
      ) : step.kind === 'question' ? (
        <section className="quiz-question">
          <p className="quiz-question-index">
            {step.episodeCode} · {step.episodeTitle}
          </p>
          <p className="quiz-question-prompt">{step.prompt}</p>
          {open || run.attempted.includes(step.id) ? (
            <>
              <p className="learn-lead">{step.answer}</p>
              <p className="learn-section-note">
                <Link to={`/game/learn/${step.episodeSlug}`}>Статья-справочник</Link>
              </p>
              <div className="learn-admin-actions">
                {MARKS.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    className="learn-admin-btn"
                    onClick={() => {
                      writeRecallMark(step.id, option.id)
                      setOpen(false)
                      save({
                        ...run,
                        index: run.index + 1,
                        attempted: run.attempted.includes(step.id)
                          ? run.attempted
                          : [...run.attempted, step.id],
                      })
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <button
                type="button"
                className="learn-admin-btn"
                onClick={() => {
                  setOpen(true)
                  save({
                    ...run,
                    attempted: run.attempted.includes(step.id)
                      ? run.attempted
                      : [...run.attempted, step.id],
                  })
                }}
              >
                Показать ответ
              </button>
              <p className="learn-section-note">Статья откроется после своей попытки.</p>
            </>
          )}
        </section>
      ) : (
        <section className="quiz-question">
          <h2 className="quiz-setup-title">{step.label}</h2>
          <p className="learn-lead">
            Одна задача руками. Слот подождёт в этой вкладке: таймер идёт, пока вы в тренажёре.
          </p>
          <p className="learn-admin-actions">
            <Link
              to={step.href}
              className="learn-admin-btn learn-admin-btn-primary"
              onClick={() => {
                const key = slotStepKey(step)
                if (!run.attempted.includes(key)) {
                  save({ ...run, attempted: [...run.attempted, key] })
                }
              }}
            >
              Открыть задачу
            </Link>
            {run.attempted.includes(slotStepKey(step)) ? (
              <button
                type="button"
                className="learn-admin-btn"
                onClick={() => save({ ...run, index: run.index + 1 })}
              >
                Дальше
              </button>
            ) : null}
          </p>
        </section>
      )}
      {step ? (
        <p className="learn-section-note">
          <button type="button" className="learn-admin-btn" onClick={restart}>
            Начать слот заново
          </button>
        </p>
      ) : null}
    </PageShell>
  )
}

function StarStep({
  attempted,
  onAttempt,
  onNext,
}: {
  attempted: boolean
  onAttempt: () => void
  onNext: () => void
}) {
  const [situation, setSituation] = useState('')
  const [task, setTask] = useState('')
  const [action, setAction] = useState('')
  const [result, setResult] = useState('')
  const [verdict, setVerdict] = useState('')

  function check() {
    const actionWords = words(action)
    const situationWords = words(situation)
    const filled = [situation, task, action, result].every((value) => words(value) >= 3)
    const actionLeads = actionWords > situationWords
    setVerdict(
      filled && actionLeads
        ? 'Действие длиннее ситуации. Это уже ответ, а не пересказ обстоятельств.'
        : 'Нужны все четыре поля, хотя бы по три слова. Действие должно быть длиннее ситуации.',
    )
    onAttempt()
  }

  return (
    <section className="quiz-question">
      <h2 className="quiz-setup-title">STAR</h2>
      <p className="learn-lead">
        На ревью нашли, что сумма заказа расходится с таблицей, релиз через два часа. Сначала
        скажите вслух, потом запишите.
      </p>
      <label className="learn-filter-field">
        <span>Ситуация</span>
        <textarea value={situation} onChange={(event) => setSituation(event.target.value)} rows={2} />
      </label>
      <label className="learn-filter-field">
        <span>Задача</span>
        <textarea value={task} onChange={(event) => setTask(event.target.value)} rows={2} />
      </label>
      <label className="learn-filter-field">
        <span>Действие</span>
        <textarea value={action} onChange={(event) => setAction(event.target.value)} rows={3} />
      </label>
      <label className="learn-filter-field">
        <span>Результат</span>
        <textarea value={result} onChange={(event) => setResult(event.target.value)} rows={2} />
      </label>
      <div className="learn-admin-actions">
        <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={check}>
          Проверить
        </button>
        {attempted ? (
          <button type="button" className="learn-admin-btn" onClick={onNext}>
            Дальше
          </button>
        ) : null}
      </div>
      {verdict ? <p className="learn-section-note">{verdict}</p> : null}
    </section>
  )
}
