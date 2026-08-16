export interface URLConfig {
  /** Stable id (uuid) for Configure deep-link */
  id?: string
  url: string
  xpath: string
  take_screenshot: boolean
  /** Формат скриншота: base64 в ответе или файл (путь). Показывается при take_screenshot. */
  screenshot_format?: 'base64' | 'file'
  target_social_networks: {
    tg?: boolean
    tw?: boolean
    vk?: boolean
    wp?: boolean
  }
  /** TG channel external_id list */
  target_channels?: string[]
  /** VK group external_id list */
  target_groups?: string[]
  /** Время запуска (HH:MM) */
  schedule_time: string
  /** Выполнить один раз в заданное время (иначе — ежедневно) */
  run_once?: boolean
  /** Per-URL processing */
  process_before_publish?: boolean
  process_description?: string
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string
  screenshot_only?: boolean
}

export interface CustomURLSettings {
  collect_enabled: boolean
  urls: URLConfig[]
  /** Legacy global processing (synced from first URL; not edited in UI) */
  process_before_publish?: boolean
  process_description?: string
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string
  screenshot_only?: boolean
}

/** Элемент списка постов из url_posts (собранные по URL) */
export interface UrlPostListItem {
  id: number
  user_id: number
  url?: string
  post_text: string
  images?: string[]
  status: string
  post_date?: string
  created_at: string
  updated_at: string
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
}
