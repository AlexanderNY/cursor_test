/** Light / dark theme for 9to18.ru (persisted in localStorage). */

const STORAGE_KEY = 'nine-to-eighteen-theme-v1'

export type ThemeMode = 'light' | 'dark'

type Listener = (theme: ThemeMode) => void

const listeners = new Set<Listener>()

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined'
}

export function getSystemTheme(): ThemeMode {
  if (!isBrowser()) {
    return 'dark'
  }
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

export function getStoredTheme(): ThemeMode | null {
  if (!isBrowser()) {
    return null
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (raw === 'light' || raw === 'dark') {
      return raw
    }
  } catch {
    /* ignore */
  }
  return null
}

export function getTheme(): ThemeMode {
  return getStoredTheme() ?? getSystemTheme()
}

export function applyTheme(theme: ThemeMode): void {
  if (!isBrowser()) {
    return
  }
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.style.colorScheme = theme
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* ignore */
  }
  listeners.forEach((listener) => listener(theme))
}

export function toggleTheme(): ThemeMode {
  const next: ThemeMode = getTheme() === 'dark' ? 'light' : 'dark'
  applyTheme(next)
  return next
}

export function subscribeTheme(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

/** Call once at app bootstrap (after DOM is ready). */
export function initTheme(): ThemeMode {
  const theme = getTheme()
  applyTheme(theme)
  return theme
}
