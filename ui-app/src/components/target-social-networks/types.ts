export type TargetSocialNetworkKey =
  | 'tg'
  | 'vk'
  | 'instagram'
  | 'threads'
  | 'wp'
  | 'dzen'
  | 'tw'

export type TargetSocialNetworks = Record<TargetSocialNetworkKey, boolean>

/** Порядок: Telegram → VK → Instagram → Threads → WordPress → Дзен → Twitter */
export const TARGET_SOCIAL_NETWORK_ORDER: TargetSocialNetworkKey[] = [
  'tg',
  'vk',
  'instagram',
  'threads',
  'wp',
  'dzen',
  'tw',
]

export const TARGET_SOCIAL_LABELS: Record<TargetSocialNetworkKey, string> = {
  tg: 'Telegram',
  vk: 'VKontakte',
  instagram: 'Instagram',
  threads: 'Threads',
  wp: 'WordPress',
  dzen: 'Дзен',
  tw: 'Twitter',
}

export const EMPTY_TARGET_SOCIAL_NETWORKS: TargetSocialNetworks = {
  tg: false,
  vk: false,
  instagram: false,
  threads: false,
  wp: false,
  dzen: false,
  tw: false,
}

export function createDefaultTargets(primary: TargetSocialNetworkKey): TargetSocialNetworks {
  return { ...EMPTY_TARGET_SOCIAL_NETWORKS, [primary]: true }
}
