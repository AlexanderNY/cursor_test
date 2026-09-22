/** JWT session for Learn admin — uses 9to18 site JWT (site_admin). */

import {
  clearSiteAuthSession,
  getSiteAccessToken,
  getSiteAuthSession,
  isSuperAdmin,
  type SiteAuthSession,
} from '@/data/site/site-auth'

export type LearnAuthSession = {
  accessToken: string
  refreshToken: string
  role: string
  username: string
}

export function getLearnAuthSession(): LearnAuthSession | null {
  const site = getSiteAuthSession()
  if (!site?.accessToken || !isSuperAdmin(site)) {
    return null
  }
  return {
    accessToken: site.accessToken,
    refreshToken: '',
    role: 'admin',
    username: site.username,
  }
}

export function setLearnAuthSession(_session: LearnAuthSession): void {
  // Learn CMS uses site session; no separate store.
}

export function clearLearnAuthSession(): void {
  // Do not clear site session from Learn CMS alone.
}

export function getLearnAccessToken(): string | null {
  const site = getSiteAuthSession()
  if (!site || !isSuperAdmin(site)) {
    return null
  }
  return getSiteAccessToken()
}

export function canEditLearn(role?: string): boolean {
  if (role) {
    const value = role.toLowerCase()
    return value === 'admin' || value === 'author' || value === 'site_admin'
  }
  return isSuperAdmin()
}

export function learnSessionFromSite(session: SiteAuthSession | null): LearnAuthSession | null {
  if (!session || !isSuperAdmin(session)) {
    return null
  }
  return {
    accessToken: session.accessToken,
    refreshToken: '',
    role: 'admin',
    username: session.username,
  }
}

export function logoutLearnAndSite(): void {
  clearSiteAuthSession()
}
