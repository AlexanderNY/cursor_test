export type BrandNetwork =
  | 'tg'
  | 'vk'
  | 'url'
  | 'instagram'
  | 'threads'
  | 'tw'
  | 'dzen'
  | 'wp'
export type ChannelKind = 'channel' | 'group' | 'public'
export type ChannelRole = 'own' | 'competitor' | 'source'
export type InboxType = 'dm' | 'comment' | 'reaction' | 'competitor_post'
export type InboxStatus = 'new' | 'read' | 'replied' | 'archived' | 'reply_failed' | 'in_progress'
export type AutomationType = 'rss' | 'tg_repost' | 'mention'
export type GroupRole = 'admin' | 'editor' | 'analyst' | 'manager' | 'author'

export const BRAND_PALETTE = [
  '#3B82F6',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#8B5CF6',
  '#EC4899',
  '#06B6D4',
  '#84CC16',
] as const

export interface BrandPromptSnippet {
  title: string
  text: string
}

export interface Brand {
  id: number
  user_id: number
  group_id?: number | null
  name: string
  color: string
  tone_of_voice?: string | null
  style_notes?: string | null
  prompt_snippets?: BrandPromptSnippet[]
  is_demo?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export type ConditionsMode = 'any_of' | 'all_of'

export interface ChannelProcessingConfig {
  process_enabled?: boolean
  processing_description?: string | null
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  /** @deprecated use BrandChannel.publish_targets */
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string | null
  summarize_enabled?: boolean
  summarize_min_length?: number
  classification_enabled?: boolean
  classification_categories?: string[]
  /** Competitor sync cadence in minutes (default 60). */
  sync_interval_min?: number
}

export interface ChannelAlertDelivery {
  channel_to_post?: string | null
  channel_to_post_title?: string | null
  alert_text?: string | null
  include_ai_summary?: boolean
  /** Own brand channel ids to send alerts to (like publish_targets). */
  alert_targets?: number[]
}

export interface ChannelAlertRule {
  id: string
  enabled?: boolean
  priority?: number
  save_conditions?: string[]
  conditions_mode?: ConditionsMode
  category_filter?: string | null
  dedup_window_sec?: number
  rate_limit_per_hour?: number | null
  time_windows?: { start: string; end: string }[]
  min_text_length?: number
  sentiment_filter?: 'positive' | 'negative' | 'neutral' | null
  tags?: string[]
  stop_on_match?: boolean
}

export interface UrlChannelConfig {
  id?: string
  url?: string
  xpath?: string
  take_screenshot?: boolean
  screenshot_format?: 'base64' | 'file' | string
  schedule_time?: string
  run_once?: boolean
  target_social_networks?: {
    tg?: boolean
    tw?: boolean
    vk?: boolean
    wp?: boolean
  }
  target_channels?: string[]
  target_groups?: string[]
  process_before_publish?: boolean
  process_description?: string | null
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string | null
  screenshot_only?: boolean
}

export interface BrandChannel {
  id: number
  brand_id: number
  network: BrandNetwork
  external_id: string
  title?: string | null
  kind: ChannelKind
  role: ChannelRole
  color_override?: string | null
  created_at?: string | null
  publish_enabled?: boolean
  collect_enabled?: boolean
  discussion_external_id?: string | null
  discussion_title?: string | null
  comments_collect_enabled?: boolean
  alert_enabled?: boolean
  save_conditions?: string[]
  conditions_mode?: ConditionsMode
  processing?: ChannelProcessingConfig
  publish_targets?: number[]
  alert_delivery?: ChannelAlertDelivery
  alert_rules?: ChannelAlertRule[]
  /** Present when network === 'url' — scrape settings from curl_settings */
  url_config?: UrlChannelConfig | null
  brand_name?: string
  brand_color?: string
  auth_status?: 'connected' | 'missing' | 'pending' | 'invalid' | 'unknown' | 'not_required'
  auth_checked_at?: string | null
  auth_error?: string | null
  auth_capabilities?: Record<string, boolean>
}

export interface PlatformNetworkStatus {
  connected: boolean
  state?: string
  message?: string
  can_collect?: boolean
  can_publish_text?: boolean
  can_publish_media?: boolean
  can_alert?: boolean
  setup_url?: string
}

export interface PlatformStatusResponse {
  tg: PlatformNetworkStatus
  vk: PlatformNetworkStatus
  instagram?: PlatformNetworkStatus
  threads?: PlatformNetworkStatus
  tw?: PlatformNetworkStatus
  dzen?: PlatformNetworkStatus
  wp?: PlatformNetworkStatus
}

export interface OnboardingState {
  step: number
  total_steps: number
  tg_ready: boolean
  vk_ready: boolean
  any_platform_ready?: boolean
  has_brand: boolean
  has_own_channel: boolean
  has_connected_own_channel: boolean
  skipped: boolean
  completed: boolean
  platforms?: PlatformStatusResponse
  demo_seeded?: boolean
  demo_brand_id?: number | null
  learn_mode?: boolean
  utm_campaign?: string | null
}

export interface InboxItem {
  id: number
  user_id: number
  brand_id?: number | null
  network: BrandNetwork
  channel_id?: number | null
  thread_id?: string | null
  type: InboxType
  author?: string | null
  text?: string | null
  status: InboxStatus
  created_at?: string | null
  reply_text?: string
  reply_queued?: boolean
  reply_job_id?: number
  reply_error?: string
  reply_status?: string
  external_msg_id?: string | null
  edited_text?: string | null
  meta?: Record<string, unknown> | null
}

export interface PublishJobTarget {
  network: BrandNetwork
  external_id: string
}

export interface PublishJob {
  id: number
  user_id: number
  brand_id?: number | null
  source_text: string
  media: string[]
  targets: PublishJobTarget[]
  adapters_result: Record<string, unknown>
  publish_at?: string | null
  status: string
  created_at?: string | null
  updated_at?: string | null
  assigned_to?: number | null
  rejection_comment?: string | null
  retry_count?: number
  last_error?: string | null
}

export type PublishJobStatus =
  | 'draft'
  | 'pending_approval'
  | 'ready'
  | 'scheduled'
  | 'publishing'
  | 'published'
  | 'failed'
  | 'rejected'
  | 'partial'


export interface AutomationRule {
  id: number
  user_id: number
  brand_id?: number | null
  type: AutomationType
  config: Record<string, unknown>
  enabled: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface AnalyticsOverview {
  period: string
  brand_id?: number | null
  channel_id?: number | null
  reach: number
  engagement: number
  er: number
  posts: number
  subscriber_growth: number
  by_network: {
    tg: Record<string, number>
    vk: Record<string, number>
  }
}

export interface AnalyticsPost {
  id: number
  text: string
  views: number
  likes: number
  comments: number
  reposts: number
  er: number
  network: string
  created_at?: string | null
  published_at?: string | null
  channel_id?: number | null
  channel_external_id?: string | null
  channel_title?: string | null
}

export interface BestTimeSlot {
  weekday: number
  hour: number
  score: number
}

export type TemplateKind = 'prompt' | 'cta' | 'utm' | 'post_body'

export interface ContentTemplate {
  id: number
  user_id: number
  brand_id: number
  kind: TemplateKind
  title: string
  body: string
  metadata: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

export interface MediaPack {
  id: number
  user_id: number
  brand_id: number
  title: string
  object_keys: string[]
  caption?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface TemplateApplyResult {
  template: ContentTemplate
  applied: {
    kind: TemplateKind
    mode: 'prompt' | 'append' | 'replace'
    text: string
    prompt_note?: string
    url?: string
    networks?: string[]
  }
  text: string
  job?: PublishJob | null
}

export interface MediaPackApplyResult {
  media_pack: MediaPack
  media: string[]
  caption?: string | null
  job?: PublishJob | null
}

export function isGroupAdmin(role?: string | null): boolean {
  return role === 'admin' || role === 'manager'
}

export function isGroupEditor(role?: string | null): boolean {
  return isGroupAdmin(role) || role === 'editor' || role === 'author'
}

export function canPublish(role?: string | null, globalRole?: string | null): boolean {
  if (globalRole === 'admin') return true
  return isGroupEditor(role) || !role
}

export function roleLabel(role?: string | null): string {
  switch (role) {
    case 'admin':
    case 'manager':
      return 'Admin'
    case 'editor':
    case 'author':
      return 'Editor'
    case 'analyst':
      return 'Analyst'
    default:
      return role ?? '—'
  }
}

export type AiAssistActionId = 'summarize' | 'categorize' | 'rewrite' | 'reply_draft'

export interface AiAssistAction {
  id: AiAssistActionId
  title: string
  description: string
  params: string[]
}

export interface AiProcessParams {
  note?: string
  tone?: string
  network?: string
  max_len?: number
  categories?: string[]
}

export interface AiProcessResult {
  text?: string
  category?: string
  confidence?: number
  meta?: Record<string, unknown>
}

export interface AiProcessResponse {
  task_id: number
  action: AiAssistActionId
  result: AiProcessResult
  model: string
  latency_ms: number
}

export interface AiUsage {
  used: number
  limit: number
  period: string
  remaining?: number
}

export interface UsageMetric {
  key: string
  used: number | null
  limit: number
  unit?: string
  remaining?: number | null
}

export interface UsageSummary {
  tariff: string
  period?: string
  features?: Record<string, boolean>
  metrics: UsageMetric[]
}

export interface CompetitorPost {
  id: number
  external_post_id?: string | null
  text?: string | null
  url?: string | null
  text_hash?: string | null
  views?: number
  likes?: number
  comments?: number
  reposts?: number
  posted_at?: string | null
  collected_at?: string | null
}

export interface CompetitorDigest {
  channel_id: number
  period: string
  since?: string
  posts_count: number
  posts: CompetitorPost[]
  summary?: string | null
  fallback?: boolean
}

export interface CompetitorDiff {
  channel_id: number
  since?: string | null
  last_seen_at?: string | null
  new_posts: CompetitorPost[]
  count: number
}

export interface CompetitorCompareStats {
  posts_count: number
  avg_length: number
  posts_per_day?: number | null
}

export interface CompetitorCompare {
  brand_id: number
  competitor_channel_id: number
  period: string
  since?: string
  own: CompetitorCompareStats
  competitor: CompetitorCompareStats
  top_themes: { theme: string; count: number }[]
}

