export interface HealthcheckItem {
  service_name: string
  status: 'ok' | 'error'
  error?: string
  server_time?: string | null
  optional?: boolean
  cpu_percent?: number | null
  memory_bytes?: number | null
  memory_limit_bytes?: number | null
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

export interface PlatformEffectivenessItem {
  platform: string
  total: number
  published: number
  failed: number
  skipped: number
  in_queue: number
  success_rate: number | null
}

export interface PipelineEffectivenessResponse {
  period_days: number
  since: string
  targets_total: number
  published: number
  failed: number
  skipped: number
  in_queue: number
  success_rate: number | null
  by_platform: PlatformEffectivenessItem[]
  failures: Array<{ reason: string; count: number }>
  latency: {
    sample_size: number
    median_minutes: number | null
    p95_minutes: number | null
  }
  stuck: {
    posts_collected: number
    posts_processing: number
    posts_review: number
    posts_ready: number
    collected_older_than_1h: number
    targets_pending: number
    targets_ready: number
    targets_publishing: number
    ready_older_than_1h: number
    publishing_older_than_15m: number
  }
  users_with_posts: number
  users_with_published: number
  collected_at?: string | null
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

// Roadmap («Что далее»)

export interface RoadmapItem {
  id: number
  title: string
  description?: string | null
  is_active: boolean
  created_by?: number | null
  created_at: string
  updated_at: string
  vote_count: number
  voted: boolean
}

export interface RoadmapListResponse {
  items: RoadmapItem[]
}

export interface RoadmapItemCreate {
  title: string
  description?: string | null
}

export interface RoadmapItemUpdate {
  title?: string
  description?: string | null
  is_active?: boolean
}

export interface RoadmapVoteResponse {
  item_id: number
  voted: boolean
  vote_count: number
}

export type ForumScope = 'workspace' | 'platform'

export type ForumKind = 'discussion' | 'bug_report' | 'suggestion' | 'contact_author'
export type ForumStatus = 'new' | 'accepted' | 'in_progress' | 'done'

export const FORUM_KIND_LABELS: Record<ForumKind, string> = {
  discussion: 'Обсуждение',
  bug_report: 'Ошибка',
  suggestion: 'Идея',
  contact_author: 'Вопрос автору',
}

export const FORUM_STATUS_LABELS: Record<ForumStatus, string> = {
  new: 'Новая',
  accepted: 'Принята',
  in_progress: 'В работе',
  done: 'Сделана',
}

export interface ForumThread {
  id: number
  scope: ForumScope
  group_id?: number | null
  group_name?: string | null
  kind: ForumKind
  title: string
  body: string
  author_id: number
  author_name: string
  author_avatar?: string | null
  is_closed: boolean
  status: ForumStatus
  is_pinned: boolean
  attachment_path?: string | null
  unread: boolean
  vote_count: number
  voted: boolean
  reply_count: number
  created_at: string
  updated_at: string
  can_reply: boolean
  can_vote: boolean
  can_close: boolean
  can_delete: boolean
  can_set_status: boolean
  can_pin: boolean
  can_attach: boolean
}

export interface ForumPost {
  id: number
  thread_id: number
  body: string
  author_id: number
  author_name: string
  author_avatar?: string | null
  created_at: string
  updated_at?: string | null
  quote_author?: string | null
  quote_body?: string | null
  can_delete: boolean
  can_edit: boolean
}

export interface ForumThreadDetail extends ForumThread {
  posts: ForumPost[]
}

export interface ForumListResponse {
  scope: ForumScope
  group_id?: number | null
  group_name?: string | null
  threads: ForumThread[]
}

export interface ForumThreadCreate {
  scope: ForumScope
  kind: ForumKind
  title: string
  body: string
}

export interface ForumVoteResponse {
  thread_id: number
  voted: boolean
  vote_count: number
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
  /** Канал публикации (tg) или целевые платформы → tg,wp,… */
  published_channel?: string | null
}

export interface PostsListResponse {
  posts: PostRow[]
}

export interface PipelineEventItem {
  id?: number | null
  user_id?: number | null
  channel?: string | null
  event_type?: string | null
  platform?: string | null
  rule_id?: string | null
  service?: string | null
  cycle_type?: string | null
  status?: string | null
  summary?: string | null
  items_processed?: number | null
  created_at?: string | null
}

export interface PipelineEventsResponse {
  alerting: PipelineEventItem[]
  publishing: PipelineEventItem[]
  collection: PipelineEventItem[]
  custom_url: PipelineEventItem[]
  services: PipelineEventItem[]
  services_error?: string | null
  collected_at?: string | null
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

export interface StorageDeleteFailure {
  key: string
  error: string
}

export interface StorageBulkDeleteResponse {
  ok: boolean
  deleted: string[]
  failed: StorageDeleteFailure[]
}

export interface PostingDiagnosticsResponse {
  tg_targets_by_status?: Array<{ status: string; count: number }>
  tg_posts_by_status: Array<{ status: string; count: number }>
  posts_by_status: Array<{ status: string; source_platform: string | null; count: number }>
  ready_for_telegram: number
  profiles_with_channel: number
  hints: string[]
  collected_at: string | null
}

export interface PostTraceStage {
  stage: string
  label: string
  done: boolean
  detail?: string | null
}

export interface PostTraceTimelineItem {
  kind: string
  at?: string | null
  platform?: string | null
  from_status?: string | null
  to_status?: string | null
  actor?: string | null
  job_id?: number | null
  payload?: Record<string, unknown>
  source?: string | null
}

export interface PostTraceResponse {
  post_id: number
  hub: Record<string, unknown>
  targets: Array<Record<string, unknown>>
  lifecycle_events: Array<Record<string, unknown>>
  timeline: PostTraceTimelineItem[]
  stages: PostTraceStage[]
  related_tg_events: Array<Record<string, unknown>>
  collected_at?: string | null
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

export interface AiCheckResponse {
  reply: string
  model: string
  latency_ms: number
}

export interface AiSettingsResponse {
  enabled: boolean
  env_enabled?: boolean
  model: string
  service_url: string
  available?: boolean
  circuit_open?: boolean
  status?: 'ready' | 'disabled' | 'unavailable' | 'circuit_open' | string
}
