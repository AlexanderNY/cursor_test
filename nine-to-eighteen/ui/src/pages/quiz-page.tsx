import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  INTERVIEW_TRACKS,
  buildInterviewQuiz,
  collectInterviewItems,
  countByTrack,
  type InterviewQuizQuestion,
  type InterviewTrackId,
} from '@/data/learn/interview-quiz'
import { postsWithBundledEpisodes } from '@/data/learn/learn-store'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'
import { INTERVIEW_CERT_MIN_TOTAL } from '@/data/site/cert-shared'
import { siteSubmitQuizAttempt } from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const SIZE_PRESETS = [5, 10, 15, 20] as const
const DEFAULT_SIZE = 10

type QuizPhase = 'setup' | 'play' | 'review'

function clampQuizSize(requested: number | 'all', poolSize: number): number {
  if (poolSize <= 0) {
    return 0
  }
  if (requested === 'all') {
    return poolSize
  }
  return Math.min(requested, poolSize)
}

export function QuizPage() {
  const { posts, isReady } = useLearnPosts()
  const published = postsWithBundledEpisodes(getPublishedPosts(posts))
  const [phase, setPhase] = useState<QuizPhase>('setup')
  const [track, setTrack] = useState<InterviewTrackId>('all')
  const [sizeChoice, setSizeChoice] = useState<number | 'all'>(DEFAULT_SIZE)
  const [round, setRound] = useState(1)
  const [activeTrack, setActiveTrack] = useState<InterviewTrackId>('all')
  const [activeSize, setActiveSize] = useState(DEFAULT_SIZE)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [saveNote, setSaveNote] = useState('')

  const items = useMemo(
    () => (isReady ? collectInterviewItems(published) : []),
    // Pool follows the loaded catalog, not a new array identity each render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isReady, posts],
  )
  const counts = useMemo(() => countByTrack(items), [items])
  const poolCount = counts[track] ?? 0
  const resolvedSize = clampQuizSize(sizeChoice, poolCount)

  useEffect(() => {
    if (poolCount <= 0 || sizeChoice === 'all') {
      return
    }
    if (sizeChoice > poolCount) {
      setSizeChoice(poolCount >= DEFAULT_SIZE ? DEFAULT_SIZE : 'all')
    }
  }, [poolCount, sizeChoice])

  const questions = useMemo((): InterviewQuizQuestion[] => {
    if (phase === 'setup') {
      return []
    }
    return buildInterviewQuiz(items, {
      track: activeTrack,
      size: activeSize,
      seed: round,
    })
  }, [phase, items, activeTrack, activeSize, round])

  const current = questions[questionIndex]
  const score = questions.reduce((sum, question) => {
    return sum + (answers[question.id] === question.correctIndex ? 1 : 0)
  }, 0)
  const hasCurrentAnswer = current ? answers[current.id] !== undefined : false
  const isLastQuestion = questions.length > 0 && questionIndex >= questions.length - 1

  function startQuiz(nextTrack: InterviewTrackId, nextSizeChoice: number | 'all') {
    const nextPool = counts[nextTrack] ?? 0
    const nextSize = clampQuizSize(nextSizeChoice, nextPool)
    if (nextSize <= 0) {
      return
    }
    setActiveTrack(nextTrack)
    setActiveSize(nextSize)
    setAnswers({})
    setQuestionIndex(0)
    setSaveNote('')
    setRound((value) => value + 1)
    setPhase('play')
  }

  function goSetup() {
    setPhase('setup')
    setAnswers({})
    setQuestionIndex(0)
    setSaveNote('')
  }

  function replaySame() {
    setAnswers({})
    setQuestionIndex(0)
    setSaveNote('')
    setRound((value) => value + 1)
    setPhase('play')
  }

  async function onSubmit() {
    const nextScore = questions.reduce((sum, question) => {
      return sum + (answers[question.id] === question.correctIndex ? 1 : 0)
    }, 0)
    setPhase('review')
    setSaveNote('')
    if (!getSiteAuthSession()?.accessToken) {
      setSaveNote('Войдите в кабинет, чтобы сохранить результат.')
      return
    }
    try {
      await siteSubmitQuizAttempt({
        source_type: 'quiz_page',
        source_key: activeTrack === 'all' ? 'learn/interview' : `learn/interview/${activeTrack}`,
        score: nextScore,
        total: questions.length,
        answers: questions.map((question) => ({
          id: question.id,
          selected: answers[question.id],
          correct: question.correctIndex,
        })),
      })
      setSaveNote('Результат сохранён в разделе «Учёба».')
    } catch (err) {
      setSaveNote(err instanceof Error ? err.message : 'Не удалось сохранить результат')
    }
  }

  return (
    <PageShell content="article">
      <Link to="/game/learn" className="back-link">
        ← Learn
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Quiz</p>
        <h1 className="learn-title">Собеседование</h1>
        <p className="learn-lead">
          Вопросы из раздела «Частые вопросы с собеседования». Правильный вариант — дословный
          ответ из статьи Learn. Результат 100% при минимум {INTERVIEW_CERT_MIN_TOTAL} вопросах
          открывает диплом в разделе{' '}
          <Link to="/game/cert">Сертификаты</Link>.
        </p>
      </header>

      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : items.length === 0 ? (
        <p className="learn-section-note">
          В опубликованных выпусках нет пар «вопрос / ответ» в разделе собеседования.
        </p>
      ) : phase === 'setup' ? (
        <div className="quiz-setup">
          <section className="quiz-setup-block" aria-labelledby="quiz-pool-label">
            <h2 id="quiz-pool-label" className="quiz-setup-title">
              Пул вопросов
            </h2>
            <div className="quiz-choice-grid" role="radiogroup" aria-labelledby="quiz-pool-label">
              {INTERVIEW_TRACKS.filter((item) => counts[item.id] > 0).map((item) => {
                const selected = track === item.id
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    className={`quiz-choice${selected ? ' is-active' : ''}`}
                    onClick={() => {
                      setTrack(item.id)
                      const nextPool = counts[item.id]
                      if (sizeChoice !== 'all' && sizeChoice > nextPool) {
                        setSizeChoice(nextPool >= DEFAULT_SIZE ? DEFAULT_SIZE : 'all')
                      }
                    }}
                  >
                    <span className="quiz-choice-label">{item.label}</span>
                    <span className="quiz-choice-meta">{counts[item.id]} в пуле</span>
                  </button>
                )
              })}
            </div>
          </section>

          <section className="quiz-setup-block" aria-labelledby="quiz-size-label">
            <h2 id="quiz-size-label" className="quiz-setup-title">
              Сколько вопросов
            </h2>
            <div className="quiz-choice-grid quiz-choice-grid--sizes" role="radiogroup" aria-labelledby="quiz-size-label">
              {SIZE_PRESETS.map((size) => {
                const disabled = size > poolCount
                const selected = sizeChoice === size
                return (
                  <button
                    key={size}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    className={`quiz-choice${selected ? ' is-active' : ''}`}
                    disabled={disabled}
                    onClick={() => setSizeChoice(size)}
                  >
                    <span className="quiz-choice-label">{size}</span>
                  </button>
                )
              })}
              <button
                type="button"
                role="radio"
                aria-checked={sizeChoice === 'all'}
                className={`quiz-choice${sizeChoice === 'all' ? ' is-active' : ''}`}
                disabled={poolCount <= 0}
                onClick={() => setSizeChoice('all')}
              >
                <span className="quiz-choice-label">Все</span>
                <span className="quiz-choice-meta">{poolCount}</span>
              </button>
            </div>
          </section>

          <div className="quiz-setup-actions">
            <p className="quiz-progress" aria-live="polite">
              Будет задано {resolvedSize} из {poolCount}
            </p>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary quiz-start-btn"
              disabled={resolvedSize <= 0}
              onClick={() => startQuiz(track, sizeChoice)}
            >
              Начать
            </button>
          </div>
        </div>
      ) : phase === 'play' && current ? (
        <div className="quiz-play">
          <p className="quiz-progress" aria-live="polite">
            Вопрос {questionIndex + 1} из {questions.length}
          </p>
          <fieldset className="quiz-question">
            <legend className="quiz-question-prompt">
              <span className="quiz-question-index">{questionIndex + 1}</span>
              <span>{current.prompt}</span>
            </legend>
            <div
              className="quiz-options"
              role="radiogroup"
              aria-label={`Вопрос ${questionIndex + 1}`}
            >
              {current.options.map((option, optionIndex) => {
                const selected = answers[current.id] === optionIndex
                const inputId = `${current.id}-${optionIndex}`
                return (
                  <label
                    key={inputId}
                    className={`quiz-option${selected ? ' is-selected' : ''}`}
                    htmlFor={inputId}
                  >
                    <input
                      id={inputId}
                      className="quiz-option-input"
                      type="radio"
                      name={current.id}
                      checked={selected}
                      onChange={() =>
                        setAnswers((prev) => ({ ...prev, [current.id]: optionIndex }))
                      }
                    />
                    <span className="quiz-option-letter" aria-hidden="true">
                      {OPTION_LETTERS[optionIndex] || String(optionIndex + 1)}
                    </span>
                    <span className="quiz-option-text">{option}</span>
                  </label>
                )
              })}
            </div>
          </fieldset>

          <div className="quiz-actions quiz-actions--sticky">
            <button
              type="button"
              className="learn-admin-btn"
              disabled={questionIndex <= 0}
              onClick={() => setQuestionIndex((value) => Math.max(0, value - 1))}
            >
              Назад
            </button>
            {isLastQuestion ? (
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={!hasCurrentAnswer}
                onClick={() => void onSubmit()}
              >
                Проверить
              </button>
            ) : (
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={!hasCurrentAnswer}
                onClick={() =>
                  setQuestionIndex((value) => Math.min(questions.length - 1, value + 1))
                }
              >
                Далее
              </button>
            )}
          </div>
        </div>
      ) : phase === 'review' ? (
        <div className="quiz-review">
          <p className="learn-admin-ok quiz-review-score">
            Результат: {score}/{questions.length}
          </p>
          {saveNote ? <p className="learn-section-note">{saveNote}</p> : null}
          {score === questions.length && questions.length >= INTERVIEW_CERT_MIN_TOTAL ? (
            <p className="quiz-cert-note">
              {getSiteAuthSession()?.accessToken ? (
                <>
                  100% — можно открыть диплом в{' '}
                  <Link to="/game/cert">Сертификатах</Link>.
                </>
              ) : (
                <>
                  100% — <Link to="/login">войдите</Link>, чтобы сохранить попытку и открыть
                  диплом в <Link to="/game/cert">Сертификатах</Link>.
                </>
              )}
            </p>
          ) : score === questions.length && questions.length < INTERVIEW_CERT_MIN_TOTAL ? (
            <p className="learn-section-note">
              Для диплома нужна попытка на {INTERVIEW_CERT_MIN_TOTAL}+ вопросов с результатом
              100%. Сейчас {questions.length} — выберите больший набор и пройдите ещё раз.
            </p>
          ) : null}

          <ul className="quiz-review-list">
            {questions.map((question, index) => {
              const selected = answers[question.id]
              const isCorrect = selected === question.correctIndex
              return (
                <li
                  key={question.id}
                  className={`quiz-review-item${isCorrect ? ' is-correct' : ' is-wrong'}`}
                >
                  <div className="quiz-review-head">
                    <span className="quiz-question-index">{index + 1}</span>
                    <span
                      className={`quiz-review-badge${isCorrect ? ' is-correct' : ' is-wrong'}`}
                    >
                      {isCorrect ? 'Верно' : 'Ошибка'}
                    </span>
                  </div>
                  <p className="quiz-review-prompt">{question.prompt}</p>
                  {!isCorrect ? (
                    <div className="quiz-review-detail">
                      <p className="quiz-review-line">
                        <span className="quiz-review-label">Ваш ответ:</span>{' '}
                        {selected === undefined
                          ? '—'
                          : question.options[selected] ?? '—'}
                      </p>
                      <p className="quiz-review-line">
                        <span className="quiz-review-label">Верный ответ:</span>{' '}
                        {question.options[question.correctIndex]}
                      </p>
                      {question.answer !== question.options[question.correctIndex] ? (
                        <p className="quiz-explain">{question.answer}</p>
                      ) : null}
                      <p className="quiz-question-link">
                        <Link to={`/game/learn/${question.episodeSlug}`}>
                          {question.episodeCode ? `${question.episodeCode} · ` : ''}
                          {question.episodeTitle} →
                        </Link>
                      </p>
                    </div>
                  ) : null}
                </li>
              )
            })}
          </ul>

          <div className="quiz-actions">
            <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={replaySame}>
              Ещё раз
            </button>
            <button type="button" className="learn-admin-btn" onClick={goSetup}>
              Изменить
            </button>
          </div>
        </div>
      ) : (
        <p className="learn-section-note">В этой теме пока нет вопросов с ответом в статье.</p>
      )}
    </PageShell>
  )
}
