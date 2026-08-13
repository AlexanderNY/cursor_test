export type BrandNetwork = 'tg' | 'vk'
export type ChannelKind = 'channel' | 'group' | 'public'
export type ChannelRole = 'own' | 'competitor' | 'source'
export type InboxType = 'dm' | 'comment' | 'reaction'
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

export interface Brand {
  id: number
  user_id: number
  group_id?: number | null
  name: string
  color: string
  created_at?: string | null
  updated_at?: string | null
}

export interface ChannelProcessingConfig {
  process_enabled?: boolean
  processing_description?: string | null
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string | null
  summarize_enabled?: boolean
  summarize_min_length?: number
  classification_enabled?: boolean
  classification_categories?: string[]
}

export interface ChannelAlertDelivery {
  channel_to_post?: string | null
  channel_to_post_title?: string | null
  alert_text?: string | null
  include_ai_summary?: boolean
}

export interface ChannelAlertRule {
  id: string
  enabled?: boolean
  priority?: number
  save_conditions?: string[]
  conditions_mode?: 'any_of' | 'all_of'
  category_filter?: string | null
  dedup_window_sec?: number
  rate_limit_per_hour?: number | null
  time_windows?: { start: string; end: string }[]
  min_text_length?: number
  sentiment_filter?: 'positive' | 'negative' | 'neutral' | null
  tags?: string[]
  stop_on_match?: boolean
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
  processing?: ChannelProcessingConfig
  alert_delivery?: ChannelAlertDelivery
  alert_rules?: ChannelAlertRule[]
  brand_name?: string
  brand_color?: string
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
}

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
}

export interface BestTimeSlot {
  weekday: number
  hour: number
  score: number
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

