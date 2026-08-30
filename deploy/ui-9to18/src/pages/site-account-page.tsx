import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import { siteChangePassword } from '@/data/site/site-api'
import {
  clearSiteAuthSession,
  describeSiteRole,
  getManagedAppSlugs,
  getSiteAuthSession,
  isSuperAdmin,
  refreshSiteAuthSession,
  type SiteAuthSession,
} from '@/data/site/site-auth'
import {
  progressPercent,
  useSiteLearnProgress,
} from '@/data/site/use-learn-progress'
import { canEditLearn, getLearnAuthSession } from '@/data/learn/learn-auth'

type AccountSectionId =
  | 'profile'
  | 'learn'
  | 'learning-map'
  | 'contact'
  | 'password'
  | `app:${string}`
  | 'site-admin'
  | 'learn-cms'

type NavItem = {
  id: AccountSectionId
  label: string
  hint?: string
}

function roleFunctions(session: SiteAuthSession): string[] {
  const items = [
    'Чтение страниц и блогов всех сервисов на витрине',
    'Личный кабинет, смена пароля и прогресс Learn',
    'Форма связи с командой',
    'Карта обучения и материалы Learn',
  ]
  if (session.appAdmin.length > 0) {
    items.push(
      `Админка сервисов: ${session.appAdmin.join(', ')} — плашка, страница и статьи`,
    )
  }
  if (isSuperAdmin(session)) {
    items.push(
      'Супер-админ сайта: плашки, спотлайт, пользователи, карта (MD), назначение админов',
      'Learn · контент: правка учебных выпусков',
    )
  }
  return items
}

