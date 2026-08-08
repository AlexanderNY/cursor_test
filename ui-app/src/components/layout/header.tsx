import { useState, useEffect, useCallback, useRef } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { useTheme } from '@/contexts/theme-context'
import { useBrand } from '@/contexts/brand-context'
import { Button } from '@/components/ui'
import { smmService } from '@/services/smm-service'
import { topNavItems } from '@/config/nav'

const INBOX_COMMENT_POLL_MS = 25_000

export function Header() {
  const { logout } = useAuth()
  const { isDarkMode, toggleTheme } = useTheme()
  const { brands, selectedBrandId, setSelectedBrandId, selectedBrand } = useBrand()
  const navigate = useNavigate()
  const location = useLocation()
  const [newCommentCount, setNewCommentCount] = useState(0)
  const prevCommentCountRef = useRef(0)
  const commentNotifyReadyRef = useRef(false)

  const loadNewComments = useCallback(async () => {
    try {
      const res = await smmService.listInbox({
        brand_id: selectedBrandId ?? undefined,
        type: 'comment',
        status: 'new',
        limit: 50,
      })
      const count = res.items?.length ?? 0
      if (
        commentNotifyReadyRef.current &&
        count > prevCommentCountRef.current &&
        typeof Notification !== 'undefined' &&
        Notification.permission === 'granted'
      ) {
        new Notification('Новые комментарии', {
          body: `Непрочитанных: ${count}`,
          tag: 'inbox-comments-badge',
        })
      }
      prevCommentCountRef.current = count
      commentNotifyReadyRef.current = true
      setNewCommentCount(count)
    } catch {
      /* ignore badge errors */
    }
  }, [selectedBrandId])

  useEffect(() => {
    void loadNewComments()
    const interval = setInterval(() => void loadNewComments(), INBOX_COMMENT_POLL_MS)
    return () => clearInterval(interval)
  }, [loadNewComments])

  return (
    <header className="h-16 shrink-0 bg-[var(--bg-secondary)] border-b border-[var(--border-color)] flex items-center justify-between gap-4 px-6">
      <div className="flex items-center gap-4 min-w-0 flex-1">
        {brands.length > 0 && (
          <div className="flex items-center gap-2 shrink-0">
            <span
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: selectedBrand?.color ?? '#64748b' }}
            />
            <select
              aria-label="Brand switcher"
              className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 py-1.5 text-sm text-[var(--text-primary)] max-w-[160px]"
              value={selectedBrandId ?? ''}
              onChange={(e) =>
                setSelectedBrandId(e.target.value ? Number(e.target.value) : null)
              }
            >
              <option value="">All brands</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <nav className="flex items-center gap-1 min-w-0 overflow-x-auto" aria-label="Основное меню">
          {topNavItems.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path === '/profile' && location.pathname.startsWith('/profile'))
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 ${
                  isActive
                    ? 'bg-[var(--bg-tertiary)] text-primary-400'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
                }`}
              >
                <item.Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={() => navigate('/inbox?mode=comments')}
          className="relative p-2 rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors text-[var(--text-secondary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
          aria-label={
            newCommentCount > 0
              ? `Inbox comments, ${newCommentCount} new`
              : 'Inbox comments'
          }
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          {newCommentCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-amber-500 text-[10px] font-semibold text-white flex items-center justify-center">
              {newCommentCount > 99 ? '99+' : newCommentCount}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={toggleTheme}
          className="p-2 rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors text-[var(--text-secondary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
          aria-label={isDarkMode ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {isDarkMode ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        <Button variant="ghost" size="sm" onClick={logout}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Logout
        </Button>
      </div>
    </header>
  )
}
