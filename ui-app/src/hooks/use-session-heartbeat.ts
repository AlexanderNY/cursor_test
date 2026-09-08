import { useEffect, useRef } from 'react'
import { authService } from '@/services/auth-service'

const SESSION_STORAGE_KEY = 'app_session_id'
const HEARTBEAT_INTERVAL_MS = 120_000

function getOrCreateSessionId(): string {
  const existing = sessionStorage.getItem(SESSION_STORAGE_KEY)
  if (existing && existing.length >= 8) {
    return existing
  }
  const id =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `sess-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
  sessionStorage.setItem(SESSION_STORAGE_KEY, id)
  return id
}

async function pingHeartbeat(): Promise<void> {
  try {
    await authService.sendActivityHeartbeat(getOrCreateSessionId())
  } catch {
    // Не мешаем работе UI, если учёт сеанса недоступен
  }
}

export function useSessionHeartbeat(isAuthenticated: boolean): void {
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    const clearTick = () => {
      if (intervalRef.current != null) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    const startTick = () => {
      clearTick()
      intervalRef.current = window.setInterval(() => {
        if (document.visibilityState === 'visible') {
          void pingHeartbeat()
        }
      }, HEARTBEAT_INTERVAL_MS)
    }

    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        void pingHeartbeat()
        startTick()
        return
      }
      clearTick()
    }

    if (document.visibilityState === 'visible') {
      void pingHeartbeat()
      startTick()
    }

    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      clearTick()
    }
  }, [isAuthenticated])
}