export function SiteAccountPage() {
  const [session, setSession] = useState<SiteAuthSession | null>(() => getSiteAuthSession())
  const [loading, setLoading] = useState(Boolean(getSiteAuthSession()))
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [searchParams, setSearchParams] = useSearchParams()
  const { posts, isReady: postsReady } = useLearnPosts()
  const { completedSlugs, isReady: progressReady } = useSiteLearnProgress()
  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)
  const learnSession = getLearnAuthSession()

  useEffect(() => {
    if (!getSiteAuthSession()?.accessToken) {
      setLoading(false)
      return
    }
    let cancelled = false
    void refreshSiteAuthSession()
      .then((next) => {
        if (cancelled) return
        setSession(next)
        setError('')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Не удалось обновить профиль')
        setSession(getSiteAuthSession())
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const managed = session ? getManagedAppSlugs(session) : []
  const doneCount = published.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, published.length)

  const navItems = useMemo((): NavItem[] => {
    if (!session) {
      return []
    }
    const items: NavItem[] = [
      { id: 'profile', label: 'Профиль', hint: 'Роль и возможности' },
      { id: 'learn', label: 'Learn', hint: 'Теория и прогресс' },
      { id: 'learning-map', label: 'Карта обучения', hint: 'Mind map · собеседование' },
      { id: 'contact', label: 'Форма связи', hint: 'Написать команде' },
    ]
    for (const slug of managed) {
      items.push({
        id: `app:${slug}`,
        label: `Админ сервиса · ${slug}`,
        hint: 'Плашка и статьи',
      })
    }
    if (isSuperAdmin(session)) {
      items.push(
        { id: 'site-admin', label: 'Супер-админ сайта', hint: 'Витрина и пользователи' },
        {
          id: 'learn-cms',
          label: 'Learn · контент',
          hint: canEditLearn(learnSession?.role)
            ? 'Сессия CopyParse активна'
            : 'Вход через сайт или CopyParse',
        },
      )
    }
    items.push({ id: 'password', label: 'Смена пароля', hint: 'Безопасность аккаунта' })
    return items
  }, [session, managed, learnSession?.role])

  const sectionParam = searchParams.get('section') || 'profile'
  const activeId: AccountSectionId = navItems.some((item) => item.id === sectionParam)
    ? (sectionParam as AccountSectionId)
    : 'profile'

  function openSection(id: AccountSectionId) {
    setSearchParams(id === 'profile' ? {} : { section: id }, { replace: true })
  }

  async function onChangePassword(event: FormEvent) {
    event.preventDefault()
    setError('')
    setOk('')
    try {
      await siteChangePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setOk('Пароль обновлён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка смены пароля')
    }
  }

  if (!session) {
    return (
      <PageShell>
        <p className="learn-section-note">
          Нужен аккаунт.{' '}
          <Link to="/register">Зарегистрироваться</Link>
          {' · '}
          <Link to="/login">Войти</Link>
        </p>
      </PageShell>
    )
  }

  const functions = roleFunctions(session)
  const activeNav = navItems.find((item) => item.id === activeId)

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Личный кабинет · Profile</p>
        <h1 className="learn-title">{session.username}</h1>
        <p className="learn-lead">
          {session.email}
          {loading ? ' · обновление роли…' : null}
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      <div className="account-layout">
        <nav className="account-nav" aria-label="Разделы кабинета">
          <p className="account-nav-label">Разделы</p>
          <ul className="account-nav-list">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`account-nav-item${activeId === item.id ? ' is-active' : ''}`}
                  aria-current={activeId === item.id ? 'page' : undefined}
                  onClick={() => openSection(item.id)}
                >
                  <span className="account-nav-item-title">{item.label}</span>
                  {item.hint ? <span className="account-nav-item-hint">{item.hint}</span> : null}
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="account-nav-logout"
            onClick={() => {
              clearSiteAuthSession()
              window.location.href = '/login'
            }}
          >
            Выйти
          </button>
        </nav>

        <div className="account-panel" aria-live="polite">
          <header className="account-panel-head">
            <h2 className="section-block-title">{activeNav?.label || 'Раздел'}</h2>
            {activeNav?.hint ? <p className="section-block-lead">{activeNav.hint}</p> : null}
          </header>

          {activeId === 'profile' ? (
            <div className="account-panel-body">
              <p className="account-role">
                Роль: <strong>{describeSiteRole(session)}</strong>
              </p>
              <h3 className="account-subheading">Доступные функции</h3>
              <ul className="account-feature-list">
                {functions.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="learn-section-note">
                Слева — меню разделов: откройте Learn, карту, связь или админку, если она вам
                доступна.
              </p>
            </div>
          ) : null}

          {activeId === 'learn' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Теория, лабы и отслеживание прогресса по сезонам.
              </p>
              {!postsReady || !progressReady ? (
                <p className="learn-section-note">Загрузка…</p>
              ) : published.length === 0 ? (
                <p className="learn-section-note">Пока нет опубликованных выпусков.</p>
              ) : (
                <>
                  <p className="account-stat">
                    {doneCount}/{published.length} выпусков ({pct}%)
                  </p>
                  <ul className="account-feature-list">
                    {seasons.map((track) => {
                      const trackDone = track.episodes.filter((e) =>
                        completedSlugs.has(e.slug),
                      ).length
                      return (
                        <li key={track.id}>
                          {track.title}: {trackDone}/{track.episodes.length}
                        </li>
                      )
                    })}
                  </ul>
                </>
              )}
              <div className="account-actions">
                <Link to="/game/learn" className="learn-admin-btn learn-admin-btn-primary">
                  Открыть Learn
                </Link>
                <Link to="/game/tasks" className="learn-admin-btn">
                  Чек-лист
                </Link>
                <Link to="/game/cert" className="learn-admin-btn">
                  Сертификат
                </Link>
                <Link to="/game/quiz" className="learn-admin-btn">
                  Quiz
                </Link>
              </div>
            </div>
          ) : null}

          {activeId === 'learning-map' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Интерактивная mind map подготовки к собеседованию: ветки, теги, Anki и выгрузка в
                Markdown.
              </p>
              <div className="account-actions">
                <Link
                  to="/game/learning-map"
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Открыть карту обучения
                </Link>
              </div>
            </div>
          ) : null}

          {activeId === 'contact' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Напишите команде через форму на главной — сообщения видны супер-админу в админке.
              </p>
              <div className="account-actions">
                <Link to="/#contacts" className="learn-admin-btn learn-admin-btn-primary">
                  Перейти к форме связи
                </Link>
              </div>
            </div>
          ) : null}

          {activeId.startsWith('app:') ? (
            <div className="account-panel-body">
              {(() => {
                const slug = activeId.slice(4)
                return (
                  <>
                    <p className="learn-section-note">
                      Вы админ сервиса <strong>{slug}</strong>: можете править плашку, страницу и
                      статьи блога.
                    </p>
                    <div className="account-actions">
                      <Link
                        to={`/admin/apps/${slug}`}
                        className="learn-admin-btn learn-admin-btn-primary"
                      >
                        Открыть админку · {slug}
                      </Link>
                    </div>
                  </>
                )
              })()}
            </div>
          ) : null}

          {activeId === 'site-admin' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Полный доступ к витрине 9to18: плашки и порядок, спотлайт, контакты, пользователи,
                загрузка MD карты обучения.
              </p>
              <div className="account-actions">
                <Link to="/admin" className="learn-admin-btn learn-admin-btn-primary">
                  Открыть супер-админку
                </Link>
              </div>
            </div>
          ) : null}

          {activeId === 'learn-cms' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Редактор учебных выпусков Learn.
                {canEditLearn(learnSession?.role)
                  ? ' Сессия CopyParse уже активна.'
                  : ' Можно войти как супер-админ сайта или через аккаунт CopyParse.'}
              </p>
              <div className="account-actions">
                <Link
                  to="/game/learn/admin"
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Открыть Learn · контент
                </Link>
              </div>
            </div>
          ) : null}

          {activeId === 'password' ? (
            <div className="account-panel-body">
              <form className="learn-admin-form" onSubmit={onChangePassword}>
                <label className="learn-admin-field">
                  <span>Текущий пароль</span>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                </label>
                <label className="learn-admin-field">
                  <span>Новый пароль</span>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                  />
                </label>
                <button type="submit" className="learn-admin-btn learn-admin-btn-primary">
                  Сохранить пароль
                </button>
              </form>
              <p className="learn-section-note">
                Забыли пароль? <Link to="/login?reset=1">Сброс по токену</Link>
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </PageShell>
  )
}
