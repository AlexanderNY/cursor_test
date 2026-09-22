import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import { getSiteAuthSession } from '@/data/site/site-auth'
import { useSiteLearnProgress } from '@/data/site/use-learn-progress'

export function CertPage() {
  const session = getSiteAuthSession()
  const { posts, isReady } = useLearnPosts()
  const { completedSlugs, isReady: progressReady } = useSiteLearnProgress()
  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)

  if (!session) {
    return (
      <PageShell>
        <p className="learn-section-note">
          <Link to="/login">Войдите</Link>, чтобы увидеть сертификаты.
        </p>
      </PageShell>
    )
  }

  const earned = seasons.filter(
    (track) =>
      track.episodes.length > 0 &&
      track.episodes.every((ep) => completedSlugs.has(ep.slug)),
  )
  const dateLabel = new Date().toLocaleDateString('ru-RU')

  function printCertificate(trackId: string) {
    const cards = document.querySelectorAll<HTMLElement>('.cert-card')
    cards.forEach((card) => {
      if (card.getAttribute('data-cert-id') === trackId) {
        card.classList.add('is-print-target')
      } else {
        card.classList.add('no-print')
      }
    })
    window.print()
    cards.forEach((card) => {
      card.classList.remove('is-print-target', 'no-print')
    })
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
          Сертификат сезона выдаётся, когда отмечены все опубликованные выпуски трека.
          Печать / «Сохранить как PDF» — через диалог печати браузера.
        </p>
      </header>

      {!isReady || !progressReady ? (
        <p className="learn-section-note no-print">Загрузка…</p>
      ) : earned.length === 0 ? (
        <section className="info-section no-print">
          <p className="learn-section-note">
            Пока нет завершённых сезонов. Отмечайте выпуски в{' '}
            <Link to="/game/tasks">Tasks</Link> или на страницах Learn.
          </p>
          <ul className="contacts-list">
            {seasons.map((track) => {
              const done = track.episodes.filter((e) => completedSlugs.has(e.slug)).length
              return (
                <li key={track.id}>
                  {track.title}: {done}/{track.episodes.length}
                </li>
              )
            })}
          </ul>
        </section>
      ) : (
        earned.map((track) => (
          <section
            key={track.id}
            className="info-section cert-card"
            data-cert-id={track.id}
          >
            <p className="learn-eyebrow">9to18 · Learn</p>
            <h2 className="learn-title" style={{ fontSize: '1.75rem' }}>
              Сертификат: {track.title}
            </h2>
            <p className="learn-lead">
              Настоящим подтверждается, что <strong>{session.username}</strong> прошёл(а) все
              выпуски трека ({track.episodes.length} шт.) на {dateLabel}.
            </p>
            <p className="learn-section-note">
              Всего на платформе отмечено{' '}
              {published.filter((p) => completedSlugs.has(p.slug)).length} выпусков.
            </p>
            <div className="cert-actions no-print">
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                onClick={() => printCertificate(track.id)}
              >
                Печать / PDF
              </button>
            </div>
          </section>
        ))
      )}
    </PageShell>
  )
}
