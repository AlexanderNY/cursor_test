import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { notificationsService } from '@/services/notifications-service'
import { CloseIcon } from '@/components/icons'
import type { Notification } from '@/types/core'

const POLL_MS = 12_000
const DISMISSED_KEY = 'cp_dismissed_notifications'

function loadDismissed(): Set<number> {
  try {
    const raw = sessionStorage.getItem(DISMISSED_KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw) as unknown
    if (!Array.isArray(arr)) return new Set()
    return new Set(arr.filter((x): x is number => typeof x === 'number'))
  } catch {
    return new Set()
  }
}

function saveDismissed(ids: Set<number>) {
  sessionStorage.setItem(DISMISSED_KEY, JSON.stringify([...ids]))
}

export function NotificationToasts() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [dismissed, setDismissed] = useState<Set<number>>(() => loadDismissed())

  const load = useCallback(async () => {
    if (!user) return
    try {
      const response = await notificationsService.getNotifications()
      setNotifications(response.notifications || [])
    } catch {
      /* ignore poll errors */
    }
  }, [user])

  useEffect(() => {
    if (!user) return
    void load()
    const t = setInterval(() => void load(), POLL_MS)
    return () => clearInterval(t)
  }, [user, load])

  const visible = useMemo(
    () => notifications.filter((n) => !dismissed.has(n.id)),
    [notifications, dismissed],
  )

  function dismiss(id: number) {
    setDismissed((prev) => {
      const next = new Set(prev)
      next.add(id)
      saveDismissed(next)
      return next
    })
  }

  function handleBodyClick(e: React.MouseEvent<HTMLDivElement>) {
    const target = e.target as HTMLElement
    const anchor = target.closest('a')
    if (!anchor) return
    const href = anchor.getAttribute('href')
    if (href && href.startsWith('/')) {
      e.preventDefault()
      navigate(href)
    }
  }

  if (visible.length === 0) return null

  return (
    <div
      className="fixed top-20 right-4 z-[90] flex flex-col gap-2 w-[min(100vw-2rem,22rem)] pointer-events-none"
      role="region"
      aria-label="Оповещения"
      aria-live="polite"
    >
      {visible.map((n) => {
        const isAuth = n.type?.startsWith('tg_auth')
        return (
          <div
            key={n.id}
            className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg bg-[var(--bg-secondary)] ${
              isAuth
                ? 'border-amber-500/50 bg-amber-500/10'
                : 'border-[var(--border-color)]'
            }`}
            role="status"
          >
            <div
              className="flex-1 text-sm text-[var(--text-primary)] notification-content min-w-0"
              onClick={handleBodyClick}
              dangerouslySetInnerHTML={{ __html: n.message || '' }}
            />
            <button
              type="button"
              onClick={() => dismiss(n.id)}
              className="flex-shrink-0 p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
              aria-label="Закрыть"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
