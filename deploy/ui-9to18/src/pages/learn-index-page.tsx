import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { getSortedRubrics } from '@/data/learn'
import {
  getPostsByRubric,
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import {
  progressPercent,
  useSiteLearnProgress,
} from '@/data/site/use-learn-progress'

export function LearnIndexPage() {
  const rubrics = getSortedRubrics()
  const { posts, isReady } = useLearnPosts()
  const published = getPublishedPosts(posts)
  const seasonTracks = getSeasonTracks(posts)
  const { completedSlugs, isAuthed, isReady: progressReady } = useSiteLearnProgress()
  const doneCount = published.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, published.length)
  const continuePost = published.find((p) => !completedSlugs.has(p.slug)) || published[0]

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← К разделам
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Learn · учебный блог</p>
        <h1 className="learn-title">Learn</h1>
        <p className="learn-lead">
          Сезон B — быстрый старт первого приложения (Git, Python, React, Docker). Сезон 1 —
          углубление со сквозным сервисом заявок. Выпуски перелинкованы между собой.
        </p>
        {isAuthed && progressReady && published.length > 0 ? (
          <p className="learn-section-note">
            Прогресс: {doneCount}/{published.length} ({pct}%)
            {continuePost ? (
              <>
                {' · '}
                <Link to={`/game/learn/${continuePost.slug}`}>Продолжить →</Link>
              </>
            ) : null}
            {' · '}
            <Link to="/game/tasks">Чек-лист</Link>
          </p>
        ) : (
          <p className="learn-section-note">
            <Link to="/login">Войдите</Link>, чтобы сохранять прогресс по выпускам.
          </p>
        )}
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
          {seasonTracks.map((track) => {
            const trackDone = track.episodes.filter((e) => completedSlugs.has(e.slug)).length
            return (
              <section
                key={track.id}
                className="learn-season"
                aria-labelledby={`learn-season-${track.id}`}
              >
                <div className="learn-season-head">
                  <h2 id={`learn-season-${track.id}`} className="learn-section-title">
                    {track.title}
                  </h2>
                  <p className="learn-section-note">
                    {track.note}
                    {isAuthed
                      ? ` · ${trackDone}/${track.episodes.length} пройдено`
                      : ''}
                  </p>
                </div>
                <ol className="learn-season-list">
                  {track.episodes.map((episode) => (
                    <li key={episode.slug}>
                      <Link to={`/game/learn/${episode.slug}`} className="learn-season-link">
                        <span className="learn-episode-code">{episode.episode}</span>
                        <span className="learn-episode-name">
                          {completedSlugs.has(episode.slug) ? '✓ ' : ''}
                          {episode.shortTitle}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ol>
              </section>
            )
          })}

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
                          <span className="learn-episode-title">
                            {completedSlugs.has(episode.slug) ? '✓ ' : ''}
                            {episode.title}
                          </span>
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
