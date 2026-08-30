import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import { getSiteAuthSession } from '@/data/site/site-auth'
import {
  progressPercent,
  useSiteLearnProgress,
} from '@/data/site/use-learn-progress'

export function TasksPage() {
  const session = getSiteAuthSession()
  const { posts, isReady } = useLearnPosts()
  const { completedSlugs, isAuthed, setCompleted, isReady: progressReady } =
    useSiteLearnProgress()
  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)
  const doneCount = published.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, published.length)

  if (!session) {
    return (
      <PageShell>
        <p className="learn-section-note">
          <Link to="/login">Войдите</Link>, чтобы вести чек-лист Learn.
        </p>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to="/account" className="back-link">
        ← Кабинет
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Tasks</p>
        <h1 className="learn-title">Чек-лист Learn</h1>
        <p className="learn-lead">
          Отмечайте пройденные выпуски. Прогресс:{' '}
          {isReady && progressReady ? `${doneCount}/${published.length} (${pct}%)` : '…'}
        </p>
      </header>

      {!isReady || !progressReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        seasons.map((track) => (
          <section key={track.id} className="learn-schedule">
            <h2 className="learn-section-title">{track.title}</h2>
            <ul className="learn-admin-list">
              {track.episodes.map((ep) => {
                const done = completedSlugs.has(ep.slug)
                return (
                  <li key={ep.slug} className="learn-admin-row">
                    <div className="learn-admin-row-main">
                      <label className="learn-admin-field" style={{ margin: 0 }}>
                        <span>
                          <input
                            type="checkbox"
                            checked={done}
                            disabled={!isAuthed}
                            onChange={() => void setCompleted(ep.slug, !done)}
                          />{' '}
                          {ep.episode} · {ep.shortTitle || ep.title}
                        </span>
                      </label>
                    </div>
                    <Link to={`/game/learn/${ep.slug}`} className="learn-admin-link">
                      Открыть
                    </Link>
                  </li>
                )
              })}
            </ul>
          </section>
        ))
      )}
    </PageShell>
  )
}
