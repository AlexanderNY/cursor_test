import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CertDiplomaCard } from '@/components/cert-diploma-card'
import { PageShell } from '@/components/page-shell'
import { downloadCertPdf, downloadCertPng } from '@/data/site/cert-png'
import {
  INTERVIEW_CERT_MIN_TOTAL,
  INTERVIEW_CERT_PERCENT,
  INTERVIEW_CERT_TRACK_ID,
  certHolderName,
  certPublicPath,
  certTopicLines,
  formatCertDateLong,
  formatCourseDuration,
  printCertificate,
  sumDurationMinutes,
  toneOf,
  type CertTopicLine,
} from '@/data/site/cert-shared'
import { getSeasonTracks, useLearnPosts } from '@/data/learn/use-learn-posts'
import { getSiteAuthSession } from '@/data/site/site-auth'
import {
  siteGetProfile,
  siteListCertificates,
  type SiteCertTrack,
} from '@/data/site/site-api'
import { useSiteLearnProgress } from '@/data/site/use-learn-progress'

function quizLabel(track: SiteCertTrack | undefined, threshold: number): string {
  if (!track || track.quizRequired === 0) {
    return 'квиз в треке не задан'
  }
  if (track.id === INTERVIEW_CERT_TRACK_ID) {
    return `квиз ${track.quizPercent}% при пороге ${threshold}% · от ${INTERVIEW_CERT_MIN_TOTAL} вопросов`
  }
  return `квиз ${track.quizPassed}/${track.quizRequired} от ${threshold}%`
}

type PreviewItem = {
  trackId: string
  holderName: string
  courseTitle: string
  earned: boolean
  issuedLabel: string
  durationLabel: string
  resultLabel: string
  resultValue: string
  percent: number
  quizLabel: string
  code: string
  serialNumber: string
  topics: CertTopicLine[]
  fileStem: string
}

