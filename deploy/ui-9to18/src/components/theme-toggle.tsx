import { useEffect, useState } from 'react'
import {
  getTheme,
  subscribeTheme,
  toggleTheme,
  type ThemeMode,
} from '@/data/theme'

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>(() => getTheme())

  useEffect(() => subscribeTheme(setTheme), [])

  const isDark = theme === 'dark'
  const label = isDark ? 'Светлая тема' : 'Тёмная тема'

  return (
    <button
      type="button"
      className="site-nav-link theme-toggle"
      onClick={() => setTheme(toggleTheme())}
      aria-label={label}
      title={label}
    >
      <span className="theme-toggle-icon" aria-hidden>
        {isDark ? '☀' : '☾'}
      </span>
      <span className="theme-toggle-label">{isDark ? 'Светлая' : 'Тёмная'}</span>
    </button>
  )
}
