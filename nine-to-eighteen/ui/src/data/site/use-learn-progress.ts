/** Learn progress keyed by site JWT (db_9to18). */

import { useCallback, useEffect, useState } from 'react'
import {
  siteGetLearnProgress,
  siteSetLearnProgress,
  type SiteLearnProgressItem,
} from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

export function useSiteLearnProgress(): {
  items: SiteLearnProgressItem[]
  completedSlugs: Set<string>
  isReady: boolean
  isAuthed: boolean
  refresh: () => Promise<void>
  setCompleted: (slug: string, completed: boolean) => Promise<void>
} {
  const [items, setItems] = useState<SiteLearnProgressItem[]>([])
  const [isReady, setIsReady] = useState(false)
  const isAuthed = Boolean(getSiteAuthSession()?.accessToken)

  const refresh = useCallback(async () => {
    if (!getSiteAuthSession()?.accessToken) {
      setItems([])
      setIsReady(true)
      return
    }
    try {
      const next = await siteGetLearnProgress()
      setItems(next)
    } catch {
      setItems([])
    } finally {
      setIsReady(true)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const setCompleted = useCallback(
    async (slug: string, completed: boolean) => {
      await siteSetLearnProgress(slug, completed)
      await refresh()
    },
    [refresh],
  )

  return {
    items,
    completedSlugs: new Set(items.map((item) => item.slug)),
    isReady,
    isAuthed,
    refresh,
    setCompleted,
  }
}

export function progressPercent(completed: number, total: number): number {
  if (total <= 0) {
    return 0
  }
  return Math.round((completed / total) * 100)
}
