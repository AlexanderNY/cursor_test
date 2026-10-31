import type { CSSProperties, ReactNode } from 'react'
import { toneOf, type CertTopicLine } from '@/data/site/cert-shared'

type CertDiplomaCardProps = {
  trackId: string
  holderName: string
  courseTitle: string
  earned: boolean
  issuedLabel: string
  durationLabel: string
  resultLabel: string
  resultValue: string
  code: string
  topics: CertTopicLine[]
  quizLabel?: string
  actions?: ReactNode
}

function toneStyle(trackId: string): CSSProperties {
  const tone = toneOf(trackId)
  return {
    '--cert-a': tone.a,
    '--cert-b': tone.b,
    '--cert-c': tone.c,
  } as CSSProperties
}

function topicClass(count: number): string {
  if (count > 40) {
    return 'cert-topics is-packed'
  }
  if (count > 12) {
    return 'cert-topics is-dense'
  }
  return 'cert-topics'
}

export function CertDiplomaCard({
  trackId,
  holderName,
  courseTitle,
  earned,
  issuedLabel,
  durationLabel,
  resultLabel,
  resultValue,
  code,
  topics,
  quizLabel = '',
  actions,
}: CertDiplomaCardProps) {
  const dateLine =
    earned && issuedLabel
      ? `Дата прохождения: ${issuedLabel}`
      : 'Дата выдачи появится после завершения курса'

  return (
    <article
      className={`cert-diploma${earned ? ' is-earned' : ''}`}
      data-cert-id={trackId}
      style={toneStyle(trackId)}
    >
      <div className="cert-diploma-sheet">
        <span className="cert-corner cert-corner-tl" aria-hidden />
        <span className="cert-corner cert-corner-tr" aria-hidden />
        <span className="cert-corner cert-corner-bl" aria-hidden />
        <span className="cert-corner cert-corner-br" aria-hidden />

        <header className="cert-a4-head">
          <p className="cert-kicker">Сертификат</p>
          <p className="cert-org">9to18 · Learn</p>
        </header>
        <div className="cert-rule" aria-hidden />

        <p className="cert-lead">{earned ? 'Настоящим подтверждается, что' : 'Бланк курса для'}</p>
        <h2 className="cert-holder">{holderName}</h2>
        <p className="cert-verb">{earned ? 'прошёл(а) курс' : 'проходит курс'}</p>
        <p className="cert-course">{courseTitle}</p>
        <p className="cert-issued">{dateLine}</p>

        <dl className="cert-facts">
          {durationLabel ? (
            <div>
              <dt>Примерное время курса</dt>
              <dd>{durationLabel}</dd>
            </div>
          ) : null}
          <div>
            <dt>{resultLabel}</dt>
            <dd>{resultValue}</dd>
          </div>
          {code ? (
            <div>
              <dt>Номер бланка</dt>
              <dd>{code}</dd>
            </div>
          ) : null}
        </dl>

        <section className="cert-topics-block">
          <h3>Пройденные темы</h3>
          {topics.length > 0 ? (
            <ol className={topicClass(topics.length)}>
              {topics.map((topic) => (
                <li key={topic.key} className="cert-topic">
                  <span className="cert-topic-code">{topic.code}</span>
                  <span className="cert-topic-title">{topic.title}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="cert-topics-empty">{quizLabel || 'Пройденных тем пока нет.'}</p>
          )}
          {quizLabel && topics.length > 0 ? <p className="cert-quiz-note">{quizLabel}</p> : null}
        </section>

        <footer className="cert-a4-foot">
          <div className="cert-a4-sign">
            {earned ? (
              <p className="cert-passed-stamp" aria-hidden>
                ПРОЙДЕНО
              </p>
            ) : (
              <p className="cert-sign-note">Бланк откроется после прохождения курса</p>
            )}
            <p className="cert-sign">9to18.ru</p>
          </div>
          <div className="cert-seal" aria-hidden>
            <div className="cert-seal-ring">
              <strong>9–18</strong>
              <span>{earned ? 'сдан' : 'путь'}</span>
            </div>
          </div>
        </footer>
      </div>

      {actions ? <div className="cert-actions no-print">{actions}</div> : null}
    </article>
  )
}
