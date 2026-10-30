import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { forumService } from '@/services/forum-service'

const POLL_MS = 20_000

export function useForumUnreadCount(): number {
  const { user } = useAuth()
  const [count, setCount] = useState(0)

  const load = useCallback(async () => {
    if (!user) return
    try {
      setCount(await forumService.unreadCount())
    } catch {
      /* бейдж не должен ломать меню */
    }
  }, [user])

  useEffect(() => {
    if (!user) return
    void load()
    const timer = window.setInterval(() => void load(), POLL_MS)
    return () => window.clearInterval(timer)
  }, [user, load])

  return count
}
