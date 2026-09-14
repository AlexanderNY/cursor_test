import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LearnPostBadges } from '@/components/learn-post-badges'
import { PageShell } from '@/components/page-shell'
import { getSortedRubrics, LEARN_LEVELS, LEARN_PROFILES } from '@/data/learn'
import type { LearnLevelId, LearnProfileId } from '@/data/learn/labels'
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
  const [profileFilter, setProfileFilter] = useState<LearnProfileId | ''>('')
  const [levelFilter, setLevelFilter] = useState<LearnLevelId | ''>('')

  const filtered = useMemo(() => {
    return published.filter((post) => {
      if (profileFilter && !(post.profiles || []).includes(profileFilter)) {
        return false
      }
      if (levelFilter && post.level !== levelFilter) {
        return false
      }
      return true
    })
  }, [published, profileFilter, levelFilter])

  const filteredSlugs = useMemo(() => new Set(filtered.map((p) => p.slug)), [filtered])
  const doneCount = filtered.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, filtered.length)
  const continuePost = filtered.find((p) => !completedSlugs.has(p.slug)) || filtered[0]

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
        {isAuthed && progressReady && filtered.length > 0 ? (
          <p className="learn-section-note">
            Прогресс: {doneCount}/{filtered.length} ({pct}%)
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

      <div className="learn-filters" aria-label="Фильтр по треку и уровню">
        <label className="learn-filter-field">
          <span>Трек</span>
          <select
            value={profileFilter}
            onChange={(event) => setProfileFilter(event.target.value as LearnProfileId | '')}
          >
            <option value="">Все</option>
            {LEARN_PROFILES.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.label}
              </option>
            ))}
          </select>
        </label>
        <label className="learn-filter-field">
          <span>Уровень</span>
          <select
            value={levelFilter}
            onChange={(event) => setLevelFilter(event.target.value as LearnLevelId | '')}
          >
            <option value="">Все</option>
            {LEARN_LEVELS.map((level) => (
              <option key={level.id} value={level.id}>
                {level.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : filtered.length === 0 ? (
        <p className="learn-section-note">
          {published.length === 0
            ? 'Пока нет опубликованных выпусков. Загляните позже.'
            : 'Нет выпусков по выбранным фильтрам.'}
        </p>
      ) : (
        <>
          {seasonTracks.map((track) => {
            const episodes = track.episodes.filter((episode) => filteredSlugs.has(episode.slug))
            if (episodes.length === 0) {
              return null
            }
            const trackDone = episodes.filter((e) => completedSlugs.has(e.slug)).length
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
                    {isAuthed ? ` · ${trackDone}/${episodes.length} пройдено` : ''}
                  </p>
                </div>
                <ol className="learn-season-list">
                  {episodes.map((episode) => (
                    <li key={episode.slug}>
                      <Link to={`/game/learn/${episode.slug}`} className="learn-season-link">
                        {episode.coverUrl?.trim() ? (
                          <img
                            className="learn-season-thumb"
                            src={episode.coverUrl.trim()}
                            alt=""
                          />
                        ) : null}
                        <span className="learn-episode-code">{episode.episode}</span>
                        <span className="learn-episode-name">
                          {completedSlugs.has(episode.slug) ? '✓ ' : ''}
                          {episode.shortTitle}
                          {episode.author?.trim() ? ` · ${episode.author.trim()}` : ''}
                        </span>
                      </Link>
                      <LearnPostBadges
                        profiles={episode.profiles}
                        level={episode.level}
                        tags={episode.tags}
                        durationMin={episode.durationMin}
                        className="learn-badges-compact"
                      />
                    </li>
                  ))}
                </ol>
              </section>
            )
          })}

          <div className="learn-rubrics">
            {rubrics.map((rubric) => {
              const episodes = getPostsByRubric(filtered, rubric.id)
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
                          {episode.coverUrl?.trim() ? (
                            <img
                              className="learn-card-thumb"
                              src={episode.coverUrl.trim()}
                              alt=""
                            />
                          ) : null}
                          <span className="learn-episode-code">{episode.episode}</span>
                          <span className="learn-episode-title">
                            {completedSlugs.has(episode.slug) ? '✓ ' : ''}
                            {episode.title}
                          </span>
                          {episode.author?.trim() ? (
                            <span className="learn-card-author">{episode.author.trim()}</span>
                          ) : null}
                        </Link>
                        <LearnPostBadges
                          profiles={episode.profiles}
                          level={episode.level}
                          tags={episode.tags}
                          durationMin={episode.durationMin}
                          className="learn-badges-compact"
                        />
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
