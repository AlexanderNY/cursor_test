import { useMemo, useState } from 'react'
import {
  sitePatchUser,
  type SiteAdminUser,
  type SiteApp,
} from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

type SiteAdminUsersPanelProps = {
  users: SiteAdminUser[]
  apps: SiteApp[]
  busy: boolean
  onBusy: (next: boolean) => void
  onMessage: (text: string) => void
  onError: (text: string) => void
  onReload: () => Promise<void>
}

type Draft = {
  siteRole: 'user' | 'site_admin'
  isActive: boolean
  appAdmin: string[]
}

function sameApps(a: string[], b: string[]): boolean {
  if (a.length !== b.length) {
    return false
  }
  const left = [...a].sort()
  const right = [...b].sort()
  return left.every((slug, index) => slug === right[index])
}

function draftFromUser(user: SiteAdminUser): Draft {
  return {
    siteRole: user.siteRole,
    isActive: user.isActive,
    appAdmin: [...user.appAdmin],
  }
}

export function SiteAdminUsersPanel({
  users,
  apps,
  busy,
  onBusy,
  onMessage,
  onError,
  onReload,
}: SiteAdminUsersPanelProps) {
  const session = getSiteAuthSession()
  const selfUsername = (session?.username || '').toLowerCase()
  const [query, setQuery] = useState('')
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) {
      return users
    }
    return users.filter((user) => {
      const hay = `${user.username} ${user.email} ${user.siteRole} ${user.appAdmin.join(' ')}`
      return hay.toLowerCase().includes(needle)
    })
  }, [users, query])

  function draftFor(user: SiteAdminUser): Draft {
    return drafts[user.id] || draftFromUser(user)
  }

  function setDraft(user: SiteAdminUser, patch: Partial<Draft>) {
    setDrafts((prev) => {
      const base = prev[user.id] || draftFromUser(user)
      return {
        ...prev,
        [user.id]: {
          ...base,
          ...patch,
          appAdmin: patch.appAdmin ? [...patch.appAdmin] : base.appAdmin,
        },
      }
    })
  }

  function toggleApp(user: SiteAdminUser, slug: string) {
    const draft = draftFor(user)
    const next = draft.appAdmin.includes(slug)
      ? draft.appAdmin.filter((item) => item !== slug)
      : [...draft.appAdmin, slug]
    setDraft(user, { appAdmin: next })
  }

  function isDirty(user: SiteAdminUser): boolean {
    const draft = draftFor(user)
    return (
      draft.siteRole !== user.siteRole ||
      draft.isActive !== user.isActive ||
      !sameApps(draft.appAdmin, user.appAdmin)
    )
  }

  function isSelf(user: SiteAdminUser): boolean {
    return Boolean(selfUsername) && user.username.toLowerCase() === selfUsername
  }

  async function saveUser(user: SiteAdminUser) {
    const draft = draftFor(user)
    if (!isDirty(user)) {
      onMessage(`Нет изменений: ${user.username}`)
      return
    }
    if (isSelf(user) && draft.siteRole === 'user') {
      onError('Нельзя снять с себя роль супер-админа')
      return
    }
    if (isSelf(user) && !draft.isActive) {
      onError('Нельзя отключить свой аккаунт')
      return
    }
    onBusy(true)
    onMessage('')
    onError('')
    try {
      const updated = await sitePatchUser(user.id, {
        site_role: draft.siteRole,
        is_active: draft.isActive,
        app_admin: draft.appAdmin,
      })
      setDrafts((prev) => {
        const next = { ...prev }
        delete next[user.id]
        return next
      })
      await onReload()
      onMessage(
        `Полномочия сохранены: ${updated.username}` +
          (updated.siteRole === 'site_admin' ? ' · супер-админ' : '') +
          (updated.appAdmin.length ? ` · сервисы: ${updated.appAdmin.join(', ')}` : ''),
      )
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Не удалось сохранить полномочия')
    } finally {
      onBusy(false)
    }
  }

  function resetDraft(user: SiteAdminUser) {
    setDrafts((prev) => {
      const next = { ...prev }
      delete next[user.id]
      return next
    })
  }

  return (
    <section id="admin-users" className="learn-schedule admin-jump-target">
      <h2 className="learn-section-title">Полномочия пользователей</h2>
      <p className="learn-section-note">
        Супер-админ управляет ролью сайта, доступом к плашкам (админ сервиса) и активацией
        аккаунта. Админ сервиса правит описание, плашку и блог своего slug.
      </p>

      <label className="learn-admin-field" style={{ maxWidth: '28rem' }}>
        <span>Поиск</span>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="username, email, роль, slug сервиса"
        />
      </label>

      <p className="learn-section-note">
        Показано {filtered.length} из {users.length}
      </p>

      <ul className="admin-users-list">
        {filtered.map((user) => {
          const draft = draftFor(user)
          const dirty = isDirty(user)
          const open = expandedId === user.id
          const selfRow = isSelf(user)
          return (
            <li
              key={user.id}
              className={`admin-user-card${dirty ? ' is-dirty' : ''}${!draft.isActive ? ' is-off' : ''}`}
            >
              <div className="admin-user-card-head">
                <div>
                  <p className="learn-admin-row-title">
                    {user.username}
                    {selfRow ? ' · вы' : ''}
                    {!draft.isActive ? ' · выключен' : ''}
                  </p>
                  <p className="learn-section-note">
                    {user.email} ·{' '}
                    {draft.siteRole === 'site_admin' ? 'супер-админ' : 'пользователь'}
                    {draft.appAdmin.length
                      ? ` · админ сервисов: ${draft.appAdmin.join(', ')}`
                      : ' · без сервисов'}
                  </p>
                </div>
                <div className="mnemonic-chip-row">
                  <button
                    type="button"
                    className="learn-admin-btn"
                    onClick={() => setExpandedId(open ? null : user.id)}
                  >
                    {open ? 'Свернуть' : 'Права'}
                  </button>
                  {dirty ? (
                    <button
                      type="button"
                      className="learn-admin-btn learn-admin-btn-primary"
                      disabled={busy}
                      onClick={() => void saveUser(user)}
                    >
                      Сохранить
                    </button>
                  ) : null}
                </div>
              </div>

              {open ? (
                <div className="admin-user-card-body">
                  <label className="learn-admin-field">
                    <span>Роль на сайте</span>
                    <select
                      value={draft.siteRole}
                      disabled={busy || (selfRow && draft.siteRole === 'site_admin')}
                      onChange={(e) =>
                        setDraft(user, {
                          siteRole: e.target.value as 'user' | 'site_admin',
                        })
                      }
                    >
                      <option value="user">Пользователь</option>
                      <option value="site_admin">Супер-админ сайта</option>
                    </select>
                  </label>

                  <label className="admin-user-check">
                    <input
                      type="checkbox"
                      checked={draft.isActive}
                      disabled={busy || selfRow}
                      onChange={(e) => setDraft(user, { isActive: e.target.checked })}
                    />
                    <span>Аккаунт активен</span>
                  </label>

                  <fieldset className="admin-user-apps">
                    <legend>Админ сервисов (плашки)</legend>
                    <p className="learn-section-note">
                      Отметьте сервисы, которыми пользователь может управлять (описание, блог,
                      плашка).
                    </p>
                    {apps.length === 0 ? (
                      <p className="learn-section-note">Нет плашек в каталоге.</p>
                    ) : (
                      <ul className="admin-user-app-grid">
                        {apps.map((app) => {
                          const checked = draft.appAdmin.includes(app.slug)
                          return (
                            <li key={app.slug}>
                              <label className={`admin-user-check${checked ? ' is-on' : ''}`}>
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  disabled={busy}
                                  onChange={() => toggleApp(user, app.slug)}
                                />
                                <span>
                                  <strong>{app.title}</strong>
                                  <span className="learn-section-note"> {app.slug}</span>
                                </span>
                              </label>
                            </li>
                          )
                        })}
                      </ul>
                    )}
                  </fieldset>

                  <div className="mnemonic-chip-row">
                    <button
                      type="button"
                      className="learn-admin-btn learn-admin-btn-primary"
                      disabled={busy || !dirty}
                      onClick={() => void saveUser(user)}
                    >
                      Сохранить полномочия
                    </button>
                    <button
                      type="button"
                      className="learn-admin-btn"
                      disabled={busy || !dirty}
                      onClick={() => resetDraft(user)}
                    >
                      Отменить правки
                    </button>
                  </div>
                </div>
              ) : null}
            </li>
          )
        })}
      </ul>

      {filtered.length === 0 ? (
        <p className="learn-section-note">Никого не найдено по запросу.</p>
      ) : null}
    </section>
  )
}
