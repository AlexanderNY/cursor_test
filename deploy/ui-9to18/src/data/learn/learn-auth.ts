/** JWT session for Learn admin (9to18). */

const AUTH_KEY = 'nine-to-eighteen-learn-auth-v1'

export type LearnAuthSession = {
  accessToken: string
  refreshToken: string
  role: string
  username: string
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function getLearnAuthSession(): LearnAuthSession | null {
  if (!isBrowser()) {
    return null
  }
  const raw = window.localStorage.getItem(AUTH_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as Partial<LearnAuthSession>
    if (!parsed.accessToken) {
      return null
    }
    return {
      accessToken: parsed.accessToken,
      refreshToken: parsed.refreshToken || '',
      role: parsed.role || 'guest',
      username: parsed.username || '',
    }
  } catch {
    return null
  }
}

export function setLearnAuthSession(session: LearnAuthSession): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(AUTH_KEY, JSON.stringify(session))
}

export function clearLearnAuthSession(): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.removeItem(AUTH_KEY)
}

export function getLearnAccessToken(): string | null {
  return getLearnAuthSession()?.accessToken || null
}

export function canEditLearn(role?: string): boolean {
  const value = (role || getLearnAuthSession()?.role || '').toLowerCase()
  return value === 'admin' || value === 'author'
}
