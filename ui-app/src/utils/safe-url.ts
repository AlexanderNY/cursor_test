/** Navigation targets the SPA is willing to open. */

const OAUTH_HOSTS = new Set([
  'oauth.vk.com',
  'id.vk.com',
  'twitter.com',
  'x.com',
  'api.twitter.com',
  'threads.net',
  'www.threads.net',
])

const STRIPE_HOSTS = new Set(['checkout.stripe.com', 'billing.stripe.com'])

export function safeHref(raw: string | null | undefined): string | null {
  if (!raw) return null
  const value = raw.trim()
  if (!value) return null
  if (value.startsWith('/')) {
    const second = value[1]
    if (second === '/' || second === '\\') return null
    return value
  }
  if (value.startsWith('#') && !value.includes(':')) {
    return value
  }
  try {
    const url = new URL(value)
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      return url.href
    }
  } catch {
    return null
  }
  return null
}

export function allowedOAuthUrl(raw: string): string | null {
  const href = safeHref(raw)
  if (!href) return null
  if (href.startsWith('/')) return href
  try {
    const url = new URL(href)
    if (typeof window !== 'undefined' && url.origin === window.location.origin) {
      return url.href
    }
    if (OAUTH_HOSTS.has(url.hostname.toLowerCase())) return url.href
  } catch {
    return null
  }
  return null
}

export function allowedStripeUrl(raw: string): string | null {
  const href = safeHref(raw)
  if (!href) return null
  try {
    const url = new URL(href)
    if (url.protocol === 'https:' && STRIPE_HOSTS.has(url.hostname.toLowerCase())) {
      return url.href
    }
  } catch {
    return null
  }
  return null
}
