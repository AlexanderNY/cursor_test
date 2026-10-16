import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CertDiplomaCard } from '@/components/cert-diploma-card'
import { PageShell } from '@/components/page-shell'
import { getSeasonTracks, useLearnPosts } from '@/data/learn/use-learn-posts'
import { downloadCertPdf, downloadCertPng } from '@/data/site/cert-png'
import {
  INTERVIEW_CERT_PERCENT,
  INTERVIEW_CERT_TRACK_ID,
  formatCertDate,
  printCertificate,
  splitTrackTitle,
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
  const { series, name } = splitTrackTitle(cert?.trackTitle || '')
  const issued = cert ? formatCertDate(cert.issuedAt) : ''
  const quiz =
    cert && cert.quizRequired > 0
      ? `квиз ${cert.quizPercent}% при пороге ${cert.quizThreshold}%`
      : 'квиз в треке не задан'
  const certCopy = cert
    ? isInterview
      ? `Подтверждается прохождение квиза «Собеседование» на ${INTERVIEW_CERT_PERCENT}% (${issued}).`
      : `Подтверждается прохождение трека «${cert.trackTitle}» (${cert.episodeCount} вып.) на ${issued}.`
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
        series,
        trackName: name,
        issuedLabel: issued,
        episodeCount: cert.episodeCount,
        done: cert.episodeCount,
        percent: 100,
        earned: true,
        quizLabel: quiz,
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
        <h1 className="learn-title">{cert ? cert.code : 'Сертификат'}</h1>
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
          series={series}
          headline={cert.holderName}
          subline={name}
          copy={certCopy}
          earned
          done={cert.episodeCount}
          total={cert.episodeCount}
          percent={100}
          quizLabel={quiz}
          code={cert.code}
          episodes={
            isInterview
              ? []
              : (season?.episodes || []).map((episode) => ({
                  key: episode.slug,
                  label: episode.episode,
                  title: episode.title,
                  done: true,
                }))
          }
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
                    series,
                    trackName: name,
                    issuedLabel: issued,
                    episodeCount: cert.episodeCount,
                    done: cert.episodeCount,
                    percent: 100,
                    earned: true,
                    quizLabel: quiz,
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
