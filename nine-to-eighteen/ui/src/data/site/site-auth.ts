/** 9to18 site auth session (separate from CopyParse / Learn admin). */

import { useEffect, useState } from 'react'

const AUTH_KEY = 'nine-to-eighteen-site-auth-v1'
/** Same-tab sync (storage event is cross-tab only). */
const AUTH_CHANGED_EVENT = 'nine-to-eighteen-site-auth'

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

function notifyAuthChanged(): void {
  if (!isBrowser()) {
    return
  }
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
}

/** Decode JWT payload without verifying signature (exp check only). */
function readJwtExpSeconds(token: string): number | null {
  const parts = token.split('.')
  if (parts.length < 2) {
    return null
  }
  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
    const json = atob(padded)
    const payload = JSON.parse(json) as { exp?: unknown }
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

export function isSiteAccessTokenExpired(token: string, skewSeconds = 30): boolean {
  const exp = readJwtExpSeconds(token)
  if (exp == null) {
    return false
  }
  return Date.now() / 1000 >= exp - skewSeconds
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
    if (isSiteAccessTokenExpired(parsed.accessToken)) {
      window.localStorage.removeItem(AUTH_KEY)
      notifyAuthChanged()
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
  notifyAuthChanged()
}

export function clearSiteAuthSession(): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.removeItem(AUTH_KEY)
  notifyAuthChanged()
}

/** Drop stale session after API 401 (Token expired / Invalid token). */
export function clearSiteAuthSessionOnAuthFailure(status: number, detail?: string): void {
  if (status !== 401) {
    return
  }
  const text = (detail || '').toLowerCase()
  const isAuthFailure =
    text.includes('token expired') ||
    text.includes('invalid token') ||
    text.includes('authorization required') ||
    text.includes('user not found')
  if (!isAuthFailure && text) {
    return
  }
  if (!getSiteAccessTokenRaw()) {
    return
  }
  clearSiteAuthSession()
}

function getSiteAccessTokenRaw(): string | null {
  if (!isBrowser()) {
    return null
  }
  try {
    const raw = window.localStorage.getItem(AUTH_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as Partial<SiteAuthSession>
    return parsed.accessToken || null
  } catch {
    return null
  }
}

export function getSiteAccessToken(): string | null {
  return getSiteAuthSession()?.accessToken || null
}

/**
 * Стабильная сессия для React-эффектов.
 * getSiteAuthSession() каждый вызов создаёт новый объект — нельзя класть в deps useEffect.
 */
export function useSiteAuthSession(): SiteAuthSession | null {
  const [session, setSession] = useState<SiteAuthSession | null>(() => getSiteAuthSession())

  useEffect(() => {
    const sync = () => {
      const next = getSiteAuthSession()
      setSession((prev) => {
        if (
          prev?.accessToken === next?.accessToken &&
          prev?.siteRole === next?.siteRole &&
          prev?.username === next?.username &&
          prev?.email === next?.email &&
          (prev?.appAdmin || []).join('\0') === (next?.appAdmin || []).join('\0')
        ) {
          return prev
        }
        return next
      })
    }
    sync()
    window.addEventListener('storage', sync)
    window.addEventListener(AUTH_CHANGED_EVENT, sync)
    return () => {
      window.removeEventListener('storage', sync)
      window.removeEventListener(AUTH_CHANGED_EVENT, sync)
    }
  }, [])

  return session
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
  const { siteGetMe, SiteApiError } = await import('@/data/site/site-api')
  try {
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
  } catch (err) {
    if (err instanceof SiteApiError && err.status === 401) {
      clearSiteAuthSession()
      return null
    }
    throw err
  }
}
