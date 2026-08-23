import { useEffect, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { smmService } from '@/services/smm-service'
import type { OnboardingState } from '@/types/smm'

const WHITELIST_PREFIXES = [
  '/profile',
  '/telegram',
  '/vkontakte',
  '/onboarding',
  '/about',
  '/pricing',
  '/sign-in',
  '/sign-up',
  '/brands',
  '/channels',
]

function isWhitelisted(path: string): boolean {
  return WHITELIST_PREFIXES.some(
    (p) => path === p || path.startsWith(`${p}/`),
  )
}

export function usePlatformReadiness() {
  const [state, setState] = useState<OnboardingState | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const data = await smmService.onboardingState()
        if (!cancelled) setState(data)
      } catch {
        if (!cancelled) setState(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return { state, loading, needsOnboarding: state ? !state.completed : false }
}

export function PlatformSetupGuard({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { state, loading, needsOnboarding } = usePlatformReadiness()

  useEffect(() => {
    if (loading || !state) return
    if (state.completed || state.skipped) return
    if (isWhitelisted(location.pathname)) return
    navigate('/onboarding', { replace: true, state: { from: location.pathname } })
  }, [loading, state, needsOnboarding, location.pathname, navigate])

  if (loading) return null
  return <>{children}</>
}

export function authStatusLabel(status?: string | null): string {
  switch (status) {
    case 'connected':
      return 'Connected'
    case 'not_required':
      return 'N/A'
    case 'pending':
      return 'Pending'
    case 'missing':
      return 'No auth'
    case 'invalid':
      return 'Invalid'
    default:
      return 'Unknown'
  }
}

export function channelOpsAllowed(channel: {
  role?: string
  auth_status?: string | null
}): boolean {
  if (channel.role === 'competitor') return true
  return channel.auth_status === 'connected'
}

/** Publish requires ownership confirmation; collect/alert do not. */
export function publishAllowed(channel: {
  role?: string
  auth_status?: string | null
}): boolean {
  if (channel.role !== 'own') return false
  return channel.auth_status === 'connected'
}
