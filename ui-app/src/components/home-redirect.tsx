import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { smmService } from '@/services/smm-service'
import { RouteLoader } from '@/components/route-loader'

/**
 * After login / home: incomplete setup → onboarding (Telegram + first channel);
 * otherwise → create post so the first publish loop is one click away.
 */
export function HomeRedirect() {
  const [to, setTo] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const state = await smmService.onboardingState()
        if (cancelled) return
        if (!state.completed && !state.skipped) {
          setTo('/onboarding')
          return
        }
        setTo('/posts')
      } catch {
        if (!cancelled) setTo('/posts')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (!to) return <RouteLoader />
  return <Navigate to={to} replace />
}
