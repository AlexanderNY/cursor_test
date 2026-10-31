import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CertDiplomaCard } from '@/components/cert-diploma-card'
import { PageShell } from '@/components/page-shell'
import { getSeasonTracks, useLearnPosts } from '@/data/learn/use-learn-posts'
import { downloadCertPdf, downloadCertPng } from '@/data/site/cert-png'
import {
  INTERVIEW_CERT_PERCENT,
  INTERVIEW_CERT_TRACK_ID,
  certTopicLines,
  formatCertDateLong,
  formatCourseDuration,
  printCertificate,
  sumDurationMinutes,
  toneOf,
} from '@/data/site/cert-shared'
import { SiteApiError, siteGetPublicCertificate, type SitePublicCert } from '@/data/site/site-api'

export function CertPublicPage() {
  const { code = '' } = useParams<{ code: string }>()
  const { posts } = useLearnPosts()
  const [cert, setCert] = useState<SitePublicCert | null>(null)
  const [missing, setMissing] = useState(false)
  const [error, setError] = useState('')
  const [pdfBusy, setPdfBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    setCert(null)
    setMissing(false)
    setError('')
    void siteGetPublicCertificate(code)
      .then((data) => {
        if (!cancelled) setCert(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof SiteApiError && err.status === 404) {
          setMissing(true)
          return
        }
        setError(err instanceof Error ? err.message : 'Не удалось проверить бланк')
      })
    return () => {
      cancelled = true
    }
  }, [code])

  const isInterview = cert?.trackId === INTERVIEW_CERT_TRACK_ID
  const season = getSeasonTracks(posts).find((track) => track.id === cert?.trackId)
  const courseTitle = cert?.trackTitle || ''
  const issued = cert ? formatCertDateLong(cert.issuedAt) : ''
  const episodes = isInterview ? [] : season?.episodes || []
  const topics = certTopicLines(episodes, null)
  const durationLabel = formatCourseDuration(sumDurationMinutes(episodes))
  const quiz =
    cert && cert.quizRequired > 0
      ? isInterview
        ? `квиз «Собеседование» ${INTERVIEW_CERT_PERCENT}%`
        : `квиз ${cert.quizPercent}% при пороге ${cert.quizThreshold}%`
      : ''
  const resultLabel = isInterview ? 'Квиз' : 'Темы'
  const resultValue = isInterview
    ? cert
      ? `${cert.quizPercent}%`
      : ''
    : episodes.length > 0
      ? `${episodes.length} из ${episodes.length}`
      : cert
        ? `${cert.episodeCount} из ${cert.episodeCount}`
        : ''

  async function savePdf() {
    if (!cert || pdfBusy) {
      return
    }
    setPdfBusy(true)
    try {
      await downloadCertPdf({
        code: cert.code,
        holderName: cert.holderName,
        series: courseTitle,
        trackName: courseTitle,
        courseTitle,
        issuedLabel: issued,
        episodeCount: cert.episodeCount,
        done: cert.episodeCount,
        percent: 100,
        earned: true,
        quizLabel: quiz,
        durationLabel,
        resultLabel,
        resultValue,
        topics,
        serialNumber: cert.serialNumber || '',
        tone: toneOf(cert.trackId),
      })
    } catch {
      setError('Не удалось скачать PDF')
    } finally {
      setPdfBusy(false)
    }
  }

  return (
    <PageShell>
      <Link to="/" className="back-link no-print">
        ← На главную
      </Link>
      <header className="learn-header no-print">
        <p className="learn-eyebrow">Проверка бланка</p>
        <h1 className="learn-title">{cert ? cert.serialNumber || cert.code : 'Сертификат'}</h1>
      </header>
      {error ? <p className="learn-admin-error">{error}</p> : null}
      {missing ? (
        <p className="learn-section-note">
          Бланк не найден или сезон больше не закрыт. Номер мог устареть после снятия отметки с
          выпуска.
        </p>
      ) : null}
      {!cert && !missing && !error ? <p className="learn-section-note">Проверяем бланк…</p> : null}
      {cert ? (
        <CertDiplomaCard
          trackId={cert.trackId}
          holderName={cert.holderName}
          courseTitle={courseTitle}
          earned
          issuedLabel={issued}
          durationLabel={durationLabel}
          resultLabel={resultLabel}
          resultValue={resultValue}
          quizLabel={quiz}
          code={cert.code}
          serialNumber={cert.serialNumber || ''}
          topics={topics}
          actions={
            <>
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={pdfBusy}
                onClick={() => void savePdf()}
              >
                {pdfBusy ? 'Готовим PDF…' : 'Скачать PDF'}
              </button>
              <button
                type="button"
                className="learn-admin-btn"
                onClick={() => printCertificate(cert.trackId)}
              >
                Печать
              </button>
              <button
                type="button"
                className="learn-admin-btn"
                onClick={() =>
                  downloadCertPng({
                    code: cert.code,
                    holderName: cert.holderName,
                    series: courseTitle,
                    trackName: courseTitle,
                    courseTitle,
                    issuedLabel: issued,
                    episodeCount: cert.episodeCount,
                    done: cert.episodeCount,
                    percent: 100,
                    earned: true,
                    quizLabel: quiz,
                    durationLabel,
                    resultLabel,
                    resultValue,
                    topics,
                    serialNumber: cert.serialNumber || '',
                    tone: toneOf(cert.trackId),
                  })
                }
              >
                Скачать PNG
              </button>
            </>
          }
        />
      ) : null}
    </PageShell>
  )
}
