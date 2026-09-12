import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AdminJumpNav } from '@/components/admin-jump-nav'
import { PageShell } from '@/components/page-shell'
import { clearLearnAuthSession, getLearnAuthSession } from '@/data/learn/learn-auth'
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

function LearnFrame({ embedded, children }: { embedded: boolean; children: ReactNode }) {
  if (embedded) {
    return <div className="account-embed">{children}</div>
  }
  return <PageShell variant="admin">{children}</PageShell>
}

export type LearnAdminPageProps = {
  embedded?: boolean
  onCreate?: () => void
  onEdit?: (slug: string) => void
}

export function LearnAdminPage({
  embedded = false,
  onCreate,
  onEdit,
}: LearnAdminPageProps = {}) {
  const { posts, isReady, error, reload } = useLearnPosts({ admin: true })
  const [scheduleStart, setScheduleStart] = useState(() =>
    toDatetimeLocalValue(new Date().toISOString()),
  )
  const [intervalDays, setIntervalDays] = useState(1)
  const [scheduleMessage, setScheduleMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const session = getLearnAuthSession()

  const handleDelete = (slug: string, title: string): void => {
    if (!window.confirm(`Удалить запись «${title}»?`)) {
      return
    }
    setBusy(true)
    void deleteLearnPost(slug)
      .then(() => reload())
      .catch((err) => setScheduleMessage(err instanceof Error ? err.message : 'Ошибка удаления'))
      .finally(() => setBusy(false))
  }

  const handleReset = (): void => {
    if (!window.confirm('Сбросить все записи к seed S01? Правки на сервере будут заменены.')) {
      return
    }
    setBusy(true)
    void resetLearnPostsToSeed()
      .then(() => {
        setScheduleMessage('Сброс выполнен')
        reload()
      })
      .catch((err) => setScheduleMessage(err instanceof Error ? err.message : 'Ошибка сброса'))
      .finally(() => setBusy(false))
  }

  const handleScheduleAll = (): void => {
    if (
      !window.confirm(
        `Назначить даты всем ${posts.length} записям по порядку: первая ${scheduleStart}, далее +${intervalDays} дн.?`,
      )
    ) {
      return
    }
    setBusy(true)
    void scheduleAllLearnPosts(fromDatetimeLocalValue(scheduleStart), intervalDays)
      .then(() => {
        setScheduleMessage('Расписание применено')
        reload()
      })
      .catch((err) =>
        setScheduleMessage(err instanceof Error ? err.message : 'Не удалось применить расписание'),
      )
      .finally(() => setBusy(false))
  }

  return (
    <LearnFrame embedded={embedded}>
      {embedded ? null : (
        <Link to="/game/learn" className="back-link">
          ← К Learn
        </Link>
      )}

      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">Учебные записи</h1>
        <p className="learn-lead">
          Управление выпусками. Супер-админ сайта может входить с JWT 9to18 (SSO-lite); иначе —
          аккаунт CopyParse (admin/author). Спотлайт на главной — в{' '}
          {embedded ? (
            <Link to="/account?section=site-admin">кабинете супер-админа</Link>
          ) : (
            <Link to="/admin">/admin</Link>
          )}
          .
          {session?.username
            ? ` Сессия CopyParse: ${session.username} (${session.role}).`
            : ' Сессия CopyParse не активна.'}
        </p>
        <p className="learn-admin-entry">
          <button
            type="button"
            className="learn-admin-link"
            onClick={() => {
              clearLearnAuthSession()
              if (embedded) {
                window.location.reload()
                return
              }
              window.location.href = '/game/learn/admin/login'
            }}
          >
            Выйти
          </button>
        </p>
      </header>

      {embedded ? null : (
        <AdminJumpNav
          items={[
            { id: 'learn-schedule', label: 'Расписание' },
            { id: 'learn-posts', label: 'Записи' },
          ]}
        />
      )}

      <section
        id="learn-schedule"
        className="learn-schedule admin-jump-target"
        aria-labelledby="learn-schedule-heading"
      >        <h2 id="learn-schedule-heading" className="learn-section-title">
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
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            onClick={handleScheduleAll}
            disabled={busy}
          >
            Применить ко всем
          </button>
        </div>
        {scheduleMessage ? <p className="learn-admin-ok">{scheduleMessage}</p> : null}
        {error ? (
          <p className="learn-section-note" style={{ color: '#b91c1c' }}>
            {error}
          </p>
        ) : null}
      </section>

      <div id="learn-posts" className="admin-jump-target">
      <div className="learn-admin-actions">
        {onCreate ? (
          <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={onCreate}>
            Добавить запись
          </button>
        ) : (
          <Link to="/game/learn/admin/new" className="learn-admin-btn learn-admin-btn-primary">
            Добавить запись
          </Link>
        )}
        <button type="button" className="learn-admin-btn" onClick={handleReset} disabled={busy}>
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
                      {isLive ? 'опубликовано' : 'запланировано'}{' '}
                      {formatPublishDate(post.publishedAt)}
                    </span>
                  </span>
                </div>
                <div className="learn-admin-row-actions">
                  <Link to={`/game/learn/${post.slug}?preview=1`} className="learn-admin-link">
                    Открыть
                  </Link>
                  {onEdit ? (
                    <button
                      type="button"
                      className="learn-admin-link"
                      onClick={() => onEdit(post.slug)}
                    >
                      Редактировать
                    </button>
                  ) : (
                    <Link to={`/game/learn/admin/${post.slug}`} className="learn-admin-link">
                      Редактировать
                    </Link>
                  )}
                  <button
                    type="button"
                    className="learn-admin-link learn-admin-danger"
                    onClick={() => handleDelete(post.slug, post.title)}
                    disabled={busy}
                  >
                    Удалить
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
      </div>
    </LearnFrame>
  )
}
