import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  deleteLearnPost,
  formatPublishDate,
  fromDatetimeLocalValue,
  isPostPublished,
  resetLearnPostsToSeed,
  scheduleAllLearnPosts,
  toDatetimeLocalValue,
} from '@/data/learn/learn-store'
import { rubricTitleById, useLearnPosts } from '@/data/learn/use-learn-posts'

export function LearnAdminPage() {
  const { posts, isReady, reload } = useLearnPosts()
  const [scheduleStart, setScheduleStart] = useState(() =>
    toDatetimeLocalValue(new Date().toISOString()),
  )
  const [intervalDays, setIntervalDays] = useState(1)
  const [scheduleMessage, setScheduleMessage] = useState('')

  const handleDelete = (slug: string, title: string): void => {
    if (!window.confirm(`Удалить запись «${title}»?`)) {
      return
    }
    deleteLearnPost(slug)
    reload()
  }

  const handleReset = (): void => {
    if (!window.confirm('Сбросить все записи к исходным S01E01–E10? Локальные правки пропадут.')) {
      return
    }
    resetLearnPostsToSeed()
    reload()
  }

  const handleScheduleAll = (): void => {
    if (
      !window.confirm(
        `Назначить даты всем ${posts.length} записям по порядку: первая ${scheduleStart}, далее +${intervalDays} дн.?`,
      )
    ) {
      return
    }
    try {
      scheduleAllLearnPosts(fromDatetimeLocalValue(scheduleStart), intervalDays)
      setScheduleMessage('Расписание применено')
      reload()
    } catch (error) {
      setScheduleMessage(error instanceof Error ? error.message : 'Не удалось применить расписание')
    }
  }

  return (
    <PageShell>
      <Link to="/game/learn" className="back-link">
        ← К Learn
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">Записи блога</h1>
        <p className="learn-lead">
          Добавление и правка выпусков. Контент хранится в localStorage этого браузера. На сайте
          видны только записи с датой публикации ≤ сейчас.
        </p>
      </header>

      <section className="learn-schedule" aria-labelledby="learn-schedule-heading">
        <h2 id="learn-schedule-heading" className="learn-section-title">
          Расписание всех статей
        </h2>
        <p className="learn-section-note">
          Задаёт `publishedAt` по порядку (`order`): первая дата, затем шаг в днях.
        </p>
        <div className="learn-schedule-row">
          <label className="learn-admin-field">
            <span>Дата первой публикации</span>
            <input
              type="datetime-local"
              value={scheduleStart}
              onChange={(event) => {
                setScheduleStart(event.target.value)
                setScheduleMessage('')
              }}
            />
          </label>
          <label className="learn-admin-field">
            <span>Интервал (дней)</span>
            <input
              type="number"
              min={0}
              step={1}
              value={intervalDays}
              onChange={(event) => {
                setIntervalDays(Number(event.target.value) || 0)
                setScheduleMessage('')
              }}
            />
          </label>
          <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={handleScheduleAll}>
            Применить ко всем
          </button>
        </div>
        {scheduleMessage ? <p className="learn-admin-ok">{scheduleMessage}</p> : null}
      </section>

      <div className="learn-admin-actions">
        <Link to="/game/learn/admin/new" className="learn-admin-btn learn-admin-btn-primary">
          Добавить запись
        </Link>
        <button type="button" className="learn-admin-btn" onClick={handleReset}>
          Сбросить к S01
        </button>
      </div>

      {!isReady ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <ul className="learn-admin-list">
          {posts.map((post) => {
            const isLive = isPostPublished(post)
            return (
              <li key={post.slug} className="learn-admin-row">
                <div className="learn-admin-row-main">
                  <span className="learn-episode-code">{post.episode}</span>
                  <span className="learn-admin-row-title">{post.title}</span>
                  <span className="learn-section-note">
                    {rubricTitleById(post.rubricId)} · order {post.order} ·{' '}
                    <span className={isLive ? 'learn-status-live' : 'learn-status-scheduled'}>
                      {isLive ? 'опубликовано' : 'запланировано'} {formatPublishDate(post.publishedAt)}
                    </span>
                  </span>
                </div>
                <div className="learn-admin-row-actions">
                  <Link to={`/game/learn/${post.slug}?preview=1`} className="learn-admin-link">
                    Открыть
                  </Link>
                  <Link to={`/game/learn/admin/${post.slug}`} className="learn-admin-link">
                    Редактировать
                  </Link>
                  <button
                    type="button"
                    className="learn-admin-link learn-admin-danger"
                    onClick={() => handleDelete(post.slug, post.title)}
                  >
                    Удалить
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </PageShell>
  )
}
