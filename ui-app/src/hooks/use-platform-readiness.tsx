import { useEffect, useState, type ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { smmService } from '@/services/smm-service'
import type { OnboardingState } from '@/types/smm'

const WHITELIST_PREFIXES = [
  '/profile',
  '/telegram',
  '/vkontakte',
  '/instagram',
  '/threads',
  '/twitter',
  '/wordpress',
  '/dzen',
  '/custom-url',
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

  async function refresh() {
    try {
      const data = await smmService.onboardingState()
      setState(data)
      return data
    } catch {
      setState(null)
      return null
    }
  }

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

  return {
    state,
    loading,
    refresh,
    needsOnboarding: state ? !state.completed : false,
  }
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

/** Collect needs platform read capability (TG session / VK user OAuth). */
export function collectAllowed(
  channel: {
    network?: string
    auth_capabilities?: Record<string, boolean> | null
  },
  platform?: { can_collect?: boolean; connected?: boolean } | null,
): boolean {
  if (channel.network === 'url') return true
  const caps = channel.auth_capabilities
  if (caps && typeof caps.can_collect === 'boolean') {
    return Boolean(caps.can_collect)
  }
  if (platform && typeof platform.can_collect === 'boolean') {
    return Boolean(platform.can_collect)
  }
  return false
}

/** Alerts need the same read session as collect (TG / VK user OAuth). */
export function alertAllowed(
  channel: {
    network?: string
    auth_capabilities?: Record<string, boolean> | null
  },
  platform?: { can_alert?: boolean; can_collect?: boolean; connected?: boolean } | null,
): boolean {
  if (channel.network === 'url') return false
  if (channel.network !== 'tg' && channel.network !== 'vk') return false
  const caps = channel.auth_capabilities
  if (caps && typeof caps.can_alert === 'boolean') {
    return Boolean(caps.can_alert)
  }
  if (caps && typeof caps.can_collect === 'boolean') {
    return Boolean(caps.can_collect)
  }
  if (platform && typeof platform.can_alert === 'boolean') {
    return Boolean(platform.can_alert)
  }
  if (platform && typeof platform.can_collect === 'boolean') {
    return Boolean(platform.can_collect)
  }
  return false
}

export type ChannelLike = {
  network?: string
  role?: string
  auth_status?: string | null
  auth_capabilities?: Record<string, boolean> | null
  publish_enabled?: boolean
  collect_enabled?: boolean
  alert_enabled?: boolean
  publish_targets?: number[] | null
  alert_delivery?: {
    alert_targets?: number[]
    channel_to_post?: string | null
    alert_text?: string | null
  } | null
  alert_rules?: { enabled?: boolean; save_conditions?: string[] }[] | null
  processing?: { status_review_after_process?: boolean } | null
  url_config?: { status_review_after_process?: boolean; url?: string } | null
}

/** Collect → manual review before publish. */
export function reviewEnabled(channel: ChannelLike): boolean {
  if (channel.network === 'url') {
    return Boolean(channel.url_config?.status_review_after_process)
  }
  return Boolean(channel.processing?.status_review_after_process)
}

export function publishReady(channel: ChannelLike): boolean {
  return (
    channel.role === 'own' &&
    Boolean(channel.publish_enabled) &&
    publishAllowed(channel)
  )
}

/** Collect is ready when enabled, readable, and has forward targets and/or review. */
export function collectReady(
  channel: ChannelLike,
  platform?: { can_collect?: boolean; connected?: boolean } | null,
): boolean {
  if (!channel.collect_enabled) return false
  if (!collectAllowed(channel, platform)) return false
  const hasTargets = (channel.publish_targets || []).length > 0
  const toReview = reviewEnabled(channel)
  // Source/competitor/url: need somewhere to go (targets) or stay on review
  return hasTargets || toReview
}

export function alertReady(
  channel: ChannelLike,
  platform?: { can_alert?: boolean; can_collect?: boolean; connected?: boolean } | null,
): boolean {
  if (!channel.alert_enabled) return false
  if (channel.network !== 'tg' && channel.network !== 'vk') return false
  if (!alertAllowed(channel, platform)) return false
  const delivery = channel.alert_delivery || {}
  const hasDest =
    (delivery.alert_targets || []).length > 0 || Boolean(delivery.channel_to_post)
  if (!hasDest) return false
  if (!(delivery.alert_text || '').trim()) return false
  const rules = channel.alert_rules || []
  const hasRule = rules.some(
    (r) =>
      r &&
      r.enabled !== false &&
      (r.save_conditions || []).some((c) => typeof c === 'string' && c.trim()),
  )
  return hasRule
}

/** Channel is operational if at least one flow is fully configured. */
export function channelReady(
  channel: ChannelLike,
  platform?: {
    can_collect?: boolean
    can_alert?: boolean
    connected?: boolean
  } | null,
): boolean {
  return (
    publishReady(channel) ||
    collectReady(channel, platform) ||
    alertReady(channel, platform)
  )
}
