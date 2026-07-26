export type PublishScheduleType = 'on_new_messages' | 'by_intervals'

export type ConditionsMode = 'any_of' | 'all_of' | 'regex'

export type SentimentFilter = 'positive' | 'negative' | 'neutral'

export interface TelegramAlertRule {
  id?: string
  enabled: boolean
  priority?: number
  chats_to_read: string[]
  save_conditions: string[]
  conditions_mode?: ConditionsMode
  category_filter?: string
  channel_to_post?: string
  alert_text?: string
  dedup_window_sec?: number
  rate_limit_per_hour?: number
  min_text_length?: number
  include_ai_summary?: boolean
  sentiment_filter?: SentimentFilter
  tags?: string[]
  stop_on_match?: boolean
}

export interface TelegramConfig {
  publish_enabled: boolean
  collect_enabled: boolean
  schedule_type?: 'immediate' | 'on_new_messages' | 'by_intervals'
  time_intervals?: TimeInterval[]
  api_id?: string
  api_hash?: string
  telegram_username?: string
  auth_phone_number?: string
  chats_to_read: string[]
  save_conditions: string[]
  channel_to_post?: string
  channels_to_post?: string[]
  alert_enabled?: boolean
  alert_rules?: TelegramAlertRule[]
  process_enabled: boolean
  processing_description?: string
  remove_emojis?: boolean
  remove_images?: boolean
  clean_html?: boolean
  process_services?: string[]
  status_review_after_process?: boolean
  add_static_html?: boolean
  static_html_content?: string
  summarize_enabled?: boolean
  summarize_min_length?: number
  digest_interval_min?: number
  digest_channel?: string
  classification_enabled?: boolean
  classification_categories?: string[]
}

export interface TimeInterval {
  start: string // HH:MM format
  end?: string // HH:MM format (optional for single time point)
}

export interface TelegramPost {
  text: string
  images?: string[]
}

export interface TelegramPostListItem {
  id: number
  post_text: string
  images?: string[]
  status: string
  created_at: string
  updated_at: string
  publish_at?: string | null
  target_channels?: string[]
  telegram_message_id?: number | null
  views?: number
  likes?: number
  comments?: number
  reposts?: number
}

export interface TelegramPostFull {
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
  created_at: string
  updated_at: string
  publish_at?: string | null
  target_channels?: string[]
  telegram_message_id?: number | null
  telegram_chat_id?: string | null
}

export interface TgPostTemplate {
  id: number
  user_id: number
  name: string
  text: string
  hashtags: string
  created_at: string
  updated_at: string
}

export interface TelegramMessage {
  id: number
  chat_id: number
  text: string
  date: string
  sender_id: number
  sender_name: string
}

export interface TgAnalyticsOverview {
  messages_collected: number
  alerts_sent: number
  alerts_suppressed: number
  unique_channels: number
  top_channel?: { chat_id: string; name?: string; count: number } | null
  period: string
}

export interface TgAnalyticsChannelItem {
  chat_id: string
  name?: string
  count: number
}

export interface TgAnalyticsKeywordItem {
  keyword: string
  count: number
}

export interface TgAnalyticsAlertItem {
  rule_id?: string
  alert_text?: string
  chat_id?: string
  event_type: string
  created_at: string
  matched_conditions: string[]
}

export interface TgAnalyticsTimelinePoint {
  bucket: string
  collected: number
  alerts_sent: number
  alerts_suppressed: number
}

export interface TgAnalyticsSentimentBreakdown {
  positive: number
  negative: number
  neutral: number
  total: number
}

export interface TgAnalyticsEngagement {
  total_views: number
  total_likes: number
  total_comments: number
  total_reposts: number
  published_count: number
  avg_er: number
  top_posts: Array<{
    id: number
    post_text: string
    views: number
    likes: number
    comments: number
    reposts: number
    publish_at?: string | null
    created_at: string
  }>
  period: string
}

export type TelegramTab =
  | 'create'
  | 'posts'
  | 'calendar'
  | 'profile'
  | 'processing'
  | 'auth'
  | 'analytics'
