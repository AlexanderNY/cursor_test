export type SpotlightItem = {
  appSlug: string
  postSlug: string
  title: string
  excerpt: string
  publishedAt: string
  appTitle: string
  emoji: string
  accent: string
  href: string
}

export type SitePromo = {
  enabled: boolean
  eyebrow: string
  items: SpotlightItem[]
  /** Ручной выбор: "appSlug/postSlug". Пусто = авто по дате. */
  curatedKeys?: string[]
  /** legacy — не используются каруселью */
  serviceSlug?: string
  title?: string
  body?: string
  ctaLabel?: string
  ctaHref?: string
}

export const DEFAULT_SITE_PROMO: SitePromo = {
  enabled: true,
  eyebrow: 'Спотлайт · взаимное продвижение',
  items: [],
  curatedKeys: [],
}

function normalizeItem(raw: Partial<SpotlightItem> | null | undefined): SpotlightItem | null {
  if (!raw?.title || !raw?.href) {
    return null
  }
  return {
    appSlug: String(raw.appSlug || ''),
    postSlug: String(raw.postSlug || ''),
    title: String(raw.title).slice(0, 200),
    excerpt: String(raw.excerpt || '').slice(0, 400),
    publishedAt: String(raw.publishedAt || ''),
    appTitle: String(raw.appTitle || raw.appSlug || ''),
    emoji: String(raw.emoji || ''),
    accent: String(raw.accent || '#2dd4bf'),
    href: String(raw.href),
  }
}

export function normalizeSitePromo(raw: Partial<SitePromo> | null | undefined): SitePromo {
  const items = Array.isArray(raw?.items)
    ? raw.items.map(normalizeItem).filter((item): item is SpotlightItem => item != null).slice(0, 5)
    : []
  const curatedKeys = Array.isArray(raw?.curatedKeys)
    ? raw.curatedKeys
        .map((k) => String(k || '').trim())
        .filter((k) => k.includes('/'))
        .slice(0, 5)
    : []
  return {
    enabled: raw?.enabled !== false,
    eyebrow: String(raw?.eyebrow ?? DEFAULT_SITE_PROMO.eyebrow).slice(0, 120),
    items,
    curatedKeys,
    serviceSlug: raw?.serviceSlug,
    title: raw?.title,
    body: raw?.body,
    ctaLabel: raw?.ctaLabel,
    ctaHref: raw?.ctaHref,
  }
}
