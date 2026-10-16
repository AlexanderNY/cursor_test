import type { CSSProperties, ReactNode } from 'react'
import { toneOf } from '@/data/site/cert-shared'

type CertEpisodePill = {
  key: string
  label: string
  title: string
  done: boolean
}

type CertDiplomaCardProps = {
  trackId: string
  series: string
  headline: string
  subline: string
  copy: string
  earned: boolean
  done: number
  total: number
  percent: number
  quizLabel: string
  code: string
  episodes: CertEpisodePill[]
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

export function CertDiplomaCard({
  trackId,
  series,
  headline,
  subline,
  copy,
  earned,
  done,
  total,
  percent,
  quizLabel,
  code,
  episodes,
  actions,
}: CertDiplomaCardProps) {
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

        <div className="cert-banner">
          <span>9to18 · Learn</span>
          <span>{percent}%</span>
        </div>

        <div className="cert-diploma-body">
          <p className="cert-series">{series}</p>
          <h2 className="cert-name">{headline}</h2>
          <p className={earned ? 'cert-track-name' : 'cert-statement'}>{subline}</p>
          <p className="cert-copy">{copy}</p>

          <div
            className="cert-bar"
            role="progressbar"
            aria-valuenow={done}
            aria-valuemin={0}
            aria-valuemax={Math.max(total, 1)}
            aria-label={`${headline}: ${done} из ${total}`}
          >
            <span style={{ width: `${percent}%` }} />
          </div>
          <p className="cert-progress-label">
            {done}/{total} выпусков · {percent}%
            {quizLabel ? ` · ${quizLabel}` : ''}
            {code ? ` · бланк ${code}` : ''}
          </p>

          {episodes.length > 0 ? (
            <ul className="cert-pills">
              {episodes.map((episode) => (
                <li
                  key={episode.key}
                  className={`cert-pill${episode.done ? ' is-done' : ''}`}
                  title={episode.title}
                >
                  {episode.label}
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="cert-seal" aria-hidden>
          <div className="cert-seal-ring">
            <strong>9–18</strong>
            <span>{earned ? 'сдан' : 'путь'}</span>
          </div>
        </div>

        {earned ? (
          <div className="cert-passed-stamp" aria-hidden>
            ПРОЙДЕНО
          </div>
        ) : null}

        {actions ? <div className="cert-actions no-print">{actions}</div> : null}
      </div>
    </article>
  )
}
