import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { QueueLearnButton } from '@/components/tasks/queue-learn-button'
import {
  learnEpisodePath,
  learnTargetFromNotes,
  learnSlugQueued,
  learnTaskKey,
} from '@/components/tasks/learn-link'
import {
  flattenTasks,
  formatDue,
  isDueToday,
  isOverdue,
  isoDate,
} from '@/components/tasks/task-utils'
import type { LearnPost } from '@/data/learn/learn-store'
import { dueCountBySlug } from '@/data/learning-map/map-progress'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import {
  siteListAnkiCards,
  siteListHabits,
  siteListUserTasks,
  siteSetHabitCheck,
  siteUpdateUserTask,
  type SiteAnkiCardState,
  type SiteUserHabit,
  type SiteUserTask,
} from '@/data/site/site-api'
import { useSiteLearnProgress } from '@/data/site/use-learn-progress'

const TASK_LIMIT = 8
const ANKI_LIMIT = 6

type AnkiGroup = {
  slug: string
  count: number
  title: string
}

type TodayPanelProps = {
  queuedSlugs: ReadonlySet<string>
  busySlug: string
  queueError: string
  queueTick: number
  onQueue: (post: LearnPost) => void
  onOpenTask: (taskId: number) => void
  onStartFocus: (taskId: number) => void
  onTasksLoaded: (items: SiteUserTask[]) => void
}

function ankiGroups(cards: SiteAnkiCardState[], posts: LearnPost[]): AnkiGroup[] {
  const titles = new Map<string, string>()
  for (const post of posts) {
    titles.set(
      post.slug.toLowerCase(),
      `${post.episode} · ${post.shortTitle || post.title}`,
    )
  }
  return [...dueCountBySlug(cards).entries()]
    .map(([slug, count]) => ({
      slug,
      count,
      title: titles.get(slug) || slug,
    }))
    .sort((a, b) => b.count - a.count || a.title.localeCompare(b.title, 'ru'))
}

function dueTasks(items: SiteUserTask[]): SiteUserTask[] {
  return flattenTasks(items)
    .filter((task) => isOverdue(task) || isDueToday(task))
    .sort((a, b) => {
      const aRank = isOverdue(a) ? 0 : 1
      const bRank = isOverdue(b) ? 0 : 1
      if (aRank !== bRank) {
        return aRank - bRank
      }
      const byTime = (a.dueTime || '').localeCompare(b.dueTime || '')
      if (byTime !== 0) {
        return byTime
      }
      return a.title.localeCompare(b.title, 'ru')
    })
}

