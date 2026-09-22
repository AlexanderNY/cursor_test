import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { hydrateLearnStructured } from '@/data/site/structured-post'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'
import type { LearnPost } from '@/data/learn/learn-store'
import { siteSubmitQuizAttempt } from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

type QuizQuestion = {
  id: string
  prompt: string
  options: string[]
  correctIndex: number
  episodeSlug: string
  explain: string
}

const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']
const QUIZ_SIZE = 10

function shuffleInPlace<T>(items: T[]): T[] {
  for (let index = items.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1))
    ;[items[index], items[swap]] = [items[swap], items[index]]
  }
  return items
}

function collectStructuredItems(posts: LearnPost[]): Array<{
  question: string
  answer: string
  explain: string
  episodeSlug: string
}> {
  const items: Array<{
    question: string
    answer: string
    explain: string
    episodeSlug: string
  }> = []
  for (const post of posts) {
    const structured = hydrateLearnStructured(post.structured, {
      lab: post.lab,
      cheatsheet: post.cheatsheet,
      cheatsheetFormat: post.cheatsheetFormat,
      diagram: post.diagram,
    })
    if (!structured) {
      continue
    }
    for (const row of structured.quiz) {
      const question = row.question.trim()
      const answer = row.answer.trim()
      if (!question || !answer) {
        continue
      }
      items.push({
        question,
        answer,
        explain: row.explain.trim(),
        episodeSlug: post.slug,
      })
    }
  }
  return items
}

function buildQuestions(posts: LearnPost[]): QuizQuestion[] {
  const pool = collectStructuredItems(posts)
  if (pool.length === 0) {
    return []
  }
  const answerPool = [...new Set(pool.map((item) => item.answer))]
  const picked = shuffleInPlace([...pool]).slice(0, Math.min(QUIZ_SIZE, pool.length))
  return picked.map((item, index) => {
    const distractors = shuffleInPlace(
      answerPool.filter((answer) => answer.toLowerCase() !== item.answer.toLowerCase()),
    ).slice(0, 3)
    while (distractors.length < 3 && answerPool.length > distractors.length + 1) {
      const fallback = answerPool.find(
        (answer) =>
          answer.toLowerCase() !== item.answer.toLowerCase() &&
          !distractors.includes(answer),
      )
      if (!fallback) {
        break
      }
      distractors.push(fallback)
    }
    const options = shuffleInPlace([item.answer, ...distractors].slice(0, 4))
    const correctIndex = options.findIndex(
      (option) => option.toLowerCase() === item.answer.toLowerCase(),
    )
    return {
      id: `${item.episodeSlug}-${index}`,
      prompt: item.question,
      options,
      correctIndex: correctIndex >= 0 ? correctIndex : 0,
      episodeSlug: item.episodeSlug,
      explain: item.explain,
    }
  })
}

function optionStateClass(
  submitted: boolean,
  selected: boolean,
  isCorrectOption: boolean,
): string {
  if (!submitted) {
    return selected ? ' is-selected' : ''
  }
  if (isCorrectOption) {
    return ' is-correct'
  }
  if (selected) {
    return ' is-wrong'
  }
  return ' is-muted'
}

export function QuizPage() {
  const { posts, isReady } = useLearnPosts()
  const published = getPublishedPosts(posts)
  const questions = useMemo(
    () => (isReady ? buildQuestions(published) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional one-shot quiz set
    [isReady, published.length],
  )
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [submitted, setSubmitted] = useState(false)
  const [saveNote, setSaveNote] = useState('')

  const answeredCount = questions.filter((q) => answers[q.id] !== undefined).length
  const score = questions.reduce((sum, q) => {
    return sum + (answers[q.id] === q.correctIndex ? 1 : 0)
  }, 0)

  async function onSubmit() {
    const nextScore = questions.reduce((sum, q) => {
      return sum + (answers[q.id] === q.correctIndex ? 1 : 0)
    }, 0)
    setSubmitted(true)
    setSaveNote('')
    if (!getSiteAuthSession()?.accessToken) {
      setSaveNote('Войдите в кабинет, чтобы сохранить результат.')
      return
    }
    try {
      await siteSubmitQuizAttempt({
        source_type: 'quiz_page',
        source_key: 'learn/quiz',
        score: nextScore,
        total: questions.length,
        answers: questions.map((q) => ({
          id: q.id,
          selected: answers[q.id],
          correct: q.correctIndex,
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
        <h1 className="learn-title">Закрепление</h1>
        <p className="learn-lead">
          Вопросы берутся из блоков «Тест» опубликованных статей Learn (
          <code>structured.quiz</code>), а не из названий выпусков.
        </p>
      </header>

      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : questions.length === 0 ? (
        <p className="learn-section-note">
          Нет вопросов в structured.quiz у опубликованных выпусков.
        </p>
      ) : (
        <form
          className="quiz-form"
          onSubmit={(e) => {
            e.preventDefault()
            void onSubmit()
          }}
        >
          {!submitted ? (
            <p className="quiz-progress" aria-live="polite">
              Отвечено {answeredCount} из {questions.length}
            </p>
          ) : null}

          {questions.map((q, qi) => (
            <fieldset key={q.id} className="quiz-question">
              <legend className="quiz-question-prompt">
                <span className="quiz-question-index">{qi + 1}</span>
                <span>{q.prompt}</span>
              </legend>
              <div className="quiz-options" role="radiogroup" aria-label={`Вопрос ${qi + 1}`}>
                {q.options.map((opt, oi) => {
                  const selected = answers[q.id] === oi
                  const isCorrectOption = oi === q.correctIndex
                  const stateClass = optionStateClass(submitted, selected, isCorrectOption)
                  const inputId = `${q.id}-${oi}`
                  return (
                    <label key={inputId} className={`quiz-option${stateClass}`} htmlFor={inputId}>
                      <input
                        id={inputId}
                        className="quiz-option-input"
                        type="radio"
                        name={q.id}
                        checked={selected}
                        disabled={submitted}
                        onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: oi }))}
                      />
                      <span className="quiz-option-letter" aria-hidden="true">
                        {OPTION_LETTERS[oi] || String(oi + 1)}
                      </span>
                      <span className="quiz-option-text">{opt}</span>
                    </label>
                  )
                })}
              </div>
              {submitted ? (
                <>
                  {q.explain ? <p className="quiz-explain">{q.explain}</p> : null}
                  <p className="quiz-question-link">
                    <Link to={`/game/learn/${q.episodeSlug}`}>Открыть выпуск →</Link>
                  </p>
                </>
              ) : null}
            </fieldset>
          ))}

          <div className="quiz-actions">
            {!submitted ? (
              <button
                type="submit"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={answeredCount < questions.length}
              >
                Проверить
              </button>
            ) : (
              <>
                <p className="learn-admin-ok">
                  Результат: {score}/{questions.length}
                </p>
                <button
                  type="button"
                  className="learn-admin-btn"
                  onClick={() => {
                    setAnswers({})
                    setSubmitted(false)
                    setSaveNote('')
                  }}
                >
                  Ещё раз
                </button>
              </>
            )}
          </div>
          {saveNote ? <p className="learn-section-note">{saveNote}</p> : null}
        </form>
      )}
    </PageShell>
  )
}
