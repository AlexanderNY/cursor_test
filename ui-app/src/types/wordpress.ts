export interface TimeInterval {
  start: string
  end: string
}

export type PublishScheduleType = 'on_new_messages' | 'by_intervals'

export type PostStatus = 'draft' | 'publish' | 'pending' | 'private'

export interface WordPressProfile {
  site_url?: string
  username?: string
  app_password?: string
  publish_enabled: boolean
  collect_enabled: boolean
  publish_schedule_type: PublishScheduleType
  time_intervals?: TimeInterval[]
  collect_sites?: WordPressCollectSiteItem[]
}

/** Профиль публикации WordPress (Post Profile Settings). time_intervals — одно значение "HH:MM". */
export interface WordPressPublishProfile {
  publish_enabled: boolean
  schedule_type?: PublishScheduleType
  time_intervals?: string // "HH:MM"
  site_url?: string
  username?: string
  app_password?: string
  /** Публиковать все посты, готовые к публикации */
  publish_all_ready?: boolean
  /** Ограничение количества постов (если publish_all_ready = false) */
  publish_limit?: number
  /** Интервал в минутах 15–1440 с шагом 15 */
  publish_interval_minutes?: number
  /** Обрабатывать перед публикацией */
  process_before_publish?: boolean
  /** Описание обработки */
  process_description?: string
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  /** Сервисы для подготовки обработки: wordpress, telegram, twitter, vkontakte */
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  /** Статичный HTML до 1000 символов */
  static_html_content?: string
}

/** Один сайт сбора: site_url, schedule_type, time_intervals (HH:MM) */
export interface WordPressCollectSiteItem {
  site_url?: string
  schedule_type?: PublishScheduleType
  time_intervals?: string // "HH:MM"
}

/** Профиль сбора WordPress (Parser Profile Settings) */
export interface WordPressCollectProfile {
  collect_enabled: boolean
  collect_sites?: WordPressCollectSiteItem[]
  /** Собрать все доступное; иначе ограничение collect_limit (1–25) */
  collect_all_available?: boolean
  /** Ограничение количества постов (1–25), по умолчанию 1 */
  collect_limit?: number
}

export interface WordPressPost {
  pageID?: string
  tagIdList?: number[]
  categoriesIdList?: number[]
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
  to_threads?: boolean
  to_dzen?: boolean
  to_instagram?: boolean
  post: {
    title: string
    content: string
    status?: PostStatus
    categories?: string[]
    tags?: string[]
    excerpt?: string
    slug?: string
    featured_media?: number
    meta?: Record<string, any>
  }
}

export interface WordPressPostListItem {
  id?: number
  title: string
  status: PostStatus
  excerpt?: string
}

/** Полный пост с бэкенда (поля БД: post_text и т.д.) */
export interface WordPressPostFull {
  id: number
  title?: string
  post_text?: string
  status?: PostStatus
  excerpt?: string
  slug?: string
  categories?: string[]
  tags?: string[]
  featured_media?: number
  meta?: Record<string, unknown>
  [key: string]: unknown
}
