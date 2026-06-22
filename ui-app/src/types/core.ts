export interface HealthcheckItem {
  service_name: string
  status: 'ok' | 'error'
  error?: string
  server_time?: string | null
}

export interface HealthcheckResponse {
  services: HealthcheckItem[]
}

export interface StatisticsItem {
  service_name: string
  collected_posts: number
  processed_posts: number
  published_posts: number
}

export interface StatisticsResponse {
  services: StatisticsItem[]
}

export interface UserStatisticsItem {
  user_id: number
  username: string
  email: string
  role: string
  total_posts: number
  collected_posts: number
  processed_posts: number
  published_posts: number
}

export interface UserStatisticsResponse {
  users: UserStatisticsItem[]
}

export interface ScheduleSnapshot {
  user_id: number
  platform: string
  publish_enabled: boolean
  collect_enabled: boolean
  schedule_type: string
  time_intervals: Array<{ start: string; end: string }>
  updated_at: string
}

export interface ScheduleResponse {
  schedules: ScheduleSnapshot[]
}

export interface Notification {
  id: number
  message: string
  user_id?: number | null
  type?: string | null
  created_at: string
}

export interface NotificationResponse {
  notifications: Notification[]
}

export interface NotificationCreate {
  message: string
  user_id?: number | null
  type?: string | null
}

export type FeedbackType = 'bug_report' | 'suggestion' | 'contact_author'

export interface Feedback {
  id: number
  type: FeedbackType
  text: string
  email?: string | null
  user_id?: number | null
  created_at: string
}

export interface FeedbackResponse {
  feedback: Feedback[]
}

export interface FeedbackCreate {
  type: FeedbackType
  text: string
  email?: string | null
}

export const FEEDBACK_TYPE_LABELS: Record<FeedbackType, string> = {
  bug_report: 'Сообщить об ошибке',
  suggestion: 'Предложить доработку',
  contact_author: 'Связаться с автором',
}

// Admin: services status & posts tables

export interface LoopStatus {
  last_run_at?: string | null
  total_processed: number
  last_cycle_count: number
}

export interface CollectorFunction {
  id: string
  name_ru: string
  description: string
}

export interface CollectorStatusDetail {
  service: string
  version: string
  collect_interval_sec?: number | null
  distribute_interval_sec?: number | null
  collect_batch_size?: number | null
  distribute_batch_size?: number | null
  collector?: LoopStatus | null
  distributor?: LoopStatus | null
  current_time?: string | null
  started_at?: string | null
  collect_functions?: CollectorFunction[] | null
  error?: string | null
}

export interface ProcessingOption {
  id: string
  name_ru: string
  description: string
}

export interface ProcessorStatusDetail {
  service: string
  version: string
  process_interval_sec?: number | null
  process_batch_size?: number | null
  processor?: LoopStatus | null
  current_time?: string | null
  started_at?: string | null
  processing_options?: ProcessingOption[] | null
  error?: string | null
}

export interface ScheduleFunction {
  id: string
  name_ru: string
  description: string
}

export interface SchedulerStatusDetail {
  service: string
  version: string
  poll_interval_sec?: number | null
  notify_on_change_only?: boolean | null
  last_poll_at?: string | null
  current_time?: string | null
  started_at?: string | null
  schedule_functions?: ScheduleFunction[] | null
  error?: string | null
}

export interface ProcessorRunResponse {
  status: string
  message: string
  count: number
  errors?: string[] | null
}

export interface ServicesStatusResponse {
  healthchecks: HealthcheckItem[]
  collector?: CollectorStatusDetail | null
  processor?: ProcessorStatusDetail | null
  scheduler?: SchedulerStatusDetail | null
}

export interface PlatformMetric {
  platform: string
  table: string
  collected_count: number
  created_count?: number
  ready_count: number
  processing_count: number
  /** Счётчики по всем статусам строк в *_posts (включая редкие из БД). */
  status_counts?: Record<string, number>
}

export interface PostsTablesResponse {
  platforms: PlatformMetric[]
  posts_table_collector?: Record<string, number> | null
  posts_table_processor?: Record<string, number> | null
  collector_error?: string | null
  processor_error?: string | null
}

/** Одна строка таблицы posts (все столбцы). */
export interface PostRow {
  id: number
  user_id: number
  domain?: string | null
  url?: string | null
  title?: string | null
  author?: string | null
  avatar?: string | null
  post_date?: string | null
  post_text?: string | null
  screenshot?: string | null
  images?: unknown[] | null
  image_over_text?: string | null
  comments: number
  reposts: number
  likes: number
  views: number
  is_ad: boolean
  status?: string | null
  post_type?: string | null
  to_tg: boolean
  to_tw: boolean
  to_wp: boolean
  to_vk: boolean
  to_threads?: boolean
  to_dzen?: boolean
  to_instagram?: boolean
  created_at?: string | null
  updated_at?: string | null
  source_platform?: string | null
  source_id?: number | null
}

export interface PostsListResponse {
  posts: PostRow[]
}

/** Результат цикла диагностики постинга (Telegram и пайплайн). */
export interface StorageFileItem {
  key: string
  size: number
  last_modified: string | null
}

export interface StorageFilesResponse {
  enabled: boolean
  objects: StorageFileItem[]
  next_continuation_token?: string | null
  /** Подстрока фильтра по ключу (например diag) */
  filter_applied?: string | null
  pages_scanned?: number | null
  filter_truncated?: boolean
}

export interface StoragePresignedUrlResponse {
  url: string
  expires_in: number
}

export interface StorageDeleteResponse {
  ok: boolean
  key: string
}

export interface PostingDiagnosticsResponse {
  tg_posts_by_status: Array<{ status: string; count: number }>
  posts_by_status: Array<{ status: string; source_platform: string | null; count: number }>
  ready_for_telegram: number
  profiles_with_channel: number
  hints: string[]
  collected_at: string | null
}

/** Гео по публичному IP (ориентир; TZ контейнера — в local_*). */
export interface RuntimeGeoByIp {
  country?: string | null
  region?: string | null
  city?: string | null
  timezone?: string | null
  isp?: string | null
}

export interface RuntimeLocationResponse {
  hostname: string
  tz_environment_variable?: string | null
  local_timezone: string
  local_utc_offset: string
  local_now_iso: string
  public_ip?: string | null
  public_lookup_error?: string | null
  geo_by_ip?: RuntimeGeoByIp | null
  geo_lookup_error?: string | null
  cloud_aws_region?: string | null
}
