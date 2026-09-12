import { FormEvent, useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { AdminJumpNav } from '@/components/admin-jump-nav'
import { PageShell } from '@/components/page-shell'
import {
  siteAdminListApps,
  siteAssignAdmin,
  siteCreateApp,
  siteDeleteApp,
  siteDeletePost,
  siteGetApp,
  siteGetLearningMap,
  siteGetPromo,
  siteListContacts,
  siteListPosts,
  siteListUsers,
  sitePatchApp,
  sitePatchContact,
  sitePatchUser,
  siteReorderApps,
  siteResetLearningMap,
  siteSaveLearningMap,
  siteSavePost,
  siteSavePromo,
  siteUnassignAdmin,
  type SiteAdminUser,
  type SiteApp,
  type SiteContact,
  type SiteLearningMap,
  type SitePost,
} from '@/data/site/site-api'
import {
  canManageApp,
  getSiteAuthSession,
  isSuperAdmin,
  refreshSiteAuthSession,
} from '@/data/site/site-auth'
import {
  downloadSitePostFile,
  parseSitePostFile,
  readTextFile,
} from '@/data/site/post-file'
import { DEFAULT_SITE_PROMO, normalizeSitePromo, type SitePromo } from '@/data/promo'
import { StructuredPostEditor } from '@/components/structured-post-editor'
import {
  EMPTY_STRUCTURED_POST,
  legacyBodyToStructured,
  parsePostBody,
  serializeStructuredPost,
  type StructuredPost,
  validateStructuredPost,
} from '@/data/site/structured-post'

function AdminFrame({
  embedded,
  children,
}: {
  embedded: boolean
  children: ReactNode
}) {
  if (embedded) {
    return <div className="account-embed">{children}</div>
  }
  return <PageShell variant="admin">{children}</PageShell>
}

function moveSlug(slugs: string[], index: number, delta: number): string[] | null {
  const next = index + delta
  if (next < 0 || next >= slugs.length) {
    return null
  }
  const copy = [...slugs]
  const [item] = copy.splice(index, 1)
  copy.splice(next, 0, item)
  return copy
}

export type SiteAdminPageProps = {
  embedded?: boolean
  onOpenApp?: (slug: string) => void
}

export function SiteAdminPage({ embedded = false, onOpenApp }: SiteAdminPageProps = {}) {
  const [session, setSession] = useState(() => getSiteAuthSession())
  const [authReady, setAuthReady] = useState(false)
  const [promo, setPromo] = useState<SitePromo>(DEFAULT_SITE_PROMO)
  const [curatedText, setCuratedText] = useState('')
  const [learningMapMeta, setLearningMapMeta] = useState<SiteLearningMap | null>(null)
  const [mapFileName, setMapFileName] = useState('')
  const mapFileRef = useRef<HTMLInputElement>(null)
  const [apps, setApps] = useState<SiteApp[]>([])
  const [contacts, setContacts] = useState<SiteContact[]>([])
  const [users, setUsers] = useState<SiteAdminUser[]>([])
  const [assignUser, setAssignUser] = useState('')
  const [assignApp, setAssignApp] = useState('learn')
  const [newSlug, setNewSlug] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [orderDirty, setOrderDirty] = useState(false)

  useEffect(() => {
    let cancelled = false
    void refreshSiteAuthSession()
      .then((next) => {
        if (!cancelled) setSession(next)
      })
      .catch(() => {
        if (!cancelled) setSession(getSiteAuthSession())
      })
      .finally(() => {
        if (!cancelled) setAuthReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function reloadApps() {
    const nextApps = await siteAdminListApps()
    setApps(nextApps)
    setOrderDirty(false)
    if (nextApps.length > 0) {
      setAssignApp((prev) =>
        nextApps.some((app) => app.slug === prev) ? prev : nextApps[0].slug,
      )
    }
  }

  async function reloadOps() {
    const [nextContacts, nextUsers] = await Promise.all([siteListContacts(), siteListUsers()])
    setContacts(nextContacts)
    setUsers(nextUsers)
  }

  useEffect(() => {
    if (!authReady || !isSuperAdmin(session)) {
      return
    }
    let cancelled = false
    void (async () => {
      try {
        const nextApps = await siteAdminListApps()
        if (cancelled) return
        setApps(nextApps)
        setOrderDirty(false)
        if (nextApps.length > 0) {
          setAssignApp((prev) =>
            nextApps.some((app) => app.slug === prev) ? prev : nextApps[0].slug,
          )
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить плашки')
        }
      }
      try {
        const raw = await siteGetPromo()
        if (cancelled) return
        const nextPromo = normalizeSitePromo(raw as Partial<SitePromo>)
        setPromo(nextPromo)
        setCuratedText((nextPromo.curatedKeys || []).join('\n'))
      } catch {
        /* promo optional on load */
      }
      try {
        const mapMeta = await siteGetLearningMap()
        if (!cancelled) {
          setLearningMapMeta(mapMeta)
        }
      } catch {
        /* map meta optional */
      }
      try {
        await reloadOps()
      } catch (err) {
        if (!cancelled) {
          setError((prev) =>
            prev || (err instanceof Error ? err.message : 'Не удалось загрузить контакты/пользователей'),
          )
        }
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once when auth ready
  }, [authReady, session])

  if (!authReady) {
    return (
      <AdminFrame embedded={embedded}>
        <p className="learn-section-note">Проверка прав…</p>
      </AdminFrame>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: '/admin' }} />
  }
  if (!isSuperAdmin(session)) {
    return (
      <AdminFrame embedded={embedded}>
        <p className="learn-admin-error">Нужна роль супер-админа</p>
        {embedded ? null : <Link to="/account">В кабинет</Link>}
      </AdminFrame>
    )
  }

  async function savePromo(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setError('')
    try {
      const curatedKeys = curatedText
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.includes('/'))
        .slice(0, 5)
      const saved = await siteSavePromo({
        enabled: promo.enabled,
        eyebrow: promo.eyebrow,
        curatedKeys,
        serviceSlug: promo.serviceSlug || 'copyparse',
        title: promo.title || promo.eyebrow,
        body: promo.body || promo.eyebrow,
        ctaLabel: promo.ctaLabel || 'Подробнее',
        ctaHref: promo.ctaHref || '/',
      })
      const nextPromo = normalizeSitePromo(saved as Partial<SitePromo>)
      setPromo(nextPromo)
      setCuratedText((nextPromo.curatedKeys || []).join('\n'))
      setMessage('Спотлайт сохранён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  async function uploadLearningMap(file: File) {
    setMessage('')
    setError('')
    setBusy(true)
    try {
      const text = await readTextFile(file)
      if (!text.trim()) {
        throw new Error('Файл пустой')
      }
      const saved = await siteSaveLearningMap(text)
      setLearningMapMeta(saved)
      setMapFileName(file.name)
      setMessage(`Карта обновлена из «${file.name}» (${saved.chars} символов)`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить карту')
    } finally {
      setBusy(false)
      if (mapFileRef.current) {
        mapFileRef.current.value = ''
      }
    }
  }

  async function resetLearningMap() {
    if (!window.confirm('Сбросить карту к встроенному файлу в UI?')) {
      return
    }
    setMessage('')
    setError('')
    setBusy(true)
    try {
      const saved = await siteResetLearningMap()
      setLearningMapMeta(saved)
      setMapFileName('')
      setMessage('Карта сброшена к встроенной')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сбросить карту')
    } finally {
      setBusy(false)
    }
  }

  async function assign(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setError('')
    try {
      await siteAssignAdmin({ username: assignUser.trim(), app_slug: assignApp })
      await reloadOps()
      setMessage(`Назначен админ сервиса: ${assignUser} → ${assignApp}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  async function unassign(username: string, appSlug: string) {
    setBusy(true)
    setMessage('')
    setError('')
    try {
      await siteUnassignAdmin({ username, app_slug: appSlug })
      await reloadOps()
      setMessage(`Снят админ: ${username} · ${appSlug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  async function createTile(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setError('')
    setBusy(true)
    try {
      await siteCreateApp({
        slug: newSlug.trim().toLowerCase(),
        title: newTitle.trim(),
        is_visible: true,
      })
      setNewSlug('')
      setNewTitle('')
      await reloadApps()
      setMessage('Плашка создана')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  function moveApp(index: number, delta: number) {
    const nextSlugs = moveSlug(
      apps.map((a) => a.slug),
      index,
      delta,
    )
    if (!nextSlugs) {
      return
    }
    const bySlug = new Map(apps.map((app) => [app.slug, app]))
    const nextApps = nextSlugs
      .map((slug, orderIndex) => {
        const app = bySlug.get(slug)
        if (!app) {
          return null
        }
        return { ...app, sortOrder: orderIndex + 1 }
      })
      .filter((app): app is SiteApp => app != null)
    setApps(nextApps)
    setOrderDirty(true)
    setMessage('')
    setError('')
  }

  async function saveAppOrder() {
    if (!orderDirty || apps.length === 0) {
      return
    }
    setBusy(true)
    setMessage('')
    setError('')
    try {
      const nextApps = await siteReorderApps(apps.map((app) => app.slug))
      setApps(nextApps)
      setOrderDirty(false)
      setMessage('Порядок плашек сохранён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения порядка')
    } finally {
      setBusy(false)
    }
  }

  async function toggleVisible(app: SiteApp) {
    setBusy(true)
    setMessage('')
    setError('')
    try {
      await sitePatchApp(app.slug, { is_visible: !app.isVisible })
      await reloadApps()
      setMessage(app.isVisible ? `Скрыта: ${app.slug}` : `Показана: ${app.slug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  async function removeApp(app: SiteApp) {
    if (!window.confirm(`Удалить плашку «${app.title}» (${app.slug}) и все её статьи?`)) {
      return
    }
    setBusy(true)
    setMessage('')
    setError('')
    try {
      await siteDeleteApp(app.slug)
      await reloadApps()
      setMessage(`Удалена: ${app.slug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AdminFrame embedded={embedded}>
      {embedded ? null : (
        <Link to="/account" className="back-link">
          ← Кабинет
        </Link>
      )}
      {embedded ? null : (
        <header className="learn-header">
          <p className="learn-eyebrow">супер-админ</p>
          <h1 className="learn-title">Админка сайта</h1>
          <p className="learn-lead">
            Состав и порядок плашек, статьи всех сервисов, спотлайт, карта обучения (MD), назначение
            админов. Учебные выпуски Learn — в{' '}
            <Link to="/game/learn/admin">/game/learn/admin</Link> (вход CopyParse).
          </p>
        </header>
      )}

      <AdminJumpNav
        showGlobal={!embedded}
        serviceItems={apps.map((app) => ({
          id: `svc-${app.slug}`,
          label: app.emoji ? `${app.emoji} ${app.title}` : app.title,
          href: embedded
            ? `/account?section=${encodeURIComponent(`app:${app.slug}`)}&view=admin`
            : `/admin/apps/${app.slug}`,
        }))}
        items={[
          { id: 'admin-tiles', label: 'Плашки' },
          { id: 'admin-promo', label: 'Спотлайт' },
          { id: 'admin-learning-map', label: 'Карта (MD)' },
          { id: 'admin-contacts', label: 'Контакты' },
          { id: 'admin-users', label: 'Пользователи' },
          { id: 'admin-assign', label: 'Админы сервисов' },
        ]}
      />

      <section id="admin-tiles" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Плашки: состав и порядок</h2>
        <p className="learn-section-note">
          ↑↓ меняют порядок только в списке; чтобы зафиксировать на главной, нажмите «Сохранить
          порядок плашек». «Скрыть» убирает с витрины без удаления; «Править» — статьи и метаданные.
        </p>
        {apps.length === 0 ? (
          <p className="learn-section-note">
            Список плашек пуст или не загрузился. Обновите страницу; если пусто снова — проверьте
            core и таблицу <code>site_apps</code>.
          </p>
        ) : null}
        <div className="learn-admin-actions" style={{ marginBottom: '0.75rem' }}>
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy || !orderDirty || apps.length === 0}
            onClick={() => void saveAppOrder()}
          >
            Сохранить порядок плашек
          </button>
          {orderDirty ? (
            <span className="learn-section-note">Есть несохранённые изменения порядка</span>
          ) : null}
        </div>
        <ul className="learn-admin-list">
          {apps.map((app, index) => (
            <li key={app.slug} className="learn-admin-row">
              <div className="learn-admin-row-main">
                <span className="learn-admin-row-title">
                  {app.emoji ? `${app.emoji} ` : ''}
                  {app.title}
                  {!app.isVisible ? ' · скрыта' : ''}
                </span>
                <span className="learn-section-note">
                  #{index + 1} · {app.slug}
                </span>
              </div>
              <div className="learn-admin-row-actions">
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy || index === 0}
                  onClick={() => moveApp(index, -1)}
                >
                  ↑
                </button>
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy || index === apps.length - 1}
                  onClick={() => moveApp(index, 1)}
                >
                  ↓
                </button>
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy}
                  onClick={() => void toggleVisible(app)}
                >
                  {app.isVisible ? 'Скрыть' : 'Показать'}
                </button>
                {onOpenApp ? (
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    onClick={() => onOpenApp(app.slug)}
                  >
                    Править
                  </button>
                ) : (
                  <Link to={`/admin/apps/${app.slug}`} className="learn-admin-btn learn-admin-btn-primary">
                    Править
                  </Link>
                )}
                <button
                  type="button"
                  className="learn-admin-link learn-admin-danger"
                  disabled={busy}
                  onClick={() => void removeApp(app)}
                >
                  Удалить
                </button>
              </div>
            </li>
          ))}
        </ul>
        <form className="learn-admin-form" onSubmit={createTile} style={{ marginTop: '1.25rem' }}>
          <h3 className="learn-panel-heading">Новая плашка</h3>
          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>Slug</span>
              <input
                value={newSlug}
                onChange={(e) => setNewSlug(e.target.value)}
                pattern="[a-z0-9][a-z0-9_-]*"
                required
                placeholder="my-service"
              />
            </label>
            <label className="learn-admin-field">
              <span>Название</span>
              <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} required />
            </label>
          </div>
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy}
          >
            Создать плашку
          </button>
        </form>
      </section>

      <section id="admin-promo" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Спотлайт</h2>
        <p className="learn-section-note">
          Пустой список ключей — авто (свежие статьи). Иначе до 5 строк вида{' '}
          <code>appSlug/postSlug</code>.
        </p>
        <form className="learn-admin-form" onSubmit={savePromo}>
          <label className="learn-admin-field">
            <span>
              <input
                type="checkbox"
                checked={promo.enabled}
                onChange={(e) => setPromo((p) => ({ ...p, enabled: e.target.checked }))}
              />{' '}
              Показывать карусель
            </span>
          </label>
          <label className="learn-admin-field">
            <span>Подпись</span>
            <input
              value={promo.eyebrow}
              onChange={(e) => setPromo((p) => ({ ...p, eyebrow: e.target.value }))}
              placeholder="Спотлайт · взаимное продвижение"
            />
          </label>
          <label className="learn-admin-field">
            <span>Ручной выбор (по одной на строку)</span>
            <textarea
              className="learn-admin-textarea"
              rows={4}
              value={curatedText}
              onChange={(e) => setCuratedText(e.target.value)}
              placeholder={'learn/about\nbowl/about'}
            />
          </label>
          {promo.items.length > 0 ? (
            <ul className="learn-admin-list">
              {promo.items.map((item) => (
                <li key={`${item.appSlug}-${item.postSlug}`} className="learn-admin-row">
                  <div className="learn-admin-row-main">
                    <span className="learn-admin-row-title">{item.title}</span>
                    <span className="learn-section-note">
                      {item.appSlug}/{item.postSlug} · {item.excerpt.slice(0, 80)}
                      {item.excerpt.length > 80 ? '…' : ''}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="learn-section-note">Пока нет карточек для карусели.</p>
          )}
          <button type="submit" className="learn-admin-btn learn-admin-btn-primary">
            Сохранить спотлайт
          </button>
        </form>
      </section>

      <section id="admin-learning-map" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Карта обучения (Markdown)</h2>
        <p className="learn-section-note">
          Загрузите <code>.md</code> outline (<code>#</code> / <code>##</code> / <code>###</code> /{' '}
          <code>-</code>) — карта на{' '}
          <Link to="/game/learning-map">/game/learning-map</Link> перерисуется для всех. Подходит
          файл из «Выгрузить MD» или Obsidian. Frontmatter и блок <code>%%…%%</code> отбрасываются.
        </p>
        <p className="learn-section-note">
          Сейчас:{' '}
          {learningMapMeta?.source === 'custom'
            ? `кастомная${learningMapMeta.updatedBy ? ` · ${learningMapMeta.updatedBy}` : ''}${
                learningMapMeta.updatedAt ? ` · ${learningMapMeta.updatedAt}` : ''
              } · ${learningMapMeta.chars} символов`
            : 'встроенная (бандл UI)'}
          {mapFileName ? ` · последний файл: ${mapFileName}` : ''}
        </p>
        <div className="learn-admin-actions" style={{ gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            ref={mapFileRef}
            type="file"
            accept=".md,text/markdown,text/plain"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) {
                void uploadLearningMap(file)
              }
            }}
          />
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy}
            onClick={() => mapFileRef.current?.click()}
          >
            Загрузить MD
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            disabled={busy || learningMapMeta?.source !== 'custom'}
            onClick={() => void resetLearningMap()}
          >
            Сбросить к встроенной
          </button>
          <Link to="/game/learning-map" className="learn-admin-btn">
            Открыть карту
          </Link>
        </div>
      </section>

      <section id="admin-contacts" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Контакты</h2>
        <ul className="learn-admin-list">
          {contacts.length === 0 ? (
            <li className="learn-section-note">Сообщений пока нет.</li>
          ) : (
            contacts.map((c) => (
              <li key={c.id} className="learn-admin-row">
                <div className="learn-admin-row-main">
                  <span className="learn-admin-row-title">
                    {c.name || 'Без имени'} · {c.email}
                  </span>
                  <span className="learn-section-note">
                    {c.status} · {c.appSlug || 'site'} · {c.createdAt}
                  </span>
                  <p className="learn-section-note">{c.message}</p>
                </div>
                <div className="learn-admin-row-actions">
                  {(['new', 'read', 'done'] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      className="learn-admin-btn"
                      disabled={busy || c.status === st}
                      onClick={() => {
                        void (async () => {
                          setBusy(true)
                          try {
                            await sitePatchContact(c.id, st)
                            await reloadOps()
                          } catch (err) {
                            setError(err instanceof Error ? err.message : 'Ошибка')
                          } finally {
                            setBusy(false)
                          }
                        })()
                      }}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </li>
            ))
          )}
        </ul>
      </section>

      <section id="admin-users" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Пользователи</h2>
        <ul className="learn-admin-list">
          {users.map((u) => (
            <li key={u.id} className="learn-admin-row">
              <div className="learn-admin-row-main">
                <span className="learn-admin-row-title">
                  {u.username}
                  {!u.isActive ? ' · выкл' : ''}
                </span>
                <span className="learn-section-note">
                  {u.email} · {u.siteRole}
                  {u.appAdmin.length ? ` · apps: ${u.appAdmin.join(', ')}` : ''}
                </span>
              </div>
              <div className="learn-admin-row-actions">
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy}
                  onClick={() => {
                    void (async () => {
                      setBusy(true)
                      try {
                        await sitePatchUser(u.id, {
                          site_role: u.siteRole === 'site_admin' ? 'user' : 'site_admin',
                        })
                        await reloadOps()
                        setMessage(`Роль обновлена: ${u.username}`)
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Ошибка')
                      } finally {
                        setBusy(false)
                      }
                    })()
                  }}
                >
                  {u.siteRole === 'site_admin' ? '→ user' : '→ site_admin'}
                </button>
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy}
                  onClick={() => {
                    void (async () => {
                      setBusy(true)
                      try {
                        await sitePatchUser(u.id, { is_active: !u.isActive })
                        await reloadOps()
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Ошибка')
                      } finally {
                        setBusy(false)
                      }
                    })()
                  }}
                >
                  {u.isActive ? 'Выкл' : 'Вкл'}
                </button>
                {u.appAdmin.map((slug) => (
                  <button
                    key={slug}
                    type="button"
                    className="learn-admin-link learn-admin-danger"
                    disabled={busy}
                    onClick={() => void unassign(u.username, slug)}
                  >
                    −{slug}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section id="admin-assign" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Назначить админа сервиса</h2>
        <form className="learn-admin-form" onSubmit={assign}>
          <label className="learn-admin-field">
            <span>Username</span>
            <input value={assignUser} onChange={(e) => setAssignUser(e.target.value)} required />
          </label>
          <label className="learn-admin-field">
            <span>Сервис</span>
            <select value={assignApp} onChange={(e) => setAssignApp(e.target.value)} required>
              {apps.map((app) => (
                <option key={app.slug} value={app.slug}>
                  {app.title} ({app.slug})
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="learn-admin-btn learn-admin-btn-primary">
            Назначить
          </button>
        </form>
      </section>

      {message ? <p className="learn-admin-ok">{message}</p> : null}
      {error ? <p className="learn-admin-error">{error}</p> : null}
    </AdminFrame>
  )
}

export type AppAdminPageProps = {
  embedded?: boolean
  slug?: string
  onOpenPublic?: () => void
  onOpenPost?: (postSlug: string) => void
}

export function AppAdminPage({
  embedded = false,
  slug: slugProp,
  onOpenPublic,
  onOpenPost,
}: AppAdminPageProps = {}) {
  const { slug: slugParam = '' } = useParams()
  const slug = slugProp || slugParam
  const [session, setSession] = useState(() => getSiteAuthSession())
  const [authReady, setAuthReady] = useState(false)
  const [app, setApp] = useState<SiteApp | null>(null)
  const [posts, setPosts] = useState<SitePost[]>([])
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState('')
  const [description, setDescription] = useState('')
  const [accent, setAccent] = useState('#2dd4bf')
  const [emoji, setEmoji] = useState('')
  const [externalHref, setExternalHref] = useState('')
  const [appPath, setAppPath] = useState('')
  const [isVisible, setIsVisible] = useState(true)
  const [postTitle, setPostTitle] = useState('')
  const [postBody, setPostBody] = useState('')
  const [postStructured, setPostStructured] = useState<StructuredPost>(EMPTY_STRUCTURED_POST)
  const [useStructured, setUseStructured] = useState(true)
  const [postSlug, setPostSlug] = useState('about')
  const [postPublished, setPostPublished] = useState(true)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const postFileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let cancelled = false
    void refreshSiteAuthSession()
      .then((next) => {
        if (!cancelled) setSession(next)
      })
      .catch(() => {
        if (!cancelled) setSession(getSiteAuthSession())
      })
      .finally(() => {
        if (!cancelled) setAuthReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  function loadPostIntoForm(post: SitePost) {
    setPostSlug(post.slug)
    setPostTitle(post.title)
    setPostPublished(post.isPublished)
    const parsed = parsePostBody(post.body)
    if (parsed.structured) {
      setUseStructured(true)
      setPostStructured(parsed.structured)
      setPostBody(post.body)
    } else {
      setUseStructured(true)
      setPostStructured(legacyBodyToStructured(parsed.legacyMarkdown))
      setPostBody(post.body)
    }
  }

  function exportPostFile() {
    setError('')
    const body = useStructured ? serializeStructuredPost(postStructured) : postBody
    downloadSitePostFile({
      slug: postSlug,
      title: postTitle,
      body,
      isPublished: postPublished,
    })
    setMessage('Статья выгружена в .md')
  }

  async function importPostFile(file: File | null) {
    if (!file) {
      return
    }
    setMessage('')
    setError('')
    try {
      const text = await readTextFile(file)
      const parsed = parseSitePostFile(text, {
        slug: postSlug,
        title: postTitle,
        isPublished: postPublished,
      })
      if (parsed.slug) {
        setPostSlug(parsed.slug)
      }
      if (parsed.title) {
        setPostTitle(parsed.title)
      }
      setPostPublished(parsed.isPublished)
      const bodyParsed = parsePostBody(parsed.body)
      if (bodyParsed.structured) {
        setUseStructured(true)
        setPostStructured(bodyParsed.structured)
        setPostBody(parsed.body)
      } else {
        setUseStructured(true)
        setPostStructured(legacyBodyToStructured(bodyParsed.legacyMarkdown))
        setPostBody(parsed.body)
      }
      setMessage(`Загружено из «${file.name}» — проверьте и сохраните`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить файл')
    } finally {
      if (postFileInputRef.current) {
        postFileInputRef.current.value = ''
      }
    }
  }

  async function reload() {
    const [nextApp, nextPosts] = await Promise.all([siteGetApp(slug), siteListPosts(slug)])
    setApp(nextApp)
    setTitle(nextApp.title)
    setSubtitle(nextApp.subtitle)
    setDescription(nextApp.description)
    setAccent(nextApp.accent || '#2dd4bf')
    setEmoji(nextApp.emoji || '')
    setExternalHref(nextApp.externalHref || '')
    setAppPath(nextApp.appPath || '')
    setIsVisible(nextApp.isVisible)
    setPosts(nextPosts)
    return nextPosts
  }

  useEffect(() => {
    if (!authReady || !canManageApp(slug, session)) {
      return
    }
    void reload()
      .then((nextPosts) => {
        const current = nextPosts.find((p) => p.slug === postSlug) || nextPosts[0]
        if (current) {
          loadPostIntoForm(current)
        }
      })
      .catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once per slug after auth
  }, [slug, authReady, session])

  if (!authReady) {
    return (
      <AdminFrame embedded={embedded}>
        <p className="learn-section-note">Проверка прав…</p>
      </AdminFrame>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: `/admin/apps/${slug}` }} />
  }
  if (!canManageApp(slug, session)) {
    return (
      <AdminFrame embedded={embedded}>
        <p className="learn-admin-error">Нет прав на сервис {slug}</p>
      </AdminFrame>
    )
  }

  async function saveTile(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setError('')
    setBusy(true)
    try {
      const saved = await sitePatchApp(slug, {
        title,
        subtitle,
        description,
        accent,
        emoji,
        external_href: externalHref,
        app_path: appPath,
        is_visible: isVisible,
      })
      setApp(saved)
      setMessage('Плашка и страница сервиса сохранены')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  async function savePost(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    setError('')
    const body = useStructured ? serializeStructuredPost(postStructured) : postBody
    if (useStructured) {
      const issues = validateStructuredPost(postStructured)
      if (issues.length > 0 && postPublished) {
        setError(`Перед публикацией: ${issues.join('; ')}`)
        return
      }
    }
    setBusy(true)
    try {
      await siteSavePost(slug, postSlug, {
        slug: postSlug,
        title: postTitle,
        body,
        is_published: postPublished,
      })
      const nextPosts = await reload()
      const current = nextPosts.find((p) => p.slug === postSlug)
      if (current) {
        loadPostIntoForm(current)
      }
      setMessage('Статья сохранена')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  async function removePost(targetSlug: string) {
    if (!window.confirm(`Удалить статью «${targetSlug}»?`)) {
      return
    }
    setBusy(true)
    setMessage('')
    setError('')
    try {
      await siteDeletePost(slug, targetSlug)
      const nextPosts = await reload()
      if (nextPosts[0]) {
        loadPostIntoForm(nextPosts[0])
      } else {
        setPostSlug('about')
        setPostTitle('')
        setPostBody('')
        setPostStructured(EMPTY_STRUCTURED_POST)
        setUseStructured(true)
        setPostPublished(true)
      }
      setMessage(`Удалена статья ${targetSlug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setBusy(false)
    }
  }

  function startNewPost() {
    setPostSlug('')
    setPostTitle('')
    setPostBody('')
    setPostStructured(EMPTY_STRUCTURED_POST)
    setUseStructured(true)
    setPostPublished(true)
    setMessage('')
    setError('')
  }

  return (
    <AdminFrame embedded={embedded}>
      {embedded ? null : (
        <Link to={isSuperAdmin(session) ? '/admin' : `/app/${slug}`} className="back-link">
          ← {isSuperAdmin(session) ? 'Админка сайта' : `Страница · ${app?.title || slug}`}
        </Link>
      )}
      {embedded ? null : (
        <header className="learn-header">
          <p className="learn-eyebrow">
            {isSuperAdmin(session) ? 'супер-админ' : 'кабинет владельца сервиса'}
          </p>
          <h1 className="learn-title">Владелец · {app?.title || slug}</h1>
          <p className="learn-lead">
            Плашка на главной ведёт сюда на публичную страницу сервиса. Здесь — описание, ссылки на
            приложение и блог в едином формате статей.
          </p>
        </header>
      )}

      {embedded ? null : (
        <AdminJumpNav
          serviceItems={Array.from(
            new Set([...(session.appAdmin || []), slug]),
          ).map((appSlug) => ({
            id: `svc-${appSlug}`,
            label: appSlug === slug && app?.title ? app.title : appSlug,
            href: `/admin/apps/${appSlug}`,
          }))}
          items={[
            { id: 'app-tile', label: 'Описание' },
            { id: 'app-posts', label: 'Блог' },
            { id: 'app-public', label: 'Открыть сервис', href: `/app/${slug}` },
            { id: 'app-account', label: 'Раздел в кабинете', href: `/account?section=app:${slug}` },
          ]}
        />
      )}

      <section id="app-tile" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Описание сервиса и плашка</h2>
        <p className="learn-section-note">
          Внешняя ссылка и внутренний путь не меняют клик по плашке на главной — они показываются
          кнопками на странице сервиса.
        </p>
        <form className="learn-admin-form" onSubmit={saveTile}>
          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>Название</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label className="learn-admin-field">
              <span>Подзаголовок</span>
              <input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
            </label>
            <label className="learn-admin-field">
              <span>Emoji</span>
              <input value={emoji} onChange={(e) => setEmoji(e.target.value)} />
            </label>
            <label className="learn-admin-field">
              <span>Accent</span>
              <input value={accent} onChange={(e) => setAccent(e.target.value)} />
            </label>
            <label className="learn-admin-field">
              <span>Внешняя ссылка</span>
              <input value={externalHref} onChange={(e) => setExternalHref(e.target.value)} />
            </label>
            <label className="learn-admin-field">
              <span>Внутренний путь</span>
              <input value={appPath} onChange={(e) => setAppPath(e.target.value)} />
            </label>
          </div>
          <label className="learn-admin-field">
            <span>Описание</span>
            <textarea
              className="learn-admin-textarea"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <label className="learn-admin-field">
            <span>
              <input
                type="checkbox"
                checked={isVisible}
                onChange={(e) => setIsVisible(e.target.checked)}
              />{' '}
              Показывать плашку на главной
            </span>
          </label>
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy}
          >
            Сохранить плашку
          </button>
        </form>
      </section>

      <section id="app-posts" className="learn-schedule admin-jump-target">
        <h2 className="learn-section-title">Статьи блога</h2>
        <div className="learn-admin-actions">
          <button type="button" className="learn-admin-btn learn-admin-btn-primary" onClick={startNewPost}>
            Новая статья
          </button>
          {onOpenPublic ? (
            <button type="button" className="learn-admin-btn" onClick={onOpenPublic}>
              Открыть страницу сервиса
            </button>
          ) : (
            <Link to={`/app/${slug}`} className="learn-admin-btn">
              Открыть страницу сервиса
            </Link>
          )}
        </div>
        <ul className="learn-admin-list">
          {posts.map((post) => (
            <li key={post.id} className="learn-admin-row">
              <div className="learn-admin-row-main">
                <span className="learn-admin-row-title">{post.title}</span>
                <span className="learn-section-note">
                  {post.slug}
                  {!post.isPublished ? ' · черновик' : ''}
                </span>
              </div>
              <div className="learn-admin-row-actions">
                <button
                  type="button"
                  className="learn-admin-link"
                  onClick={() => loadPostIntoForm(post)}
                >
                  Править
                </button>
                {onOpenPost ? (
                  <button
                    type="button"
                    className="learn-admin-link"
                    onClick={() => onOpenPost(post.slug)}
                  >
                    Открыть
                  </button>
                ) : (
                  <Link to={`/app/${slug}/${post.slug}`} className="learn-admin-link">
                    Открыть
                  </Link>
                )}
                <button
                  type="button"
                  className="learn-admin-link learn-admin-danger"
                  disabled={busy}
                  onClick={() => void removePost(post.slug)}
                >
                  Удалить
                </button>
              </div>
            </li>
          ))}
        </ul>

        <form className="learn-admin-form" onSubmit={savePost} style={{ marginTop: '1.25rem' }}>
          <h3 className="learn-panel-heading">Редактор статьи</h3>
          <div className="learn-admin-actions" style={{ marginBottom: '0.75rem' }}>
            <button
              type="button"
              className="learn-admin-btn"
              onClick={exportPostFile}
              disabled={busy}
            >
              Скачать .md
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => postFileInputRef.current?.click()}
            >
              Загрузить .md
            </button>
            <input
              ref={postFileInputRef}
              type="file"
              accept=".md,.markdown,.txt,text/markdown,text/plain"
              hidden
              onChange={(e) => void importPostFile(e.target.files?.[0] || null)}
            />
          </div>
          <p className="learn-section-note" style={{ marginTop: 0 }}>
            Файл: YAML frontmatter (slug, title, published) + тело статьи (JSON единого формата или
            markdown). Загрузка заполняет форму; сохранение в БД — отдельно.
          </p>
          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>Slug</span>
              <input value={postSlug} onChange={(e) => setPostSlug(e.target.value)} required />
            </label>
            <label className="learn-admin-field">
              <span>Заголовок</span>
              <input value={postTitle} onChange={(e) => setPostTitle(e.target.value)} required />
            </label>
          </div>
          <label className="learn-admin-field">
            <span>
              <input
                type="checkbox"
                checked={useStructured}
                onChange={(e) => setUseStructured(e.target.checked)}
              />{' '}
              Единый формат (введение / разделы / схемы / тест / anki)
            </span>
          </label>
          {useStructured ? (
            <StructuredPostEditor value={postStructured} onChange={setPostStructured} />
          ) : (
            <label className="learn-admin-field">
              <span>Текст (markdown)</span>
              <textarea
                className="learn-admin-textarea"
                rows={10}
                value={postBody}
                onChange={(e) => setPostBody(e.target.value)}
              />
            </label>
          )}
          <label className="learn-admin-field">
            <span>
              <input
                type="checkbox"
                checked={postPublished}
                onChange={(e) => setPostPublished(e.target.checked)}
              />{' '}
              Опубликована
            </span>
          </label>
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy}
          >
            Сохранить статью
          </button>
        </form>
      </section>

      {message ? <p className="learn-admin-ok">{message}</p> : null}
      {error ? <p className="learn-admin-error">{error}</p> : null}
    </AdminFrame>
  )
}
