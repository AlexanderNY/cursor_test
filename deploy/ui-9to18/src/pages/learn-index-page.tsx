import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { getSortedRubrics } from '@/data/learn'
import {
  getPostsByRubric,
  getPublishedPosts,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'

export function LearnIndexPage() {
  const rubrics = getSortedRubrics()
  const { posts, isReady } = useLearnPosts()
  const published = getPublishedPosts(posts)
  const seasonTrack = published

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← К разделам
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Сезон 1 · учебный блог</p>
        <h1 className="learn-title">Learn</h1>
        <p className="learn-lead">
          Теория, лабораторные и шпаргалки. Сквозной учебный сервис — заявки (tickets). CopyParse —
          референс взрослого стенда, не форк.
        </p>
        <p className="learn-admin-entry">
          <Link to="/game/learn/admin" className="learn-admin-link">
            Админка
          </Link>
        </p>
      </header>

      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : published.length === 0 ? (
        <p className="learn-section-note">Пока нет опубликованных выпусков. Загляните позже.</p>
      ) : (
        <>
          <section className="learn-season" aria-labelledby="learn-season-heading">
            <div className="learn-season-head">
              <h2 id="learn-season-heading" className="learn-section-title">
                Идти по сезону
              </h2>
              <p className="learn-section-note">Линейный порядок выпусков</p>
            </div>
            <ol className="learn-season-list">
              {seasonTrack.map((episode) => (
                <li key={episode.slug}>
                  <Link to={`/game/learn/${episode.slug}`} className="learn-season-link">
                    <span className="learn-episode-code">{episode.episode}</span>
                    <span className="learn-episode-name">{episode.shortTitle}</span>
                  </Link>
                </li>
              ))}
            </ol>
          </section>

          <div className="learn-rubrics">
            {rubrics.map((rubric) => {
              const episodes = getPostsByRubric(published, rubric.id)
              if (episodes.length === 0) {
                return null
              }
              return (
                <section
                  key={rubric.id}
                  className="learn-rubric"
                  aria-labelledby={`rubric-${rubric.id}`}
                >
                  <header className="learn-rubric-header">
                    <h2 id={`rubric-${rubric.id}`} className="learn-section-title">
                      {rubric.title}
                    </h2>
                    <p className="learn-section-note">{rubric.subtitle}</p>
                  </header>
                  <ul className="learn-episode-list">
                    {episodes.map((episode) => (
                      <li key={episode.slug}>
                        <Link to={`/game/learn/${episode.slug}`} className="learn-episode-card">
                          <span className="learn-episode-code">{episode.episode}</span>
                          <span className="learn-episode-title">{episode.title}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              )
            })}
          </div>
        </>
      )}
    </PageShell>
  )
}