export function TodayPanel({
  queuedSlugs,
  busySlug,
  queueError,
  queueTick,
  onQueue,
  onOpenTask,
  onStartFocus,
  onTasksLoaded,
}: TodayPanelProps) {
  const { posts, isReady: postsReady } = useLearnPosts()
  const { completedSlugs, isReady: progressReady } = useSiteLearnProgress()
  const [tasks, setTasks] = useState<SiteUserTask[]>([])
  const [habits, setHabits] = useState<SiteUserHabit[]>([])
  const [cards, setCards] = useState<SiteAnkiCardState[]>([])
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [busyTaskId, setBusyTaskId] = useState<number | null>(null)
  const [busyHabitId, setBusyHabitId] = useState<number | null>(null)
  const today = isoDate(new Date())

  const refresh = useCallback(async () => {
    const [taskResult, habitResult, cardResult] = await Promise.allSettled([
      siteListUserTasks(),
      siteListHabits(),
      siteListAnkiCards(),
    ])
    const messages: string[] = []
    if (taskResult.status === 'fulfilled') {
      setTasks(taskResult.value)
      onTasksLoaded(taskResult.value)
    } else {
      setTasks([])
      messages.push('задачи')
    }
    if (habitResult.status === 'fulfilled') {
      setHabits(habitResult.value)
    } else {
      setHabits([])
      messages.push('привычки')
    }
    if (cardResult.status === 'fulfilled') {
      setCards(cardResult.value)
    } else {
      setCards([])
      messages.push('карточки Anki')
    }
    setError(messages.length ? `Не удалось загрузить: ${messages.join(', ')}` : '')
    setReady(true)
  }, [onTasksLoaded])

  useEffect(() => {
    void refresh()
  }, [refresh, queueTick])

  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)
  const nextPost =
    seasons.flatMap((track) => track.episodes).find((post) => !completedSlugs.has(post.slug)) ||
    null
  const tasksDue = useMemo(() => dueTasks(tasks), [tasks])
  const openHabits = habits.filter(
    (habit) => !habit.isArchived && !habit.checks.includes(today),
  )
  const groups = useMemo(() => ankiGroups(cards, published), [cards, published])

  async function toggleTask(task: SiteUserTask) {
    setBusyTaskId(task.id)
    setError('')
    try {
      await siteUpdateUserTask(task.id, { completed: !task.completed })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обновить задачу')
    } finally {
      setBusyTaskId(null)
    }
  }

  async function checkHabit(habit: SiteUserHabit) {
    setBusyHabitId(habit.id)
    setError('')
    try {
      const updated = await siteSetHabitCheck(habit.id, { day: today, checked: true })
      setHabits((prev) => prev.map((item) => (item.id === habit.id ? updated : item)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отметить привычку')
    } finally {
      setBusyHabitId(null)
    }
  }

  if (!ready || !postsReady || !progressReady) {
    return <p className="learn-section-note">Собираю сегодняшний список…</p>
  }

  const visibleTasks = tasksDue.slice(0, TASK_LIMIT)
  const hiddenTasks = tasksDue.length - visibleTasks.length
  const visibleAnki = groups.slice(0, ANKI_LIMIT)
  const hiddenAnki = groups.length - visibleAnki.length
  const ankiTotal = groups.reduce((sum, group) => sum + group.count, 0)
  const isClear =
    tasksDue.length === 0 && openHabits.length === 0 && groups.length === 0 && !nextPost

  return (
    <div className="tasks-today">
      {error ? <p className="tasks-personal-error">{error}</p> : null}
      {queueError ? <p className="tasks-personal-error">{queueError}</p> : null}

      {isClear ? (
        <p className="learn-section-note">
          На сегодня пусто: нет сроков, привычек и карточек к повторению.
        </p>
      ) : null}

      {tasksDue.length > 0 ? (
        <section aria-labelledby="today-tasks-title">
          <h2 id="today-tasks-title" className="learn-section-title">
            Задачи · {tasksDue.length}
          </h2>
          <ul className="tasks-today-list">
            {visibleTasks.map((task) => {
              const overdue = isOverdue(task)
              const target = learnTargetFromNotes(task.notes)
              const dueLabel = formatDue(task.dueAt, task.dueTime)
              return (
                <li
                  key={task.id}
                  className={overdue ? 'tasks-today-row is-overdue' : 'tasks-today-row'}
                >
                  <div className="tasks-today-main">
                    <input
                      type="checkbox"
                      checked={task.completed}
                      disabled={busyTaskId === task.id}
                      aria-label={task.completed ? 'Открыть снова' : 'Отметить готовым'}
                      onChange={() => void toggleTask(task)}
                    />
                    <span>
                      <span className="tasks-today-title">{task.title}</span>
                      {dueLabel ? (
                        <span className={overdue ? 'tasks-due is-overdue' : 'tasks-due'}>
                          {overdue ? 'Просрочено · ' : ''}
                          {dueLabel}
                        </span>
                      ) : null}
                    </span>
                  </div>
                  <div className="tasks-today-actions">
                    {target ? (
                      <Link
                        to={learnEpisodePath(
                          target.slug,
                          target.kind === 'quiz' ? 'quiz' : undefined,
                        )}
                        className="learn-admin-link"
                      >
                        {target.kind === 'quiz' ? 'Тест' : 'Статья'}
                      </Link>
                    ) : null}
                    {!task.completed ? (
                      <button
                        type="button"
                        className="learn-admin-btn"
                        onClick={() => onStartFocus(task.id)}
                      >
                        Фокус
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="learn-admin-btn"
                      onClick={() => onOpenTask(task.id)}
                    >
                      Карточка
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
          {hiddenTasks > 0 ? (
            <p className="learn-section-note">Ещё {hiddenTasks} в списке задач.</p>
          ) : null}
        </section>
      ) : null}

      {openHabits.length > 0 ? (
        <section aria-labelledby="today-habits-title">
          <h2 id="today-habits-title" className="learn-section-title">
            Привычки · {openHabits.length}
          </h2>
          <ul className="tasks-today-list">
            {openHabits.map((habit) => (
              <li key={habit.id} className="tasks-today-row">
                <div className="tasks-today-main">
                  <span className="tasks-today-title">{habit.title}</span>
                  <span className="tasks-mini-badge">серия {habit.streak}</span>
                </div>
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={busyHabitId === habit.id}
                  onClick={() => void checkHabit(habit)}
                >
                  Отметить
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {groups.length > 0 ? (
        <section aria-labelledby="today-anki-title">
          <h2 id="today-anki-title" className="learn-section-title">
            Anki · {ankiTotal}
          </h2>
          <ul className="tasks-today-list">
            {visibleAnki.map((group) => (
              <li key={group.slug} className="tasks-today-row">
                <span className="tasks-today-title">
                  {group.title}
                  <span className="learn-badge tasks-badge-due">{group.count}</span>
                </span>
                <Link
                  to={learnEpisodePath(group.slug, 'anki')}
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Повторить
                </Link>
              </li>
            ))}
          </ul>
          {hiddenAnki > 0 ? (
            <p className="learn-section-note">Ещё {hiddenAnki} выпусков с карточками.</p>
          ) : null}
        </section>
      ) : null}

      {nextPost ? (
        <section aria-labelledby="today-learn-title">
          <h2 id="today-learn-title" className="learn-section-title">
            Следующий выпуск
          </h2>
          <div className="tasks-today-row">
            <div className="tasks-today-main">
              <span className="tasks-today-title">
                {nextPost.episode} · {nextPost.shortTitle || nextPost.title}
              </span>
              {nextPost.durationMin > 0 ? (
                <span className="learn-badge">{nextPost.durationMin} мин</span>
              ) : null}
            </div>
            <div className="tasks-today-actions">
              <QueueLearnButton
                label="В разобрать"
                queued={learnSlugQueued(queuedSlugs, nextPost.slug)}
                busy={busySlug === learnTaskKey(nextPost.slug, 'article')}
                onQueue={() => onQueue(nextPost)}
              />
              <Link
                to={learnEpisodePath(nextPost.slug)}
                className="learn-admin-btn learn-admin-btn-primary"
              >
                Открыть
              </Link>
            </div>
          </div>
        </section>
      ) : published.length > 0 ? (
        <p className="learn-section-note">
          Все выпуски отмечены. <Link to="/game/cert">Сертификаты</Link>
        </p>
      ) : null}
    </div>
  )
}
