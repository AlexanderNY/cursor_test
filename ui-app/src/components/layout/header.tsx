import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { useTheme } from '@/contexts/theme-context'
import { Button } from '@/components/ui'
import { notificationsService } from '@/services/notifications-service'
import type { Notification } from '@/types/core'

const NOTIFICATIONS_POLL_INTERVAL_MS = 12_000

export function Header() {
  const { user, logout } = useAuth()
  const { isDarkMode, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const notificationRef = useRef<HTMLDivElement>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [currentNotificationIndex, setCurrentNotificationIndex] = useState(0)
  const [_isLoadingNotifications, setIsLoadingNotifications] = useState(false)

  const loadNotifications = useCallback(async () => {
    setIsLoadingNotifications(true)
    try {
      const response = await notificationsService.getNotifications()
      setNotifications(response.notifications || [])
      setCurrentNotificationIndex(0)
    } catch (error) {
      console.error('Failed to load notifications:', error)
      setNotifications([])
    } finally {
      setIsLoadingNotifications(false)
    }
  }, [])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  useEffect(() => {
    if (!user) return
    const interval = setInterval(loadNotifications, NOTIFICATIONS_POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [user, loadNotifications])

  function handleNextNotification() {
    if (notifications.length === 0) return
    setCurrentNotificationIndex((prev) => (prev + 1) % notifications.length)
  }

  function handlePrevNotification() {
    if (notifications.length === 0) return
    setCurrentNotificationIndex((prev) => (prev - 1 + notifications.length) % notifications.length)
  }

  const currentNotification = notifications[currentNotificationIndex]
  const isAuthNotification = currentNotification?.type?.startsWith('tg_auth')

  // Intercept clicks on internal <a> links inside notification HTML
  // so they use React Router (SPA navigation) instead of full page reload
  const handleNotificationClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const target = e.target as HTMLElement
      const anchor = target.closest('a')
      if (!anchor) return
      const href = anchor.getAttribute('href')
      if (href && href.startsWith('/')) {
        e.preventDefault()
        navigate(href)
      }
    },
    [navigate]
  )

  return (
    <header className="h-[115px] bg-[var(--bg-secondary)] border-b border-[var(--border-color)] flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        {/* Notifications Block */}
        {notifications.length > 0 && (
          <div
            role="region"
            aria-label="Notifications"
            aria-live="polite"
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border max-w-md ${
              isAuthNotification
                ? 'bg-amber-500/10 border-amber-500/50'
                : 'bg-[var(--bg-tertiary)] border-[var(--border-color)]'
            }`}
          >
            <button
              type="button"
              onClick={handlePrevNotification}
              disabled={notifications.length <= 1}
              className="p-1 rounded hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
              aria-label="Previous notification"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-[var(--text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <div
              ref={notificationRef}
              onClick={handleNotificationClick}
              className="flex-1 text-sm text-[var(--text-primary)] text-center px-2 notification-content"
              dangerouslySetInnerHTML={{ __html: currentNotification?.message || '' }}
            />
            
            <button
              type="button"
              onClick={handleNextNotification}
              disabled={notifications.length <= 1}
              className="p-1 rounded hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
              aria-label="Next notification"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-[var(--text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>
      
      <div className="flex items-center gap-3">
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


