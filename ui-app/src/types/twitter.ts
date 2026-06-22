/** Соответствует Core ScheduleType: immediate | intervals */
export type TwitterScheduleType = 'immediate' | 'intervals'

export interface TwitterProfile {
  publish_enabled: boolean
  collect_enabled: boolean
  schedule_type: TwitterScheduleType
  time_intervals?: TimeInterval[]
  use_proxy?: boolean
  proxy_user?: string
  proxy_pass?: string
  proxy_host?: string
  proxy_port?: number
  twitter_username?: string | null
  twitter_password?: string | null
  take_screenshot_collect?: boolean
  screenshot_xpath?: string | null
  twitter_connected?: boolean
  twitter_rest_id?: string | null
}

export interface TwitterPost {
  text: string
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
  to_threads?: boolean
  to_dzen?: boolean
  to_instagram?: boolean
}

export interface TwPostRow {
  id: number
  user_id: number
  domain?: string | null
  url?: string | null
  title?: string | null
  author?: string | null
  post_text?: string | null
  screenshot?: string | null
  status?: string | null
  post_type?: string | null
  created_at?: string
  updated_at?: string
}

export interface TwitterOAuthStatus {
  twitter_connected: boolean
  twitter_rest_id: string | null
}

export interface TwitterFollowingUser {
  id: string
  username?: string | null
  name?: string | null
}

export interface TwitterFollowingResponse {
  users: TwitterFollowingUser[]
  next_token?: string | null
  error?: string | null
}

/** Ответ tw-bot POST /tw-bot/verify-selenium (fallback браузером) */
export interface TwitterSeleniumVerifyResponse {
  ok: boolean
  method: 'selenium'
  users: TwitterFollowingUser[]
  error?: string
  message?: string
  /** Ключ в S3 при ошибке Selenium (имя содержит «diag») */
  diag_s3_key?: string
}

export interface TimeInterval {
  start: string // HH:MM format
  end: string // HH:MM format
}
