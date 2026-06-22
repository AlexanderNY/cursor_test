export type PublishScheduleType = 'on_new_messages' | 'by_intervals'

export interface TelegramAlertRule {
  enabled: boolean
  chats_to_read: string[]
  save_conditions: string[]
  channel_to_post?: string
  alert_text?: string
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
}

export interface TelegramMessage {
  id: number
  chat_id: number
  text: string
  date: string
  sender_id: number
  sender_name: string
}


