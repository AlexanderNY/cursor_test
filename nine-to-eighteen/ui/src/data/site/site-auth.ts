/** 9to18 site auth session (separate from CopyParse / Learn admin). */

const AUTH_KEY = 'nine-to-eighteen-site-auth-v1'

/**
 * Роли контура 9to18:
 * - user — чтение всех опубликованных страниц и статей сервисов
 * - service_admin (через appAdmin[]) — плитка, страница и блог своих сервисов
 * - site_admin (супер-админ) — всё выше + любой сервис, спотлайт, назначение админов
 */
export type SiteRole = 'user' | 'site_admin'

export type SiteAuthSession = {
  accessToken: string
  siteRole: SiteRole
  username: string
  email: string
  /** Slug'и сервисов, где пользователь — админ сервиса (плашки). */
  appAdmin: string[]
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function getSiteAuthSession(): SiteAuthSession | null {
  if (!isBrowser()) {
    return null
  }
  const raw = window.localStorage.getItem(AUTH_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as Partial<SiteAuthSession>
    if (!parsed.accessToken) {
      return null
    }
    return {
      accessToken: parsed.accessToken,
      siteRole: parsed.siteRole === 'site_admin' ? 'site_admin' : 'user',
      username: parsed.username || '',
      email: parsed.email || '',
      appAdmin: Array.isArray(parsed.appAdmin) ? parsed.appAdmin.map(String) : [],
    }
  } catch {
    return null
  }
}

export function setSiteAuthSession(session: SiteAuthSession): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(AUTH_KEY, JSON.stringify(session))
}

export function clearSiteAuthSession(): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.removeItem(AUTH_KEY)
}

export function getSiteAccessToken(): string | null {
  return getSiteAuthSession()?.accessToken || null
}

/** Супер-админ сайта (в БД: site_role = site_admin). */
export function isSuperAdmin(session?: SiteAuthSession | null): boolean {
  const value = session ?? getSiteAuthSession()
  return value?.siteRole === 'site_admin'
}

/** @deprecated используйте isSuperAdmin */
export function isSiteAdmin(session?: SiteAuthSession | null): boolean {
  return isSuperAdmin(session)
}

/** Админ конкретного сервиса (плашки) или супер-админ. */
export function canManageApp(appSlug: string, session?: SiteAuthSession | null): boolean {
  const value = session ?? getSiteAuthSession()
  if (!value) {
    return false
  }
  if (isSuperAdmin(value)) {
    return true
  }
  return value.appAdmin.includes(appSlug)
}

export function getManagedAppSlugs(session?: SiteAuthSession | null): string[] {
  const value = session ?? getSiteAuthSession()
  if (!value) {
    return []
  }
  return value.appAdmin
}

export function describeSiteRole(session: SiteAuthSession): string {
  if (isSuperAdmin(session)) {
    return 'супер-админ'
  }
  if (session.appAdmin.length > 0) {
    return `админ сервиса (${session.appAdmin.join(', ')})`
  }
  return 'пользователь'
}

/** Подтянуть роль/права из GET /site/me (роль в БД важнее JWT). */
export async function refreshSiteAuthSession(): Promise<SiteAuthSession | null> {
  const current = getSiteAuthSession()
  if (!current?.accessToken) {
    return null
  }
  const { siteGetMe } = await import('@/data/site/site-api')
  const me = await siteGetMe()
  const next: SiteAuthSession = {
    accessToken: current.accessToken,
    siteRole: me.siteRole === 'site_admin' ? 'site_admin' : 'user',
    username: me.username,
    email: me.email,
    appAdmin: me.appAdmin || [],
  }
  setSiteAuthSession(next)
  return next
}
