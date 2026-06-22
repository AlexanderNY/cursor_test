export type PublishScheduleType = 'on_new_messages' | 'by_intervals'

export interface TimeInterval {
  start: string
  end?: string
}

export interface ThreadsConfig {
  /** @username или имя без @ — для подписи; OAuth остаётся единственным способом входа API */
  instagram_handle?: string | null
  publish_enabled: boolean
  collect_enabled: boolean
  schedule_type?: 'immediate' | 'on_new_messages' | 'by_intervals'
  time_intervals?: TimeInterval[]
  process_enabled: boolean
  processing_description?: string
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string
  threads_connected?: boolean
  threads_user_id?: string
}

export interface ThreadsPostListItem {
  id: number
  post_text: string
  images?: string[]
  status: string
  created_at: string
  updated_at: string
}

export interface ThreadsPostFull {
  id: number
  user_id: number
  domain?: string
  url?: string
  title?: string
  author?: string
  avatar?: string
  post_date?: string
  post_text: string
  screenshot?: string
  images?: string[]
  image_over_text?: string
  comments: number
  reposts: number
  likes: number
  views: number
  is_ad: boolean
  status: string
  post_type?: string
  to_tg: boolean
  to_tw: boolean
  to_wp: boolean
  to_vk: boolean
  to_threads: boolean
  created_at: string
  updated_at: string
}

export interface ThreadsAuthStatus {
  user_id: number
  connected: boolean
  /** true если есть токен и локальное время истечения ещё не прошло */
  connected_effective?: boolean
  expires_at?: string | null
  token_expired_locally?: boolean
  threads_user_id?: string | null
  message: string
}

/** Элемент GET /me/permissions (разрешения приложения у пользователя) */
export interface ThreadsGraphPermission {
  permission: string
  status: string
}

/** Результат POST /threads-bot/selenium/attempt (диагностика, не OAuth token) */
export interface ThreadsSeleniumAttemptResult {
  session_id: number
  user_id: number
  status: string
  message: string
  /** Ключ объекта в S3 (подстрока diag), если скрин сохранён при сбое */
  diagnostic_s3_key?: string | null
  /** Скрин для встраивания в UI (только если PNG ≤ лимита на бэкенде) */
  diagnostic_image_data_url?: string | null
  disclaimer?: string
}

export interface ThreadsSeleniumSessionRow {
  id: number
  user_id: number
  status: string
  detail_message?: string | null
  created_at?: string
  updated_at?: string
}

export interface ThreadsAuthVerify {
  user_id: number
  valid: boolean
  message: string
  threads_user_id?: string | null
  graph_user_id?: string | null
  expires_at?: string | null
  token_expired_locally: boolean
  persisted_threads_user_id: boolean
  /** Scopes из ответа debug_token (если настроены App ID / Secret) */
  scopes?: string[]
  /** Подписки/разрешения: список из Graph API /me/permissions */
  permissions?: ThreadsGraphPermission[]
  /** Текст ошибки, если список разрешений не удалось получить */
  permissions_error?: string | null
}
