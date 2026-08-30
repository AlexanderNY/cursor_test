/** Canonical SMM channel networks (aligned with core/services/smm_networks.py). */

export type BrandNetwork =
  | 'tg'
  | 'vk'
  | 'url'
  | 'instagram'
  | 'threads'
  | 'tw'
  | 'dzen'
  | 'wp'

export const BRAND_NETWORKS: BrandNetwork[] = [
  'tg',
  'vk',
  'instagram',
  'threads',
  'tw',
  'dzen',
  'wp',
  'url',
]

export const INBOX_NETWORKS: BrandNetwork[] = [
  'tg',
  'vk',
  'instagram',
  'threads',
  'tw',
  'dzen',
  'wp',
]

export const NETWORK_LABELS: Record<BrandNetwork, string> = {
  tg: 'Telegram',
  vk: 'VKontakte',
  url: 'URL',
  instagram: 'Instagram',
  threads: 'Threads',
  tw: 'Twitter',
  dzen: 'Дзен',
  wp: 'WordPress',
}

export const NETWORK_SETUP_URLS: Record<BrandNetwork, string> = {
  tg: '/telegram',
  vk: '/vkontakte',
  url: '/custom-url',
  instagram: '/instagram',
  threads: '/threads',
  tw: '/twitter',
  dzen: '/dzen',
  wp: '/wordpress',
}

export function networkLabel(network: string | null | undefined): string {
  if (!network) return '—'
  return NETWORK_LABELS[network as BrandNetwork] ?? network.toUpperCase()
}

export function networkSetupUrl(network: string | null | undefined): string {
  if (!network) return '/channels'
  return NETWORK_SETUP_URLS[network as BrandNetwork] ?? '/channels'
}

export function isPublishNetwork(network: string | null | undefined): boolean {
  return Boolean(network && network !== 'url')
}
