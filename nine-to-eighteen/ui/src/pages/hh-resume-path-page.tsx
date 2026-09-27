import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { getEpisodeBySlug } from '@/data/learn'
import {
  resumeApplyQuestionnaire,
  resumeCreate,
  resumeGet,
  resumeGetQuestionnaire,
  resumeMockChatMessage,
  resumeMockChatStart,
  resumePathPrepare,
  resumeUploadSource,
  type MockChatMessage,
  type PathRecommendation,
  type ResumeQuestion,
  type ResumeQuestionnaire,
  type SiteResumeSkill,
} from '@/data/site/resume-api'
import { useSiteAuthSession } from '@/data/site/site-auth'

type PathStep = 'source' | 'quiz' | 'prepare' | 'interview'

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

function episodeTitle(slug: string): string {
  return getEpisodeBySlug(slug)?.title || slug
}

const STEP_LABELS: Record<PathStep, string> = {
  source: 'Резюме',
  quiz: 'Специальность',
  prepare: 'Лекции и навыки',
  interview: 'Интервью',
}

/** Пошаговый путь: загрузка → опросник → рекомендации → mock-interview. */
export function HhResumePathPage() {
  const { resumeId: resumeIdParam } = useParams()
  const session = useSiteAuthSession()
  const navigate = useNavigate()

  const [resumeId, setResumeId] = useState(resumeIdParam || '')
  const [step, setStep] = useState<PathStep>('source')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  const [pasteText, setPasteText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [sourceChars, setSourceChars] = useState(0)
  const [detectedKeys, setDetectedKeys] = useState<string[]>([])

  const [schema, setSchema] = useState<ResumeQuestionnaire | null>(null)
  const [answers, setAnswers] = useState<Record<string, unknown>>({})
  const [quizStep, setQuizStep] = useState(0)

  const [skills, setSkills] = useState<SiteResumeSkill[]>([])
  const [recommendations, setRecommendations] = useState<PathRecommendation[]>([])

  const [chatSessionId, setChatSessionId] = useState('')
  const [chatMessages, setChatMessages] = useState<MockChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatDone, setChatDone] = useState(false)
  const [chatSummary, setChatSummary] = useState('')
  const [chatTurn, setChatTurn] = useState(0)
  const [chatMaxTurns, setChatMaxTurns] = useState(5)

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
          navigate(`/game/hh-resume/${id}/path`, { replace: true })
          return
        }
        const [resume, questionnaire] = await Promise.all([
          resumeGet(id),
          resumeGetQuestionnaire(),
        ])
        if (cancelled) return
        setResumeId(id)
        setSchema(questionnaire)
        const savedAnswers = resume.questionnaireAnswers || {}
        const hasAnswers = Object.keys(savedAnswers).length > 0
        setAnswers(hasAnswers ? { ...emptyAnswers(questionnaire.questions), ...savedAnswers } : emptyAnswers(questionnaire.questions))
        const src = (resume.sourceText || '').trim()
        if (src) {
          setPasteText(src)
          setSourceChars(src.length)
        }
        if (resume.generatedSkills?.length) {
          setSkills(resume.generatedSkills)
        }
        if (src && hasAnswers && String(savedAnswers.role_track || '').trim()) {
          setStep('prepare')
        } else if (src) {
          setStep('quiz')
        } else {
          setStep('source')
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить путь')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [session?.accessToken, resumeIdParam, navigate])

  const questions = schema?.questions || []
  const currentQ = questions[quizStep]
  const quizProgress = useMemo(() => {
    if (!questions.length) return 0
    return Math.round(((quizStep + 1) / questions.length) * 100)
  }, [questions.length, quizStep])

  const onSubmitSource = useCallback(async () => {
    if (!resumeId) return
    if (!file && !pasteText.trim()) {
      setError('Загрузите PDF/DOCX или вставьте текст резюме')
      return
    }
    setBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeUploadSource(resumeId, {
        file,
        text: pasteText,
      })
      setSourceChars(result.chars)
      setDetectedKeys(result.detectedSkillKeys)
      setPasteText(result.sourceText)
      setOk(`Текст сохранён (${result.chars} символов)`)
      setStep('quiz')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки')
    } finally {
      setBusy(false)
    }
  }, [resumeId, file, pasteText])

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

  async function onSubmitQuiz(event?: FormEvent) {
    event?.preventDefault()
    if (!schema || !resumeId) return
    for (const q of schema.questions) {
      if (q.required && !isAnswered(q, answers)) {
        setError(`Ответьте на вопрос: ${q.title}`)
        const idx = schema.questions.findIndex((item) => item.id === q.id)
        if (idx >= 0) setQuizStep(idx)
        return
      }
    }
    setBusy(true)
    setError('')
    try {
      await resumeApplyQuestionnaire(resumeId, { answers, persist: true })
      const prepared = await resumePathPrepare(resumeId, true)
      setSkills(prepared.skills)
      setRecommendations(prepared.recommendations)
      setDetectedKeys(prepared.detectedSkillKeys)
      setOk('Навыки и рекомендации обновлены')
      setStep('prepare')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось применить опросник')
    } finally {
      setBusy(false)
    }
  }

  function onQuizNext() {
    if (!currentQ) return
    if (currentQ.required && !isAnswered(currentQ, answers)) {
      setError('Выберите вариант, чтобы продолжить')
      return
    }
    setError('')
    if (quizStep >= questions.length - 1) {
      void onSubmitQuiz()
      return
    }
    setQuizStep((s) => s + 1)
  }

  async function onRefreshPrepare() {
    if (!resumeId) return
    setBusy(true)
    setError('')
    try {
      const prepared = await resumePathPrepare(resumeId, true)
      setSkills(prepared.skills)
      setRecommendations(prepared.recommendations)
      setOk('Рекомендации обновлены')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка подготовки')
    } finally {
      setBusy(false)
    }
  }

  async function onStartInterview() {
    if (!resumeId || skills.length === 0) return
    setBusy(true)
    setError('')
    setChatInput('')
    setChatSummary('')
    setChatDone(false)
    try {
      const data = await resumeMockChatStart(resumeId, 5)
      setChatSessionId(data.sessionId)
      setChatMessages(data.messages || [])
      setChatTurn(data.turn)
      setChatMaxTurns(data.maxTurns)
      setStep('interview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось начать собеседование')
    } finally {
      setBusy(false)
    }
  }

  async function onSendChat() {
    if (!resumeId || !chatSessionId || !chatInput.trim()) return
    setBusy(true)
    setError('')
    try {
      const result = await resumeMockChatMessage(
        resumeId,
        chatSessionId,
        chatInput.trim(),
      )
      setChatMessages(result.messages)
      setChatTurn(result.turn)
      setChatMaxTurns(result.maxTurns)
      setChatDone(result.done)
      setChatInput('')
      if (result.done) {
        setChatSummary(
          result.summary ||
            (result.overallScore != null
              ? `Средняя оценка ${result.overallScore}/5`
              : 'Собеседование завершено'),
        )
        setOk('Собеседование завершено — можно открыть редактор или превью.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка чата')
    } finally {
      setBusy(false)
    }
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
      <Link to="/game/hh-resume" className="back-link">
        ← К списку
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">HH-резюме · путь</p>
        <h1 className="learn-title">Путь к резюме</h1>
        <p className="learn-lead">
          Загрузите резюме, укажите желаемую специальность, получите рекомендации лекций, навыки и
          тренировочные вопросы.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      <nav className="hh-path-steps" aria-label="Шаги пути">
        {(Object.keys(STEP_LABELS) as PathStep[]).map((key) => (
          <button
            key={key}
            type="button"
            className={
              step === key
                ? 'hh-path-step is-active'
                : 'hh-path-step'
            }
            disabled={busy || loading}
            onClick={() => {
              if (key === 'source') setStep('source')
              else if (key === 'quiz' && sourceChars > 0) setStep('quiz')
              else if (key === 'prepare' && (skills.length > 0 || recommendations.length > 0)) {
                setStep('prepare')
              } else if (key === 'interview' && skills.length > 0) setStep('interview')
            }}
          >
            {STEP_LABELS[key]}
          </button>
        ))}
      </nav>

      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : null}

      {!loading && step === 'source' ? (
        <section className="hh-resume-ai-block" aria-label="Загрузка резюме">
          <h2 className="account-subheading">1. Ваше резюме</h2>
          <p className="learn-section-note">
            PDF или DOCX (до 8 МБ) и/или вставка текста. Навыки появятся только если они
            подтверждены текстом или уже пройденными лекциями.
          </p>
          <label className="learn-admin-field">
            <span>Файл PDF / DOCX</span>
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          <label className="learn-admin-field">
            <span>Или вставьте текст</span>
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={10}
              maxLength={50_000}
              placeholder="Вставьте текст резюме…"
            />
          </label>
          {sourceChars > 0 ? (
            <p className="learn-section-note">
              Сохранено: {sourceChars} символов
              {detectedKeys.length ? ` · найдено: ${detectedKeys.join(', ')}` : ''}
            </p>
          ) : null}
          <div className="account-actions">
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy}
              onClick={() => void onSubmitSource()}
            >
              Сохранить и далее
            </button>
          </div>
        </section>
      ) : null}

      {!loading && step === 'quiz' && currentQ ? (
        <form className="hh-quiz-card" onSubmit={(e) => void onSubmitQuiz(e)}>
          <h2 className="account-subheading">2. Желаемая специальность</h2>
          <div className="hh-quiz-progress" aria-hidden>
            <div className="hh-quiz-progress-bar" style={{ width: `${quizProgress}%` }} />
          </div>
          <p className="learn-section-note">
            Шаг {quizStep + 1} из {questions.length}
          </p>
          <h3 className="account-subheading">{currentQ.title}</h3>
          {currentQ.hint ? <p className="learn-section-note">{currentQ.hint}</p> : null}

          {currentQ.type === 'text' ? (
            <label className="learn-admin-field">
              <span className="sr-only">{currentQ.title}</span>
              <textarea
                value={String(answers[currentQ.id] || '')}
                onChange={(e) => setSingle(currentQ.id, e.target.value)}
                rows={4}
                maxLength={currentQ.maxLength || 500}
                placeholder={currentQ.placeholder || ''}
              />
            </label>
          ) : (
            <div className="hh-quiz-options" role="group" aria-label={currentQ.title}>
              {(currentQ.options || []).map((opt) => {
                const selected =
                  currentQ.type === 'multi'
                    ? Array.isArray(answers[currentQ.id]) &&
                      (answers[currentQ.id] as string[]).includes(opt.id)
                    : answers[currentQ.id] === opt.id
                return (
                  <label
                    key={opt.id}
                    className={selected ? 'hh-quiz-option is-selected' : 'hh-quiz-option'}
                  >
                    <input
                      type={currentQ.type === 'multi' ? 'checkbox' : 'radio'}
                      name={currentQ.id}
                      checked={selected}
                      onChange={() => {
                        if (currentQ.type === 'multi') {
                          toggleMulti(currentQ.id, opt.id)
                        } else {
                          setSingle(currentQ.id, opt.id)
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
              disabled={quizStep === 0 || busy}
              onClick={() => {
                setError('')
                setQuizStep((s) => Math.max(0, s - 1))
              }}
            >
              Назад
            </button>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy}
              onClick={onQuizNext}
            >
              {quizStep >= questions.length - 1 ? 'Получить рекомендации' : 'Далее'}
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => setStep('source')}
            >
              К загрузке
            </button>
          </div>
        </form>
      ) : null}

      {!loading && step === 'prepare' ? (
        <section className="hh-resume-ai-block" aria-label="Рекомендации">
          <h2 className="account-subheading">3. Лекции и навыки</h2>
          <p className="learn-section-note">
            В резюме попали только подтверждённые навыки. Ниже — модули Learn, с которыми стоит
            ознакомиться.
          </p>

          {skills.length > 0 ? (
            <div>
              <h3 className="account-subheading">Навыки в резюме</h3>
              <ul className="hh-resume-skill-list">
                {skills.map((skill) => (
                  <li key={skill.key}>
                    <span>{skill.display}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="learn-section-note">
              Пока нет подтверждённых навыков — пройдите рекомендованные лекции.
            </p>
          )}

          {recommendations.length > 0 ? (
            <div style={{ marginTop: '1.25rem' }}>
              <h3 className="account-subheading">Рекомендуем ознакомиться</h3>
              <ul className="hh-resume-gap-list">
                {recommendations.map((rec) => (
                  <li key={rec.skillKey}>
                    <strong>{rec.name}</strong>
                    {rec.evidenced ? ' · уже в резюме' : ' · ещё не в резюме'}
                    {rec.reason ? ` — ${rec.reason}` : ''}
                    <p className="hh-resume-gap-slugs">
                      {rec.learnSlugs.map((slug) => (
                        <Link key={slug} to={`/game/learn/${slug}`}>
                          {episodeTitle(slug)}
                        </Link>
                      ))}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="learn-section-note">По каталогу Learn для вашей роли пробелов нет.</p>
          )}

          <div className="account-actions" style={{ marginTop: '1.25rem' }}>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => void onRefreshPrepare()}
            >
              Обновить после Learn
            </button>
            {skills.length > 0 ? (
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={busy}
                onClick={() => void onStartInterview()}
              >
                К вопросам интервью
              </button>
            ) : (
              <p className="learn-section-note">
                Когда появятся подтверждённые навыки, станет доступно тренировочное собеседование.
              </p>
            )}
            {resumeId ? (
              <Link to={`/game/hh-resume/${resumeId}/edit`} className="learn-admin-btn">
                Открыть редактор
              </Link>
            ) : null}
          </div>
        </section>
      ) : null}

      {!loading && step === 'interview' ? (
        <section className="hh-resume-ai-block" aria-label="Mock interview chat">
          <h2 className="account-subheading">4. Техническое интервью</h2>
          {!chatSessionId ? (
            <>
              <p className="learn-section-note">
                {skills.length === 0
                  ? 'Сначала нужны подтверждённые навыки.'
                  : 'Нажмите, чтобы начать чат-собеседование по навыкам из резюме.'}
              </p>
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={busy || skills.length === 0}
                onClick={() => void onStartInterview()}
              >
                Начать собеседование
              </button>
            </>
          ) : (
            <div className="hh-mock-chat">
              <p className="learn-section-note">
                Ход {Math.min(chatTurn, chatMaxTurns)} / {chatMaxTurns}
                {chatDone ? ' · завершено' : ''}
              </p>
              <div className="hh-mock-chat-log" role="log">
                {chatMessages.map((msg, idx) => (
                  <div
                    key={`${msg.role}-${idx}`}
                    className={
                      msg.role === 'user'
                        ? 'hh-mock-chat-bubble is-user'
                        : 'hh-mock-chat-bubble is-assistant'
                    }
                  >
                    <span className="hh-mock-chat-role">
                      {msg.role === 'user' ? 'Вы' : 'Интервьюер'}
                    </span>
                    <p>{msg.content}</p>
                  </div>
                ))}
              </div>
              {chatSummary ? <p className="learn-admin-ok">{chatSummary}</p> : null}
              {!chatDone ? (
                <>
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    rows={4}
                    placeholder="Ваш ответ"
                  />
                  <div className="account-actions">
                    <button
                      type="button"
                      className="learn-admin-btn learn-admin-btn-primary"
                      disabled={busy || !chatInput.trim()}
                      onClick={() => void onSendChat()}
                    >
                      Отправить
                    </button>
                    {resumeId ? (
                      <Link to={`/game/hh-resume/${resumeId}`} className="learn-admin-btn">
                        К превью
                      </Link>
                    ) : null}
                  </div>
                </>
              ) : (
                <div className="account-actions">
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    disabled={busy}
                    onClick={() => void onStartInterview()}
                  >
                    Ещё раз
                  </button>
                  {resumeId ? (
                    <Link to={`/game/hh-resume/${resumeId}/edit`} className="learn-admin-btn">
                      В редактор
                    </Link>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </section>
      ) : null}
    </PageShell>
  )
}
