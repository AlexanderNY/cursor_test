import { FormEvent, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LearnContent } from '@/components/learn-content'
import { MermaidBlock } from '@/components/learn-mermaid'
import {
  ensureAnkiFromQuiz,
  learnAnkiCards,
  type StructuredPost,
} from '@/data/site/structured-post'
import {
  siteReviewAnkiCard,
  siteSubmitQuizAttempt,
} from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

type StructuredPostViewProps = {
  post: StructuredPost
  appSlug: string
  postSlug: string
  /** Quiz attempt source_type; default `post` for blog, use `learn` for course. */
  sourceType?: 'post' | 'learn' | 'quiz_page'
}

export function StructuredPostView({
  post,
  appSlug,
  postSlug,
  sourceType = 'post',
}: StructuredPostViewProps) {
  const sourceKey = `${appSlug}/${postSlug}`
  const isLearn = sourceType === 'learn'
  const ankiCards = useMemo(
    () => (isLearn ? learnAnkiCards(post) : ensureAnkiFromQuiz(post)),
    [post, isLearn],
  )
  const theorySections = post.sections.filter((section) => {
    if (!(section.heading.trim() || section.body.trim())) {
      return false
    }
    /* Cheatsheet lives on its own tab for Learn; skip duplicate section from seed. */
    if (isLearn && /^шпаргалка$/i.test(section.heading.trim())) {
      return false
    }
    return true
  })
  const quizItems = post.quiz.filter((q) => q.question.trim() && q.answer.trim())
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [revealed, setRevealed] = useState(false)
  const [quizMessage, setQuizMessage] = useState('')
  const [ankiIndex, setAnkiIndex] = useState(0)
  const [ankiFlipped, setAnkiFlipped] = useState(false)
  const [ankiMessage, setAnkiMessage] = useState('')
  const isAuthed = Boolean(getSiteAuthSession()?.accessToken)

  function computeScore(currentAnswers: Record<number, string>): number {
    return quizItems.reduce((sum, item, index) => {
      const given = (currentAnswers[index] || '').trim().toLowerCase()
      const expected = item.answer.trim().toLowerCase()
      const isMatch =
        Boolean(given) &&
        (given === expected || expected.includes(given) || given.includes(expected))
      return sum + (isMatch ? 1 : 0)
    }, 0)
  }

  const score = useMemo(
    () => (revealed ? computeScore(answers) : 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- quizItems stable per post
    [answers, quizItems, revealed],
  )

  async function submitQuiz(event: FormEvent) {
    event.preventDefault()
    const nextScore = computeScore(answers)
    setRevealed(true)
    setQuizMessage('')
    if (!isAuthed) {
      setQuizMessage('Войдите в кабинет, чтобы сохранить результат теста.')
      return
    }
    try {
      await siteSubmitQuizAttempt({
        source_type: sourceType,
        source_key: sourceKey,
        score: nextScore,
        total: quizItems.length,
        answers: quizItems.map((item, index) => ({
          question: item.question,
          given: answers[index] || '',
          expected: item.answer,
        })),
      })
      setQuizMessage('Результат сохранён в личном кабинете.')
    } catch (err) {
      setQuizMessage(err instanceof Error ? err.message : 'Не удалось сохранить результат')
    }
  }

  async function rateAnki(ease: 1 | 2 | 3 | 4) {
    const card = ankiCards[ankiIndex]
    if (!card) {
      return
    }
    setAnkiMessage('')
    if (isAuthed) {
      try {
        await siteReviewAnkiCard({
          card_id: `post:${sourceKey}:${ankiIndex}:${card.front.slice(0, 40)}`,
          front: card.front,
          back: card.back,
          source_key: sourceKey,
          ease,
        })
        setAnkiMessage('Карточка учтена в прогрессе.')
      } catch (err) {
        setAnkiMessage(err instanceof Error ? err.message : 'Не удалось сохранить карточку')
      }
    } else {
      setAnkiMessage('Войдите, чтобы прогресс anki сохранялся.')
    }
    setAnkiFlipped(false)
    setAnkiIndex((prev) => Math.min(prev + 1, Math.max(ankiCards.length - 1, 0)))
  }

  const activeAnki = ankiCards[ankiIndex]

  return (
    <article className="structured-post">
      <section className="structured-block" aria-labelledby="sp-intro">
        <h2 id="sp-intro" className="learn-section-title">
          Введение
        </h2>
        <LearnContent content={post.intro} format="markdown" />
      </section>

      {theorySections.map((section, index) => (
          <section
            key={`section-${index}`}
            className="structured-block"
            aria-labelledby={`sp-section-${index}`}
          >
            <h2 id={`sp-section-${index}`} className="learn-section-title">
              {section.heading.trim() || `Раздел ${index + 1}`}
            </h2>
            <LearnContent content={section.body} format="markdown" />
          </section>
        ))}

      {post.diagrams.filter((d) => d.mermaid.trim()).length > 0 ? (
        <section className="structured-block" aria-labelledby="sp-diagrams">
          <h2 id="sp-diagrams" className="learn-section-title">
            Схемы
          </h2>
          {post.diagrams
            .filter((d) => d.mermaid.trim())
            .map((diagram, index) => (
              <figure key={`diagram-${index}`} className="structured-diagram">
                {diagram.caption ? (
                  <figcaption className="learn-section-note">{diagram.caption}</figcaption>
                ) : null}
                <MermaidBlock chart={diagram.mermaid} />
              </figure>
            ))}
        </section>
      ) : null}

      {quizItems.length > 0 ? (
        <section className="structured-block" aria-labelledby="sp-quiz">
          <h2 id="sp-quiz" className="learn-section-title">
            Тест
          </h2>
          <form className="learn-admin-form" onSubmit={(e) => void submitQuiz(e)}>
            {quizItems.map((item, index) => (
              <fieldset key={`quiz-${index}`} className="structured-quiz-item">
                <legend className="learn-panel-heading">
                  {index + 1}. {item.question}
                </legend>
                <label className="learn-admin-field">
                  <span>Ваш ответ</span>
                  <input
                    value={answers[index] || ''}
                    onChange={(e) =>
                      setAnswers((prev) => ({ ...prev, [index]: e.target.value }))
                    }
                    disabled={revealed}
                  />
                </label>
                {revealed ? (
                  <div className="structured-quiz-reveal">
                    <p className="learn-section-note">
                      Ответ: <strong>{item.answer}</strong>
                    </p>
                    {item.explain ? (
                      <LearnContent content={item.explain} format="markdown" />
                    ) : null}
                  </div>
                ) : null}
              </fieldset>
            ))}
            {!revealed ? (
              <button type="submit" className="learn-admin-btn learn-admin-btn-primary">
                Проверить
              </button>
            ) : (
              <p className="learn-admin-ok">
                Результат: {score}/{quizItems.length}
                {!isAuthed ? (
                  <>
                    {' '}
                    · <Link to="/login">войти</Link>, чтобы сохранить
                  </>
                ) : null}
              </p>
            )}
            {quizMessage ? <p className="learn-section-note">{quizMessage}</p> : null}
          </form>
        </section>
      ) : null}

      {post.summary.filter(Boolean).length > 0 || ankiCards.length > 0 ? (
        <section className="structured-block" aria-labelledby="sp-summary">
          <h2 id="sp-summary" className="learn-section-title">
            {isLearn ? 'Anki' : 'Итог для anki'}
          </h2>
          {post.summary.filter(Boolean).length > 0 ? (
            <ul className="account-feature-list">
              {post.summary.filter(Boolean).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}

          {activeAnki ? (
            <div className="structured-anki">
              <p className="learn-section-note">
                Карточка {ankiIndex + 1} / {ankiCards.length}
              </p>
              <button
                type="button"
                className={`structured-anki-card${ankiFlipped ? ' is-flipped' : ''}`}
                onClick={() => setAnkiFlipped((prev) => !prev)}
              >
                <span className="structured-anki-label">{ankiFlipped ? 'Ответ' : 'Вопрос'}</span>
                <span>{ankiFlipped ? activeAnki.back : activeAnki.front}</span>
              </button>
              {ankiFlipped ? (
                <div className="structured-anki-rates">
                  <button type="button" className="learn-admin-btn" onClick={() => void rateAnki(1)}>
                    Снова
                  </button>
                  <button type="button" className="learn-admin-btn" onClick={() => void rateAnki(2)}>
                    Сложно
                  </button>
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    onClick={() => void rateAnki(3)}
                  >
                    Хорошо
                  </button>
                  <button type="button" className="learn-admin-btn" onClick={() => void rateAnki(4)}>
                    Легко
                  </button>
                </div>
              ) : (
                <p className="learn-section-note">Нажмите карточку, чтобы увидеть ответ.</p>
              )}
              {ankiMessage ? <p className="learn-section-note">{ankiMessage}</p> : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {post.appendix?.trim() ? (
        <section className="structured-block" aria-labelledby="sp-appendix">
          <h2 id="sp-appendix" className="learn-section-title">
            Дополнительно
          </h2>
          <LearnContent content={post.appendix} format="markdown" />
        </section>
      ) : null}
    </article>
  )
}
