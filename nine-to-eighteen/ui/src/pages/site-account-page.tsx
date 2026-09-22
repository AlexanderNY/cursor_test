import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { AdminJumpNav, type AdminNavGroup, type AdminNavItem } from '@/components/admin-jump-nav'
import { ContactForm } from '@/components/contact-form'
import { PageShell } from '@/components/page-shell'
import { AppBlogPage, AppPostPage } from '@/pages/app-blog-page'
import { LearnAdminEditPage } from '@/pages/learn-admin-edit-page'
import { LearnAdminPage } from '@/pages/learn-admin-page'
import { AppAdminPage, SiteAdminPage } from '@/pages/site-admin-page'
import {
  getPublishedPosts,
  getSeasonTracks,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import {
  siteChangePassword,
  siteFetchPhotoBlob,
  siteGetProfile,
  siteGetStudySummary,
  sitePutProfile,
  siteUploadPhoto,
  type SiteStudySummary,
  type SiteUserProfile,
} from '@/data/site/site-api'
import {
  clearSiteAuthSession,
  describeSiteRole,
  canManageApp,
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

type AccountSectionId =
  | 'profile'
  | 'learn'
  | 'study'
  | 'learning-map'
  | 'hh-resume'
  | 'contact'
  | 'password'
  | `app:${string}`
  | 'site-admin'
  | 'learn-cms'

type AccountNavMeta = {
  id: AccountSectionId
  label: string
  hint?: string
}

function accountHref(id: AccountSectionId): string {
  return id === 'profile' ? '/account' : `/account?section=${encodeURIComponent(id)}`
}

function roleFunctions(session: SiteAuthSession): string[] {
  const items = [
    'Чтение страниц и блогов всех сервисов на витрине',
    'Личный кабинет учащегося: прогресс Learn, тесты и anki',
    'Форма связи с командой',
    'Карта обучения и материалы Learn',
  ]
  if (session.appAdmin.length > 0) {
    items.push(
      `Кабинет владельца: ${session.appAdmin.join(', ')} — описание, плашка и блог`,
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
  const [study, setStudy] = useState<SiteStudySummary | null>(null)
  const [studyReady, setStudyReady] = useState(false)
  const [profile, setProfile] = useState<SiteUserProfile | null>(null)
  const [profileReady, setProfileReady] = useState(false)
  const [profileSaving, setProfileSaving] = useState(false)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [lastName, setLastName] = useState('')
  const [firstName, setFirstName] = useState('')
  const [patronymic, setPatronymic] = useState('')
  const [phone, setPhone] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [city, setCity] = useState('')
  const [citizenship, setCitizenship] = useState('')
  const [readyForTrips, setReadyForTrips] = useState(false)
  const published = getPublishedPosts(posts)
  const seasons = getSeasonTracks(posts)

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

  useEffect(() => {
    if (!getSiteAuthSession()?.accessToken) {
      setStudy(null)
      setStudyReady(true)
      return
    }
    let cancelled = false
    void siteGetStudySummary()
      .then((next) => {
        if (!cancelled) setStudy(next)
      })
      .catch(() => {
        if (!cancelled) setStudy(null)
      })
      .finally(() => {
        if (!cancelled) setStudyReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!getSiteAuthSession()?.accessToken) {
      setProfile(null)
      setProfileReady(true)
      return
    }
    let cancelled = false
    void siteGetProfile()
      .then(async (next) => {
        if (cancelled) return
        setProfile(next)
        setLastName(next.lastName)
        setFirstName(next.firstName)
        setPatronymic(next.patronymic)
        setPhone(next.phone)
        setBirthDate(next.birthDate || '')
        setCity(next.city)
        setCitizenship(next.citizenship)
        setReadyForTrips(next.readyForTrips)
        if (next.hasPhoto) {
          const url = await siteFetchPhotoBlob()
          if (!cancelled) {
            setPhotoPreview((prev) => {
              if (prev) URL.revokeObjectURL(prev)
              return url
            })
          }
        }
      })
      .catch(() => {
        if (!cancelled) setProfile(null)
      })
      .finally(() => {
        if (!cancelled) setProfileReady(true)
      })
    return () => {
      cancelled = true
      setPhotoPreview((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
    }
  }, [])

  const managed = session ? getManagedAppSlugs(session) : []
  const doneCount = published.filter((p) => completedSlugs.has(p.slug)).length
  const pct = progressPercent(doneCount, published.length)

  const accountGroups = useMemo((): AdminNavGroup[] => {
    if (!session) {
      return []
    }
    const cabinetMeta: AccountNavMeta[] = [
      { id: 'profile', label: 'Профиль', hint: 'Анкета и роль' },
      { id: 'study', label: 'Учёба', hint: 'Тесты и anki' },
      { id: 'learn', label: 'Learn', hint: 'Теория и прогресс' },
      { id: 'learning-map', label: 'Карта обучения', hint: 'Mind map · собеседование' },
      { id: 'hh-resume', label: 'Резюме', hint: 'Плашка сервиса на главной' },
      { id: 'contact', label: 'Форма связи', hint: 'Написать команде' },
      { id: 'password', label: 'Смена пароля', hint: 'Безопасность аккаунта' },
    ]
    const serviceMeta: AccountNavMeta[] = managed.map((slug) => ({
      id: `app:${slug}`,
      label: slug,
      hint: 'Описание и блог',
    }))
    const adminMeta: AccountNavMeta[] = []
    if (isSuperAdmin(session)) {
      adminMeta.push(
        { id: 'site-admin', label: 'Супер-админ сайта', hint: 'Витрина и пользователи' },
        {
          id: 'learn-cms',
          label: 'Learn · контент',
          hint: 'Супер-админ · Learn CMS',
        },
      )
    }
    const toNav = (meta: AccountNavMeta[]): AdminNavItem[] =>
      meta.map((item) => ({
        id: item.id,
        label: item.label,
        href: accountHref(item.id),
      }))
    const groups: AdminNavGroup[] = [{ label: 'Кабинет', items: toNav(cabinetMeta) }]
    if (serviceMeta.length > 0) {
      groups.push({ label: 'Сервисы', items: toNav(serviceMeta) })
    }
    if (adminMeta.length > 0) {
      groups.push({ label: 'Админ-разделы', items: toNav(adminMeta) })
    }
    return groups
  }, [session, managed])

  const allMeta = useMemo(
    () =>
      accountGroups.flatMap((group) =>
        group.items.map((item) => {
          const id = item.id as AccountSectionId
          const hintById: Partial<Record<AccountSectionId, string>> = {
            profile: 'Анкета и фото',
            study: 'Тесты и anki',
            learn: 'Теория и прогресс',
            'learning-map': 'Mind map · собеседование',
            'hh-resume': 'Плашка сервиса на главной',
            contact: 'Написать команде',
            password: 'Безопасность аккаунта',
            'site-admin': 'Витрина и пользователи',
            'learn-cms': 'Супер-админ · Learn CMS',
          }
          return {
            id,
            label: item.label,
            hint: id.startsWith('app:') ? 'Описание и блог' : hintById[id],
          } satisfies AccountNavMeta
        }),
      ),
    [accountGroups],
  )

  const sectionParam = searchParams.get('section') || 'profile'
  const appSectionSlug = sectionParam.startsWith('app:') ? sectionParam.slice(4) : ''
  const activeId: AccountSectionId = allMeta.some((item) => item.id === sectionParam)
    ? (sectionParam as AccountSectionId)
    : appSectionSlug && canManageApp(appSectionSlug, session)
      ? (sectionParam as AccountSectionId)
      : 'profile'
  const paneView = searchParams.get('view') || 'overview'
  const panePost = searchParams.get('post') || ''

  function setPane(view: string, post?: string) {
    const next = new URLSearchParams(searchParams)
    if (activeId === 'profile') {
      next.delete('section')
    } else {
      next.set('section', activeId)
    }
    if (!view || view === 'overview') {
      next.delete('view')
      next.delete('post')
    } else {
      next.set('view', view)
      if (post) {
        next.set('post', post)
      } else {
        next.delete('post')
      }
    }
    setSearchParams(next, { replace: true })
  }

  function openAppAdmin(slug: string) {
    setSearchParams(
      { section: `app:${slug}`, view: 'admin' },
      { replace: true },
    )
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

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
    setError('')
    setOk('')
    setProfileSaving(true)
    try {
      const next = await sitePutProfile({
        last_name: lastName,
        first_name: firstName,
        patronymic,
        phone,
        birth_date: birthDate || null,
        city,
        citizenship,
        ready_for_trips: readyForTrips,
      })
      setProfile(next)
      setOk('Анкета сохранена')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения анкеты')
    } finally {
      setProfileSaving(false)
    }
  }

  async function onPhotoChange(file: File | null) {
    if (!file) return
    setError('')
    setOk('')
    try {
      await siteUploadPhoto(file)
      const url = await siteFetchPhotoBlob()
      setPhotoPreview((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return url
      })
      setOk('Фото обновлено')
      setProfile((prev) => (prev ? { ...prev, hasPhoto: true } : prev))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки фото')
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
  const activeNav =
    allMeta.find((item) => item.id === activeId) ??
    (activeId.startsWith('app:')
      ? {
          id: activeId,
          label: activeId.slice(4),
          hint: 'Описание и блог',
        }
      : undefined)

  return (
    <PageShell variant="admin">
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
        <div className="account-nav-shell">
          <AdminJumpNav
            showGlobal={false}
            ariaLabel="Разделы кабинета"
            groups={accountGroups}
          />
          <button
            type="button"
            className="admin-jump-nav-link account-nav-logout-link"
            onClick={() => {
              clearSiteAuthSession()
              window.location.href = '/login'
            }}
          >
            Выйти
          </button>
        </div>

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
              <h3 className="account-subheading">Анкета для резюме</h3>
              <p className="learn-section-note">
                Поля опциональны. Используются сервисом{' '}
                <Link to="/game/hh-resume">HH-резюме</Link>. Email:{' '}
                <strong>{session.email}</strong>
                {profile?.email && profile.email !== session.email
                  ? ` (${profile.email})`
                  : null}
              </p>
              {!profileReady ? (
                <p className="learn-section-note">Загрузка анкеты…</p>
              ) : (
                <form className="learn-admin-form" onSubmit={onSaveProfile}>
                  <div className="hh-profile-photo-row">
                    {photoPreview ? (
                      <img src={photoPreview} alt="" className="hh-resume-photo" />
                    ) : (
                      <div className="hh-resume-photo hh-resume-photo-placeholder" aria-hidden>
                        фото
                      </div>
                    )}
                    <label className="learn-admin-field">
                      <span>Фото (JPEG/PNG/WebP)</span>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={(e) => {
                          const file = e.target.files?.[0] || null
                          void onPhotoChange(file)
                          e.target.value = ''
                        }}
                      />
                    </label>
                  </div>
                  <div className="learn-admin-grid">
                    <label className="learn-admin-field">
                      <span>Фамилия</span>
                      <input
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        maxLength={120}
                        autoComplete="family-name"
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Имя</span>
                      <input
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        maxLength={120}
                        autoComplete="given-name"
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Отчество</span>
                      <input
                        value={patronymic}
                        onChange={(e) => setPatronymic(e.target.value)}
                        maxLength={120}
                        autoComplete="additional-name"
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Телефон</span>
                      <input
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        maxLength={64}
                        autoComplete="tel"
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Дата рождения</span>
                      <input
                        type="date"
                        value={birthDate}
                        onChange={(e) => setBirthDate(e.target.value)}
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Город</span>
                      <input
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        maxLength={120}
                      />
                    </label>
                    <label className="learn-admin-field">
                      <span>Гражданство</span>
                      <input
                        value={citizenship}
                        onChange={(e) => setCitizenship(e.target.value)}
                        maxLength={120}
                      />
                    </label>
                  </div>
                  <label className="hh-resume-check">
                    <input
                      type="checkbox"
                      checked={readyForTrips}
                      onChange={(e) => setReadyForTrips(e.target.checked)}
                    />
                    Готовность к командировкам
                  </label>
                  <div className="account-actions">
                    <button
                      type="submit"
                      className="learn-admin-btn learn-admin-btn-primary"
                      disabled={profileSaving}
                    >
                      Сохранить анкету
                    </button>
                    <Link to="/game/hh-resume" className="learn-admin-btn">
                      Открыть HH-резюме
                    </Link>
                  </div>
                </form>
              )}
              <h3 className="account-subheading">Доступные функции</h3>
              <ul className="account-feature-list">
                {functions.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {activeId === 'study' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Кабинет учащегося: результаты тестов по статьям и прогресс anki-карточек.
              </p>
              {!studyReady ? (
                <p className="learn-section-note">Загрузка…</p>
              ) : !study ? (
                <p className="learn-section-note">Пока нет сохранённых попыток.</p>
              ) : (
                <>
                  <div className="account-study-grid">
                    <div className="account-study-card">
                      <h3 className="account-subheading">Тесты</h3>
                      <p className="account-stat">
                        {study.quiz.attempts} попыток · среднее {study.quiz.avgPercent}%
                      </p>
                      {study.quiz.recent.length > 0 ? (
                        <ul className="account-feature-list">
                          {study.quiz.recent.map((item) => (
                            <li key={`${item.sourceKey}-${item.finishedAt}`}>
                              {item.sourceKey}: {item.score}/{item.total}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="learn-section-note">Пройдите тест в статье блога.</p>
                      )}
                    </div>
                    <div className="account-study-card">
                      <h3 className="account-subheading">Anki</h3>
                      <p className="account-stat">
                        {study.anki.cards} карточек · due {study.anki.due} · в работе{' '}
                        {study.anki.learning}
                      </p>
                      <p className="learn-section-note">
                        Оценивайте карточки в конце статей — интервалы сохранятся здесь.
                      </p>
                    </div>
                  </div>
                  {!postsReady || !progressReady ? null : (
                    <p className="learn-section-note">
                      Learn-прогресс: {doneCount}/{published.length} выпусков ({pct}%).
                    </p>
                  )}
                </>
              )}
              <div className="account-actions">
                <Link to="/game/quiz" className="learn-admin-btn learn-admin-btn-primary">
                  Quiz Learn
                </Link>
                <Link to="/game/learning-map" className="learn-admin-btn">
                  Карта · Anki
                </Link>
                <Link to="/" className="learn-admin-btn">
                  Свежие статьи
                </Link>
              </div>
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

          {activeId === 'hh-resume' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Сервис «Резюме» — отдельная плашка на главной (slug <code>hh-resume</code>).
                Опросник, шаблон HH, правка текста и навыки из Learn. Анкета и фото — в профиле.
              </p>
              <div className="account-actions">
                <Link to="/" className="learn-admin-btn">
                  На главную · плашка
                </Link>
                <Link
                  to="/game/hh-resume/quiz"
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Опросник
                </Link>
                <Link
                  to="/game/hh-resume"
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Превью
                </Link>
                <Link
                  to="/game/hh-resume/edit"
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Доработать
                </Link>
                <Link to="/account" className="learn-admin-btn">
                  Анкета
                </Link>
              </div>
            </div>
          ) : null}

          {activeId === 'contact' ? (
            <div className="account-panel-body">
              <p className="learn-section-note">
                Напишите команде — сообщения видны супер-админу в админке.
              </p>
              <ContactForm />
            </div>
          ) : null}

          {activeId.startsWith('app:') ? (
            <div className="account-panel-body">
              {(() => {
                const slug = activeId.slice(4)
                return (
                  <>
                    <p className="learn-section-note">
                      Кабинет владельца сервиса <strong>{slug}</strong>: описание на витрине, кнопки
                      приложения и блог в едином формате (введение, разделы, схемы, тест, anki).
                    </p>
                    <div className="account-actions">
                      <button
                        type="button"
                        className={
                          paneView === 'admin'
                            ? 'learn-admin-btn learn-admin-btn-primary'
                            : 'learn-admin-btn'
                        }
                        onClick={() => setPane('admin')}
                      >
                        Кабинет владельца
                      </button>
                      <button
                        type="button"
                        className={
                          paneView === 'public' || paneView === 'post'
                            ? 'learn-admin-btn learn-admin-btn-primary'
                            : 'learn-admin-btn'
                        }
                        onClick={() => setPane('public')}
                      >
                        Публичная страница
                      </button>
                    </div>
                    {paneView === 'admin' ? (
                      <AppAdminPage
                        embedded
                        slug={slug}
                        onOpenPublic={() => setPane('public')}
                        onOpenPost={(postSlug) => setPane('post', postSlug)}
                      />
                    ) : null}
                    {paneView === 'public' ? (
                      <AppBlogPage
                        embedded
                        slug={slug}
                        onOpenAdmin={() => setPane('admin')}
                        onOpenPost={(postSlug) => setPane('post', postSlug)}
                      />
                    ) : null}
                    {paneView === 'post' && panePost ? (
                      <AppPostPage
                        embedded
                        slug={slug}
                        postSlug={panePost}
                        onBack={() => setPane('public')}
                      />
                    ) : null}
                  </>
                )
              })()}
            </div>
          ) : null}

          {activeId === 'site-admin' ? (
            <div className="account-panel-body">
              <SiteAdminPage embedded onOpenApp={openAppAdmin} />
            </div>
          ) : null}

          {activeId === 'learn-cms' ? (
            <div className="account-panel-body">
              {paneView === 'edit' ? (
                <LearnAdminEditPage
                  embedded
                  slug={panePost === 'new' ? undefined : panePost || undefined}
                  forceNew={panePost === 'new'}
                  onBack={() => setPane('overview')}
                  onSaved={(nextSlug) => setPane('edit', nextSlug)}
                />
              ) : (
                <LearnAdminPage
                  embedded
                  onCreate={() => setPane('edit', 'new')}
                  onEdit={(nextSlug) => setPane('edit', nextSlug)}
                />
              )}
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
