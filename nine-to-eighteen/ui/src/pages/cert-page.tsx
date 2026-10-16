import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CertDiplomaCard } from '@/components/cert-diploma-card'
import { PageShell } from '@/components/page-shell'
import { downloadCertPdf, downloadCertPng } from '@/data/site/cert-png'
import {
  INTERVIEW_CERT_MIN_TOTAL,
  INTERVIEW_CERT_PERCENT,
  INTERVIEW_CERT_TRACK_ID,
  certPublicPath,
  formatCertDate,
  printCertificate,
  splitTrackTitle,
  toneOf,
} from '@/data/site/cert-shared'
import { getSeasonTracks, useLearnPosts } from '@/data/learn/use-learn-posts'
import { getSiteAuthSession } from '@/data/site/site-auth'
import {
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
  series: string
  name: string
  title: string
  headline: string
  subline: string
  copy: string
  earned: boolean
  done: number
  total: number
  percent: number
  quizLabel: string
  code: string
  issued: string
  episodes: { key: string; label: string; title: string; done: boolean }[]
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
  const seasons = getSeasonTracks(posts)

  const accessToken = session?.accessToken || ''

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

  const username = session.username
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
            episodes: [] as { slug: string; episode: string; title: string }[],
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

  function openPreview(item: (typeof board)[number], series: string, name: string, label: string, issued: string) {
    const isInterview = item.track.id === INTERVIEW_CERT_TRACK_ID
    setPreview({
      trackId: item.track.id,
      series,
      name,
      title: item.api?.title || item.track.title,
      headline: item.earned ? username : name,
      subline: item.earned ? name : `Бланк для ${username}`,
      copy: item.earned
        ? isInterview
          ? `Подтверждается прохождение квиза «Собеседование» на ${INTERVIEW_CERT_PERCENT}% (${issued}).`
          : `Подтверждается прохождение трека «${item.api?.title || item.track.title}» (${item.total} вып.) на ${issued}.`
        : item.track.note,
      earned: item.earned,
      done: item.done,
      total: item.total,
      percent: item.percent,
      quizLabel: label,
      code: item.api?.code || '',
      issued,
      episodes: item.track.episodes.map((episode) => ({
        key: episode.slug,
        label: episode.episode,
        title: episode.title,
        done: completedSlugs.has(episode.slug),
      })),
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
        holderName: preview.earned ? username : preview.headline,
        series: preview.series,
        trackName: preview.name,
        issuedLabel: preview.issued,
        episodeCount: preview.total,
        done: preview.done,
        percent: preview.percent,
        earned: preview.earned,
        quizLabel: preview.quizLabel,
        tone: toneOf(preview.trackId),
        fileStem: preview.code || preview.trackId,
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
          Сезонный диплом — когда отмечены все выпуски трека и лучшая попытка каждого квиза не
          ниже {threshold}%. Отдельно: квиз{' '}
          <Link to="/game/quiz">Собеседование</Link> открывает диплом при {INTERVIEW_CERT_PERCENT}%
          и минимум {INTERVIEW_CERT_MIN_TOTAL} вопросах. После сдачи — штамп «ПРОЙДЕНО».
        </p>
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
              const { series, name } = splitTrackTitle(item.api?.title || item.track.title)
              const issued = item.api?.issuedAt ? formatCertDate(item.api.issuedAt) : ''
              const label = quizLabel(item.api, item.quizThreshold)
              const isInterview = item.track.id === INTERVIEW_CERT_TRACK_ID
              return (
                <CertDiplomaCard
                  key={item.track.id}
                  trackId={item.track.id}
                  series={series}
                  headline={item.earned ? username : name}
                  subline={item.earned ? name : `Бланк для ${username}`}
                  copy={
                    item.earned
                      ? isInterview
                        ? `Подтверждается прохождение квиза «Собеседование» на ${INTERVIEW_CERT_PERCENT}% (${issued}).`
                        : `Подтверждается прохождение трека «${item.api?.title || item.track.title}» (${item.total} вып.) на ${issued}.`
                      : item.track.note
                  }
                  earned={item.earned}
                  done={item.done}
                  total={item.total}
                  percent={item.percent}
                  quizLabel={label}
                  code={item.api?.code || ''}
                  episodes={item.track.episodes.map((episode) => ({
                    key: episode.slug,
                    label: episode.episode,
                    title: episode.title,
                    done: completedSlugs.has(episode.slug),
                  }))}
                  actions={
                    <>
                      <button
                        type="button"
                        className="learn-admin-btn learn-admin-btn-primary"
                        onClick={() => openPreview(item, series, name, label, issued)}
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
                                code: item.api?.code || '',
                                holderName: username,
                                series,
                                trackName: name,
                                issuedLabel: issued,
                                episodeCount: item.total,
                                done: item.done,
                                percent: item.percent,
                                earned: true,
                                quizLabel: label,
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
              series={preview.series}
              headline={preview.headline}
              subline={preview.subline}
              copy={preview.copy}
              earned={preview.earned}
              done={preview.done}
              total={preview.total}
              percent={preview.percent}
              quizLabel={preview.quizLabel}
              code={preview.code}
              episodes={preview.episodes}
            />
          </div>
        </div>
      ) : null}
    </PageShell>
  )
}
