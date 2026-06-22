export type ScheduleType = 'immediate' | 'intervals'

export interface TimeInterval {
  start: string
  end?: string
}

export type DzenCollectSource = 'rss' | 'selenium' | 'both'

export interface DzenSubscriptionItem {
  title: string
  url: string
}

/** Ответ dzen-bot POST /dzen-bot/verify-yandex/start | push-code (и legacy /verify-yandex) */
export interface DzenVerifyResponse {
  ok: boolean
  need_push_code?: boolean
  subscriptions: DzenSubscriptionItem[]
  error?: string | null
  message?: string | null
  diag_image_url?: string | null
}

export interface DzenProfile {
  publish_enabled: boolean
  collect_enabled: boolean
  schedule_type?: ScheduleType
  time_intervals?: TimeInterval[]
  rss_feed_url?: string | null
  channel_name?: string | null
  channels_to_read?: string[]
  rss_token?: string | null
  yandex_login?: string | null
  yandex_password?: string | null
  dzen_studio_url?: string | null
  collect_source?: DzenCollectSource
  last_auth_error?: string | null
}

export interface DzenPost {
  text: string
  title?: string | null
  images?: string[]
  videos?: string[]
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
  to_dzen?: boolean
  to_threads?: boolean
  to_instagram?: boolean
}

export interface DzenPostListItem {
  id: number
  post_text: string
  title?: string | null
  images?: string[]
  videos?: string[]
  status: string
  created_at: string
  updated_at: string
}

export interface DzenPostFull {
  id: number
  user_id: number
  title?: string | null
  post_text: string
  images?: string[]
  videos?: string[]
  status: string
  to_tg: boolean
  to_wp: boolean
  to_vk: boolean
  to_dzen: boolean
  created_at: string
  updated_at: string
}
