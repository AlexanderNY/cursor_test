import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  resumeApplyQuestionnaire,
  resumeCreate,
  resumeGetQuestionnaire,
  type ResumeQuestion,
  type ResumeQuestionnaire,
} from '@/data/site/resume-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

function emptyAnswers(questions: ResumeQuestion[]): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const q of questions) {
    if (q.type === 'multi') out[q.id] = []
    else if (q.type === 'text') out[q.id] = ''
    else out[q.id] = ''
  }
  return out
}

function isAnswered(q: ResumeQuestion, answers: Record<string, unknown>): boolean {
  const value = answers[q.id]
  if (q.type === 'multi') {
    return Array.isArray(value) && value.length > 0
  }
  if (q.type === 'text') {
    return !q.required || Boolean(String(value || '').trim())
  }
  return Boolean(String(value || '').trim())
}

export function HhResumeQuizPage() {
  const { resumeId: resumeIdParam } = useParams()
  const session = getSiteAuthSession()
  const navigate = useNavigate()
  const [resumeId, setResumeId] = useState(resumeIdParam || '')
  const [schema, setSchema] = useState<ResumeQuestionnaire | null>(null)
  const [answers, setAnswers] = useState<Record<string, unknown>>({})
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!session) {
      setLoading(false)
      return
    }
    let cancelled = false
    void (async () => {
      try {
        let id = resumeIdParam || ''
        if (!id) {
          const created = await resumeCreate({ version_name: 'Основное' })
          id = created.id
          if (!cancelled) setResumeId(id)
          navigate(`/game/hh-resume/${id}/quiz`, { replace: true })
        }
        const data = await resumeGetQuestionnaire()
        if (cancelled) return
        setSchema(data)
        setAnswers(emptyAnswers(data.questions))
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить опросник')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [session, resumeIdParam, navigate])

  const questions = schema?.questions || []
  const current = questions[step]
  const progress = useMemo(() => {
    if (!questions.length) return 0
    return Math.round(((step + 1) / questions.length) * 100)
  }, [questions.length, step])

  function setSingle(id: string, value: string) {
    setAnswers((prev) => ({ ...prev, [id]: value }))
  }

  function toggleMulti(id: string, optionId: string) {
    setAnswers((prev) => {
      const currentList = Array.isArray(prev[id]) ? (prev[id] as string[]) : []
      const next = currentList.includes(optionId)
        ? currentList.filter((x) => x !== optionId)
        : [...currentList, optionId]
      return { ...prev, [id]: next }
    })
  }

  async function onSubmit(event?: FormEvent) {
    event?.preventDefault()
    if (!schema || !resumeId) return
    for (const q of schema.questions) {
      if (q.required && !isAnswered(q, answers)) {
        setError(`Ответьте на вопрос: ${q.title}`)
        const idx = schema.questions.findIndex((item) => item.id === q.id)
        if (idx >= 0) setStep(idx)
        return
      }
    }
    setSubmitting(true)
    setError('')
    try {
      await resumeApplyQuestionnaire(resumeId, { answers, persist: true })
      navigate(`/game/hh-resume/${resumeId}/edit`, {
        replace: false,
        state: { fromQuiz: true },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось применить опросник')
    } finally {
      setSubmitting(false)
    }
  }

  function onNext() {
    if (!current) return
    if (current.required && !isAnswered(current, answers)) {
      setError('Выберите вариант, чтобы продолжить')
      return
    }
    setError('')
    if (step >= questions.length - 1) {
      void onSubmit()
      return
    }
    setStep((s) => s + 1)
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К списку
        </Link>
        <p className="learn-section-note">
          <Link to="/login">Войти</Link>
        </p>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to={resumeId ? `/game/hh-resume/${resumeId}` : '/game/hh-resume'} className="back-link">
        ← Назад
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">HH-резюме · опросник</p>
        <h1 className="learn-title">{schema?.title || 'Идеальное резюме'}</h1>
        <p className="learn-lead">{schema?.lead || ''}</p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
      </header>

      {loading || !current ? (
        <p className="learn-section-note">Загрузка опросника…</p>
      ) : (
        <form className="hh-quiz-card" onSubmit={(e) => void onSubmit(e)}>
          <div className="hh-quiz-progress" aria-hidden>
            <div className="hh-quiz-progress-bar" style={{ width: `${progress}%` }} />
          </div>
          <p className="learn-section-note">
            Шаг {step + 1} из {questions.length}
          </p>
          <h2 className="account-subheading">{current.title}</h2>
          {current.hint ? <p className="learn-section-note">{current.hint}</p> : null}

          {current.type === 'text' ? (
            <label className="learn-admin-field">
              <span className="sr-only">{current.title}</span>
              <textarea
                value={String(answers[current.id] || '')}
                onChange={(e) => setSingle(current.id, e.target.value)}
                rows={4}
                maxLength={current.maxLength || 500}
                placeholder={current.placeholder || ''}
              />
            </label>
          ) : (
            <div className="hh-quiz-options" role="group" aria-label={current.title}>
              {(current.options || []).map((opt) => {
                const selected =
                  current.type === 'multi'
                    ? Array.isArray(answers[current.id]) &&
                      (answers[current.id] as string[]).includes(opt.id)
                    : answers[current.id] === opt.id
                return (
                  <label
                    key={opt.id}
                    className={selected ? 'hh-quiz-option is-selected' : 'hh-quiz-option'}
                  >
                    <input
                      type={current.type === 'multi' ? 'checkbox' : 'radio'}
                      name={current.id}
                      checked={selected}
                      onChange={() => {
                        if (current.type === 'multi') {
                          toggleMulti(current.id, opt.id)
                        } else {
                          setSingle(current.id, opt.id)
                        }
                      }}
                    />
                    <span>{opt.label}</span>
                  </label>
                )
              })}
            </div>
          )}

          <div className="account-actions">
            <button
              type="button"
              className="learn-admin-btn"
              disabled={step === 0 || submitting}
              onClick={() => {
                setError('')
                setStep((s) => Math.max(0, s - 1))
              }}
            >
              Назад
            </button>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={submitting}
              onClick={onNext}
            >
              {step >= questions.length - 1 ? 'Собрать резюме' : 'Далее'}
            </button>
            {resumeId ? (
              <Link to={`/game/hh-resume/${resumeId}/edit`} className="learn-admin-btn">
                Пропустить → правка
              </Link>
            ) : null}
          </div>
        </form>
      )}
    </PageShell>
  )
}
