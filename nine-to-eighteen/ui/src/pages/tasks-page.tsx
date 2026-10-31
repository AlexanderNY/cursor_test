import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { PersonalTasksPanel } from '@/components/personal-tasks-panel'
import { QueueLearnButton } from '@/components/tasks/queue-learn-button'
import { TaskComposer } from '@/components/tasks/task-composer'
import { TodayPanel } from '@/components/tasks/today-panel'
import {
  episodeTaskDraft,
  learnSlugQueued,
  learnTaskKey,
  openLearnKeys,
  planEpisodes,
  postHasLab,
  postHasQuiz,
  wordingTaskDraft,
} from '@/components/tasks/learn-link'
import { passedQuizSlugSet, syncLearnTasks } from '@/components/tasks/learn-sync'
import { isoDate } from '@/components/tasks/task-utils'
import { LEARN_LEVELS, LEARN_PROFILES } from '@/data/learn'
import type { LearnLevelId, LearnProfileId } from '@/data/learn/labels'
import type { LearnPost } from '@/data/learn/learn-store'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import { dueCountBySlug } from '@/data/learning-map/map-progress'
import {
  siteCreateUserTask,
  siteGetStudySummary,
  siteListAnkiCards,
  siteListUserTasks,
  type SiteQuizAttemptSummary,
  type SiteUserTask,
} from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'
import {
  progressPercent,
  useSiteLearnProgress,
} from '@/data/site/use-learn-progress'

type SortMode = 'course' | 'completed_at'
type OpenFilter = 'all' | 'open' | 'done'
type TasksTab = 'today' | 'personal' | 'learn'

function quizBestBySlug(
  best: SiteQuizAttemptSummary[] | undefined,
): Map<string, SiteQuizAttemptSummary> {
  const map = new Map<string, SiteQuizAttemptSummary>()
  for (const row of best || []) {
    const key = (row.sourceKey || '').trim()
    if (!key.toLowerCase().startsWith('learn/')) {
      continue
    }
    const slug = key.slice('learn/'.length).toLowerCase()
    if (!slug) {
      continue
    }
    map.set(slug, row)
  }
  return map
}

function matchesSearch(post: LearnPost, query: string): boolean {
  if (!query) {
    return true
  }
  const hay = [
    post.episode,
    post.title,
    post.shortTitle,
    ...(post.tags || []),
  ]
    .join(' ')
    .toLowerCase()
  return hay.includes(query)
}

function formatCompletedAt(iso: string | undefined): string {
  if (!iso) {
    return ''
  }
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleDateString('ru-RU')
}