export function CertPage() {
  const session = getSiteAuthSession()
  const { posts, isReady } = useLearnPosts()
  const { completedSlugs, isReady: progressReady } = useSiteLearnProgress()
  const [tracks, setTracks] = useState<SiteCertTrack[]>([])
  const [threshold, setThreshold] = useState(70)
  const [certsReady, setCertsReady] = useState(false)
  const [certError, setCertError] = useState('')
  const [copiedCode, setCopiedCode] = useState('')
  const [preview, setPreview] = useState<PreviewItem | null>(null)
  const [pdfBusy, setPdfBusy] = useState(false)
  const [holderName, setHolderName] = useState(session?.username || '')
  const [hasLegalName, setHasLegalName] = useState<boolean | null>(null)
  const seasons = getSeasonTracks(posts)

  const accessToken = session?.accessToken || ''
  const username = session?.username || ''

  useEffect(() => {
    if (!accessToken) {
      return
    }
    let cancelled = false
    void siteListCertificates()
      .then((board) => {
        if (cancelled) return
        setTracks(board.tracks)
        setThreshold(board.quizThreshold || 70)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setCertError(err instanceof Error ? err.message : 'Не удалось выдать бланки')
      })
      .finally(() => {
        if (!cancelled) setCertsReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [accessToken])

  useEffect(() => {
    if (!accessToken) {
      return
    }
    let cancelled = false
    void siteGetProfile()
      .then((profile) => {
        if (cancelled) return
        const first = profile.firstName || ''
        const last = profile.lastName || ''
        setHasLegalName(Boolean(first.trim() && last.trim()))
        setHolderName(certHolderName(first, last, profile.patronymic || '', username))
      })
      .catch(() => {
        if (cancelled) return
        setHasLegalName(false)
        setHolderName(certHolderName('', '', '', username))
      })
    return () => {
      cancelled = true
    }
  }, [accessToken, username])

  useEffect(() => {
    if (!preview) {
      return
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setPreview(null)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [preview])

  if (!session) {
    return (
      <PageShell>
        <p className="learn-section-note">
          <Link to="/login">Войдите</Link>, чтобы увидеть сертификаты.
        </p>
      </PageShell>
    )
  }

  const byId = new Map(tracks.map((track) => [track.id, track]))
  const seasonBoard = seasons.map((track) => {
    const api = byId.get(track.id)
    const done = api?.done ?? track.episodes.filter((episode) => completedSlugs.has(episode.slug)).length
    const total = api?.total ?? track.episodes.length
    const earned = Boolean(api?.earned)
    const percent = total === 0 ? 0 : Math.round((done / total) * 100)
    const nextEpisode = track.episodes.find((episode) => !completedSlugs.has(episode.slug))
    const quizSlug = api?.quizMissing[0]
    return {
      track: {
        id: track.id,
        title: track.title,
        note: track.note,
        episodes: track.episodes,
      },
      api,
      done,
      total,
      earned,
      percent,
      quizThreshold: threshold,
      continueTo: nextEpisode
        ? { href: `/game/learn/${nextEpisode.slug}`, label: 'Продолжить трек' }
        : !earned && quizSlug
          ? { href: `/game/learn/${quizSlug}`, label: 'Сдать квиз' }
          : null,
    }
  })
  const interviewApi = byId.get(INTERVIEW_CERT_TRACK_ID)
  const interviewBoard = interviewApi
    ? [
        {
          track: {
            id: INTERVIEW_CERT_TRACK_ID,
            title: interviewApi.title || 'Quiz · Собеседование',
            note: `Диплом за квиз собеседования: лучшая попытка ${INTERVIEW_CERT_PERCENT}% при минимум ${INTERVIEW_CERT_MIN_TOTAL} вопросах.`,
            episodes: [] as { slug: string; episode: string; title: string; durationMin?: number }[],
          },
          api: interviewApi,
          done: interviewApi.done,
          total: interviewApi.total,
          earned: Boolean(interviewApi.earned),
          percent: interviewApi.quizPercent,
          quizThreshold: INTERVIEW_CERT_PERCENT,
          continueTo: interviewApi.earned
            ? null
            : { href: '/game/quiz', label: 'Пройти квиз' },
        },
      ]
    : []
  const board = [...interviewBoard, ...seasonBoard].sort(
    (left, right) =>
      Number(right.earned) - Number(left.earned) || right.percent - left.percent,
  )
  const earnedCount = board.filter((item) => item.earned).length

  async function copyLink(code: string) {
    try {
      const url = `${window.location.origin}${certPublicPath(code)}`
      await navigator.clipboard.writeText(url)
      setCopiedCode(code)
    } catch {
      setCertError('Не удалось скопировать ссылку')
    }
  }

  function blankOf(item: (typeof board)[number]) {
    const courseTitle = item.api?.title || item.track.title
    const hasEpisodes = item.track.episodes.length > 0
    const issuedLabel = item.api?.issuedAt ? formatCertDateLong(item.api.issuedAt) : ''
    return {
      courseTitle,
      issuedLabel,
      durationLabel: formatCourseDuration(
        sumDurationMinutes(item.track.episodes.map((episode) => ({ durationMin: episode.durationMin }))),
      ),
      resultLabel: hasEpisodes ? 'Темы' : 'Квиз',
      resultValue: hasEpisodes ? `${item.done} из ${item.total}` : `${item.percent}%`,
      topics: certTopicLines(item.track.episodes, completedSlugs),
      quizLabel: quizLabel(item.api, item.quizThreshold),
      code: item.api?.code || '',
      serialNumber: item.api?.serialNumber || '',
    }
  }

  function openPreview(item: (typeof board)[number]) {
    const blank = blankOf(item)
    setPreview({
      trackId: item.track.id,
      holderName,
      earned: item.earned,
      percent: item.percent,
      fileStem: blank.code || item.track.id,
      ...blank,
    })
  }

  async function savePreviewPdf() {
    if (!preview || pdfBusy) {
      return
    }
    setPdfBusy(true)
    try {
      await downloadCertPdf({
        code: preview.code,
        holderName: preview.holderName,
        series: preview.courseTitle,
        trackName: preview.courseTitle,
        courseTitle: preview.courseTitle,
        issuedLabel: preview.issuedLabel,
        episodeCount: preview.topics.length,
        percent: preview.percent,
        earned: preview.earned,
        quizLabel: preview.quizLabel,
        durationLabel: preview.durationLabel,
        resultLabel: preview.resultLabel,
        resultValue: preview.resultValue,
        topics: preview.topics,
        serialNumber: preview.serialNumber,
        tone: toneOf(preview.trackId),
        fileStem: preview.fileStem,
      })
    } catch {
      setCertError('Не удалось скачать PDF')
    } finally {
      setPdfBusy(false)
    }
  }

  return (
    <PageShell>
      <Link to="/account" className="back-link no-print">
        ← Кабинет
      </Link>
      <header className="learn-header no-print">
        <p className="learn-eyebrow">Cert</p>
        <h1 className="learn-title">Сертификаты</h1>
        <p className="learn-lead">
          Бланк формата А4: имя и фамилия, курс и дата прохождения. Сезонный диплом — когда отмечены
          все выпуски трека и лучшая попытка каждого квиза не ниже {threshold}%. Квиз{' '}
          <Link to="/game/quiz">Собеседование</Link> открывает диплом при {INTERVIEW_CERT_PERCENT}% и
          минимум {INTERVIEW_CERT_MIN_TOTAL} вопросах.
        </p>
        {hasLegalName === false ? (
          <p className="learn-section-note">
            На бланке сейчас логин. Укажите имя и фамилию в <Link to="/account">кабинете</Link>, чтобы
            сертификат был выдан на человека.
          </p>
        ) : null}
      </header>

      {certError ? <p className="learn-admin-error no-print">{certError}</p> : null}

      {!isReady || !progressReady || !certsReady ? (
        <p className="learn-section-note no-print">Загрузка…</p>
      ) : board.length === 0 ? (
        <p className="learn-section-note no-print">Опубликованных треков пока нет.</p>
      ) : (
        <>
          <div className="cert-stats no-print">
            <article className="cert-stat" style={{ ['--cert-a' as string]: '#5eead4' }}>
              <strong>{earnedCount}</strong>
              <span>сдано сезонов</span>
            </article>
            <article className="cert-stat" style={{ ['--cert-a' as string]: '#fbbf24' }}>
              <strong>{board.length - earnedCount}</strong>
              <span>ещё в пути</span>
            </article>
            <article className="cert-stat" style={{ ['--cert-a' as string]: '#c4b5fd' }}>
              <strong>{tracks.reduce((sum, track) => sum + track.done, 0)}</strong>
              <span>выпусков в треках</span>
            </article>
          </div>

          <div className="cert-board">
            {board.map((item) => {
              const blank = blankOf(item)
              const isInterview = item.track.id === INTERVIEW_CERT_TRACK_ID
              return (
                <CertDiplomaCard
                  key={item.track.id}
                  trackId={item.track.id}
                  holderName={holderName}
                  courseTitle={blank.courseTitle}
                  earned={item.earned}
                  issuedLabel={blank.issuedLabel}
                  durationLabel={blank.durationLabel}
                  resultLabel={blank.resultLabel}
                  resultValue={blank.resultValue}
                  quizLabel={blank.quizLabel}
                  code={blank.code}
                  serialNumber={blank.serialNumber}
                  topics={blank.topics}
                  actions={
                    <>
                      <button
                        type="button"
                        className="learn-admin-btn learn-admin-btn-primary"
                        onClick={() => openPreview(item)}
                      >
                        Предпросмотр
                      </button>
                      {item.earned && item.api?.code ? (
                        <>
                          <button
                            type="button"
                            className="learn-admin-btn"
                            onClick={() => printCertificate(item.track.id)}
                          >
                            Печать
                          </button>
                          <button
                            type="button"
                            className="learn-admin-btn"
                            onClick={() =>
                              downloadCertPng({
                                code: blank.code,
                                holderName,
                                series: blank.courseTitle,
                                trackName: blank.courseTitle,
                                courseTitle: blank.courseTitle,
                                issuedLabel: blank.issuedLabel,
                                episodeCount: item.total,
                                done: item.done,
                                percent: item.percent,
                                earned: true,
                                quizLabel: blank.quizLabel,
                                durationLabel: blank.durationLabel,
                                resultLabel: blank.resultLabel,
                                resultValue: blank.resultValue,
                                topics: blank.topics,
                                serialNumber: blank.serialNumber,
                                tone: toneOf(item.track.id),
                              })
                            }
                          >
                            Скачать PNG
                          </button>
                          <button
                            type="button"
                            className="learn-admin-btn"
                            onClick={() => void copyLink(item.api?.code || '')}
                          >
                            {copiedCode === item.api.code ? 'Ссылка скопирована' : 'Ссылка на проверку'}
                          </button>
                        </>
                      ) : item.continueTo ? (
                        <Link to={item.continueTo.href} className="learn-admin-btn">
                          {item.continueTo.label}
                        </Link>
                      ) : null}
                      <Link
                        to={isInterview ? '/game/quiz' : '/game/tasks'}
                        className="learn-admin-btn"
                      >
                        {isInterview ? 'Quiz' : 'Tasks'}
                      </Link>
                    </>
                  }
                />
              )
            })}
          </div>
        </>
      )}

      {preview ? (
        <div
          className="cert-preview-overlay no-print"
          role="dialog"
          aria-modal="true"
          aria-label="Предпросмотр сертификата"
          onClick={() => setPreview(null)}
        >
          <div
            className="cert-preview-dialog"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="cert-preview-head">
              <h2>
                Предпросмотр · {preview.percent}%
                {preview.earned ? ' · ПРОЙДЕНО' : ''}
              </h2>
              <div className="cert-preview-actions">
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={pdfBusy}
                  onClick={() => void savePreviewPdf()}
                >
                  {pdfBusy ? 'Готовим PDF…' : 'Скачать PDF'}
                </button>
                <button
                  type="button"
                  className="learn-admin-btn"
                  onClick={() => setPreview(null)}
                >
                  Закрыть
                </button>
              </div>
            </div>
            <CertDiplomaCard
              trackId={preview.trackId}
              holderName={preview.holderName}
              courseTitle={preview.courseTitle}
              earned={preview.earned}
              issuedLabel={preview.issuedLabel}
              durationLabel={preview.durationLabel}
              resultLabel={preview.resultLabel}
              resultValue={preview.resultValue}
              quizLabel={preview.quizLabel}
              code={preview.code}
              serialNumber={preview.serialNumber}
              topics={preview.topics}
            />
          </div>
        </div>
      ) : null}
    </PageShell>
  )
}