export function TasksPage() {
  const session = getSiteAuthSession()
  const accessToken = session?.accessToken || ''
  const { posts, isReady } = useLearnPosts()
  const {
    items: progressItems,
    completedSlugs,
    isAuthed,
    setCompleted,
    isReady: progressReady,
  } = useSiteLearnProgress()
  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)

  const [activeTab, setActiveTab] = useState<TasksTab>('today')
  const [focusTaskId, setFocusTaskId] = useState<number | null>(null)
  const [queuedKeys, setQueuedKeys] = useState<Set<string>>(() => new Set())
  const [busyKey, setBusyKey] = useState('')
  const [queueError, setQueueError] = useState('')
  const [queueTick, setQueueTick] = useState(0)
  const [planNote, setPlanNote] = useState('')
  const [focusRequest, setFocusRequest] = useState<{ id: number; token: number } | null>(
    null,
  )
  const [seasonFilter, setSeasonFilter] = useState('')
  const [profileFilter, setProfileFilter] = useState<LearnProfileId | ''>('')
  const [levelFilter, setLevelFilter] = useState<LearnLevelId | ''>('')
  const [openFilter, setOpenFilter] = useState<OpenFilter>('all')
  const [search, setSearch] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('course')
  const [dueBySlug, setDueBySlug] = useState<Map<string, number>>(() => new Map())
  const [quizBest, setQuizBest] = useState<Map<string, SiteQuizAttemptSummary>>(
    () => new Map(),
  )
  const [evidenceReady, setEvidenceReady] = useState(false)

  const rememberQueued = useCallback((items: SiteUserTask[]) => {
    setQueuedKeys(openLearnKeys(items))
  }, [])

  const completedAtBySlug = useMemo(() => {
    const map = new Map<string, string>()
    for (const item of progressItems) {
      map.set(item.slug, item.completedAt)
    }
    return map
  }, [progressItems])

  useEffect(() => {
    if (!accessToken) {
      return
    }
    let cancelled = false
    void siteListUserTasks()
      .then((items) => {
        if (!cancelled) {
          rememberQueued(items)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setQueuedKeys(new Set())
        }
      })
    return () => {
      cancelled = true
    }
  }, [accessToken, queueTick, rememberQueued])

  async function queueEpisode(post: LearnPost) {
    const key = learnTaskKey(post.slug, 'article')
    if (!key || learnSlugQueued(queuedKeys, post.slug) || busyKey) {
      return
    }
    setBusyKey(key)
    setQueueError('')
    try {
      await siteCreateUserTask(episodeTaskDraft(post, { board: 'inbox', dueAt: null }))
      setQueuedKeys((prev) => {
        const next = new Set(prev)
        next.add(key)
        return next
      })
      setQueueTick((value) => value + 1)
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : 'Не удалось добавить задачу')
    } finally {
      setBusyKey('')
    }
  }

  async function planToday(minutes: number) {
    if (busyKey) {
      return
    }
    setBusyKey('plan')
    setQueueError('')
    setPlanNote('')
    try {
      const openSlugs = new Set(
        [...queuedKeys].map((key) => key.split('#')[0]).filter(Boolean),
      )
      const pool = published.filter((post) => !completedSlugs.has(post.slug))
      const picked = planEpisodes(pool, openSlugs, minutes)
      if (picked.length === 0) {
        setPlanNote('Незакрытых выпусков для плана нет.')
        return
      }
      for (const post of picked) {
        await siteCreateUserTask(
          episodeTaskDraft(post, { board: 'today', dueAt: isoDate(new Date()) }),
        )
      }
      const spent = picked.reduce(
        (sum, post) => sum + (post.durationMin > 0 ? post.durationMin : 15),
        0,
      )
      setPlanNote(`На сегодня: ${picked.map((post) => post.episode).join(', ')} · ${spent} мин`)
      setQueuedKeys((prev) => {
        const next = new Set(prev)
        for (const post of picked) {
          const key = learnTaskKey(post.slug, 'article')
          if (key) {
            next.add(key)
          }
        }
        return next
      })
      setQueueTick((value) => value + 1)
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : 'Не удалось собрать план')
    } finally {
      setBusyKey('')
    }
  }

  async function addWording(title: string) {
    const next = title.trim()
    if (!next || busyKey) {
      return
    }
    setBusyKey('wording')
    setQueueError('')
    try {
      await siteCreateUserTask(wordingTaskDraft(next, isoDate(new Date())))
      setQueueTick((value) => value + 1)
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : 'Не удалось добавить задачу')
    } finally {
      setBusyKey('')
    }
  }

  const completedKey = useMemo(
    () => progressItems.map((item) => item.slug).sort().join('\n'),
    [progressItems],
  )

  useEffect(() => {
    if (!isAuthed) {
      setDueBySlug(new Map())
      setQuizBest(new Map())
      setEvidenceReady(true)
      return
    }
    let cancelled = false
    setEvidenceReady(false)
    void Promise.all([siteListAnkiCards(), siteGetStudySummary()])
      .then(([cards, summary]) => {
        if (cancelled) {
          return
        }
        setDueBySlug(dueCountBySlug(cards))
        setQuizBest(quizBestBySlug(summary.quiz.best || summary.quiz.recent))
      })
      .catch(() => {
        if (!cancelled) {
          setDueBySlug(new Map())
          setQuizBest(new Map())
        }
      })
      .finally(() => {
        if (!cancelled) {
          setEvidenceReady(true)
        }
      })
    return () => {
      cancelled = true
    }
  }, [isAuthed])

  useEffect(() => {
    if (!accessToken || !progressReady || !evidenceReady) {
      return
    }
    let cancelled = false
    const passed = passedQuizSlugSet([...quizBest.values()])
    const done = new Set(
      completedKey
        ? completedKey
            .split('\n')
            .map((slug) => slug.toLowerCase())
            .filter(Boolean)
        : [],
    )
    void syncLearnTasks({ completedSlugs: done, passedQuizSlugs: passed })
      .then((count) => {
        if (!cancelled && count > 0) {
          setQueueTick((value) => value + 1)
        }
      })
      .catch(() => {
        /* The list still works if a step sync fails. */
      })
    return () => {
      cancelled = true
    }
  }, [accessToken, progressReady, evidenceReady, completedKey, quizBest])

  const searchQuery = search.trim().toLowerCase()

  const filteredSeasons = useMemo(() => {
    return seasons
      .filter((track) => !seasonFilter || track.id === seasonFilter)
      .map((track) => {
        let episodes = track.episodes.filter((ep) => {
          if (profileFilter && !(ep.profiles || []).includes(profileFilter)) {
            return false
          }
          if (levelFilter && ep.level !== levelFilter) {
            return false
          }
          if (openFilter === 'open' && completedSlugs.has(ep.slug)) {
            return false
          }
          if (openFilter === 'done' && !completedSlugs.has(ep.slug)) {
            return false
          }
          if (!matchesSearch(ep, searchQuery)) {
            return false
          }
          return true
        })
        if (sortMode === 'completed_at') {
          episodes = [...episodes].sort((a, b) => {
            const aAt = completedAtBySlug.get(a.slug) || ''
            const bAt = completedAtBySlug.get(b.slug) || ''
            if (aAt === bAt) {
              return a.order - b.order
            }
            if (!aAt) {
              return 1
            }
            if (!bAt) {
              return -1
            }
            return bAt.localeCompare(aAt)
          })
        }
        return { ...track, episodes }
      })
      .filter((track) => track.episodes.length > 0)
  }, [
    seasons,
    seasonFilter,
    profileFilter,
    levelFilter,
    openFilter,
    searchQuery,
    sortMode,
    completedSlugs,
    completedAtBySlug,
  ])

  const doneCount = published.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, published.length)
  const continuePost =
    seasons.flatMap((track) => track.episodes).find((p) => !completedSlugs.has(p.slug)) ||
    published[0]

  if (!session) {
    return (
      <PageShell>
        <p className="learn-section-note">
          <Link to="/login">Войдите</Link>, чтобы вести задачи и чек-лист Learn.
        </p>
      </PageShell>
    )
  }

  const listReady = isReady && progressReady && evidenceReady

  return (
    <PageShell>
      <Link to="/account" className="back-link">
        ← Кабинет
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Tasks</p>
        <h1 className="learn-title">Задачи</h1>
        <p className="learn-lead">
          Новые дела попадают в «Разобрать». Выпуск — одна задача со шагами.
          План по минутам собирает сегодня. Списки и календарь — в «Мои задачи».
        </p>
      </header>

      <TaskComposer
        posts={published}
        postsReady={isReady}
        queuedKeys={queuedKeys}
        busyKey={busyKey}
        error={queueError}
        planNote={planNote}
        onAddWording={addWording}
        onAddEpisode={queueEpisode}
        onPlan={planToday}
      />

      <div className="tasks-tabs" role="tablist" aria-label="Разделы задач">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'today'}
          className={activeTab === 'today' ? 'tasks-tab is-active' : 'tasks-tab'}
          onClick={() => setActiveTab('today')}
        >
          Сегодня
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'personal'}
          className={
            activeTab === 'personal' ? 'tasks-tab is-active' : 'tasks-tab'
          }
          onClick={() => setActiveTab('personal')}
        >
          Мои задачи
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'learn'}
          className={activeTab === 'learn' ? 'tasks-tab is-active' : 'tasks-tab'}
          onClick={() => setActiveTab('learn')}
        >
          Learn
        </button>
      </div>

      {activeTab === 'today' ? (
        <TodayPanel
          queuedSlugs={queuedKeys}
          busySlug={busyKey}
          queueError=""
          queueTick={queueTick}
          onQueue={(post) => void queueEpisode(post)}
          onTasksLoaded={rememberQueued}
          onOpenTask={(taskId) => {
            setFocusTaskId(taskId)
            setActiveTab('personal')
          }}
          onStartFocus={(taskId) => {
            setFocusRequest({ id: taskId, token: Date.now() })
            setActiveTab('personal')
          }}
        />
      ) : null}

      {activeTab === 'personal' ? (
        <PersonalTasksPanel
          focusTaskId={focusTaskId}
          reloadToken={queueTick}
          startFocusId={focusRequest?.id ?? null}
          startFocusToken={focusRequest?.token ?? 0}
        />
      ) : null}

      {activeTab === 'learn' && listReady ? (
        <p className="learn-section-note">
          Прогресс Learn: {doneCount}/{published.length} ({pct}%)
          {continuePost && !completedSlugs.has(continuePost.slug) ? (
            <>
              {' · '}
              <Link
                to={`/game/learn/${continuePost.slug}`}
                className="learn-admin-btn learn-admin-btn-primary tasks-continue-btn"
              >
                Продолжить: {continuePost.episode} ·{' '}
                {continuePost.shortTitle || continuePost.title}
              </Link>
            </>
          ) : published.length > 0 ? (
            <>
              {' · '}
              <Link to="/game/cert">Все выпуски отмечены · сертификаты</Link>
            </>
          ) : null}
        </p>
      ) : null}

      {activeTab === 'learn' && !listReady ? (
        <p className="learn-section-note">Загрузка Learn…</p>
      ) : null}

      {activeTab === 'learn' && listReady ? (
        <>
          <div className="learn-filters" aria-label="Фильтры чек-листа">
            <label className="learn-filter-field">
              <span>Сезон</span>
              <select
                value={seasonFilter}
                onChange={(event) => setSeasonFilter(event.target.value)}
              >
                <option value="">Все</option>
                {seasons.map((track) => (
                  <option key={track.id} value={track.id}>
                    {track.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="learn-filter-field">
              <span>Трек</span>
              <select
                value={profileFilter}
                onChange={(event) =>
                  setProfileFilter(event.target.value as LearnProfileId | '')
                }
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
                onChange={(event) =>
                  setLevelFilter(event.target.value as LearnLevelId | '')
                }
              >
                <option value="">Все</option>
                {LEARN_LEVELS.map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="learn-filter-field">
              <span>Статус</span>
              <select
                value={openFilter}
                onChange={(event) =>
                  setOpenFilter(event.target.value as OpenFilter)
                }
              >
                <option value="all">Все</option>
                <option value="open">Только открытые</option>
                <option value="done">Только пройденные</option>
              </select>
            </label>
            <label className="learn-filter-field">
              <span>Сортировка</span>
              <select
                value={sortMode}
                onChange={(event) => setSortMode(event.target.value as SortMode)}
              >
                <option value="course">По порядку курса</option>
                <option value="completed_at">По дате отметки</option>
              </select>
            </label>
            <label className="learn-filter-field tasks-search-field">
              <span>Поиск</span>
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Название, код, тег…"
              />
            </label>
          </div>

          {filteredSeasons.length === 0 ? (
            <p className="learn-section-note">
              {published.length === 0
                ? 'Пока нет опубликованных выпусков.'
                : 'Нет выпусков по выбранным фильтрам.'}
            </p>
          ) : (
            filteredSeasons.map((track) => {
              const trackDone = track.episodes.filter((ep) =>
                completedSlugs.has(ep.slug),
              ).length
              const fullTrack =
                seasons.find((item) => item.id === track.id)?.episodes ||
                track.episodes
              const fullDone = fullTrack.filter((ep) =>
                completedSlugs.has(ep.slug),
              ).length
              const trackPct = progressPercent(fullDone, fullTrack.length)
              const isTrackComplete =
                fullTrack.length > 0 && fullDone === fullTrack.length

              return (
                <section key={track.id} className="learn-schedule tasks-track">
                  <div className="tasks-track-head">
                    <div>
                      <h2 className="learn-section-title">{track.title}</h2>
                      <p className="learn-section-note">
                        {fullDone}/{fullTrack.length} ({trackPct}%)
                        {isTrackComplete ? (
                          <>
                            {' · '}
                            <Link to="/game/cert">Сертификат</Link>
                          </>
                        ) : null}
                        {trackDone !== fullDone ? (
                          <> · в фильтре: {trackDone}</>
                        ) : null}
                      </p>
                    </div>
                    <div
                      className="tasks-progress"
                      role="progressbar"
                      aria-valuenow={trackPct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Прогресс ${track.title}`}
                    >
                      <span
                        className="tasks-progress-fill"
                        style={{ width: `${trackPct}%` }}
                      />
                    </div>
                  </div>
                  <ul className="learn-admin-list">
                    {track.episodes.map((ep) => {
                      const done = completedSlugs.has(ep.slug)
                      const hasLab = postHasLab(ep)
                      const hasQuiz = postHasQuiz(ep)
                      const dueCount = dueBySlug.get(ep.slug) || 0
                      const quiz = quizBest.get(ep.slug)
                      const completedLabel = formatCompletedAt(
                        completedAtBySlug.get(ep.slug),
                      )
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
                            <div className="tasks-row-meta">
                              {ep.durationMin > 0 ? (
                                <span className="learn-badge">{ep.durationMin} мин</span>
                              ) : null}
                              {hasLab ? (
                                <span className="learn-badge">Лаба</span>
                              ) : null}
                              {hasQuiz ? (
                                <span className="learn-badge">Квиз</span>
                              ) : null}
                              {dueCount > 0 ? (
                                <span className="learn-badge tasks-badge-due">
                                  Anki due {dueCount}
                                </span>
                              ) : null}
                              {quiz ? (
                                <span className="learn-badge tasks-badge-quiz">
                                  Тест {quiz.score}/{quiz.total}
                                  {typeof quiz.percent === 'number'
                                    ? ` (${quiz.percent}%)`
                                    : ''}
                                </span>
                              ) : hasQuiz ? (
                                <span className="learn-badge">Тест не сдан</span>
                              ) : null}
                              {done && completedLabel ? (
                                <span className="learn-badge">
                                  Отмечено {completedLabel}
                                </span>
                              ) : null}
                            </div>
                          </div>
                          <div className="learn-admin-row-actions">
                            <QueueLearnButton
                              label="В разобрать"
                              queued={learnSlugQueued(queuedKeys, ep.slug)}
                              busy={busyKey === learnTaskKey(ep.slug, 'article')}
                              onQueue={() => void queueEpisode(ep)}
                            />
                            <Link
                              to={`/game/learn/${ep.slug}`}
                              className="learn-admin-link"
                            >
                              Открыть
                            </Link>
                          </div>
                        </li>
                      )
                    })}
                  </ul>
                </section>
              )
            })
          )}
        </>
      ) : null}
    </PageShell>
  )
}
