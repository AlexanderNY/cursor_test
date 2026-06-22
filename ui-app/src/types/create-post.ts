export interface CreatePostRequest {
  social_networks: {
    tg?: boolean
    tw?: boolean
    vk?: boolean
    wp?: boolean
    threads?: boolean
    instagram?: boolean
    dzen?: boolean
  }
  text: string
  title?: string
  domain?: string
  url?: string
  author?: string
  avatar?: string
  post_date?: string
  screenshot?: string
  images?: string[]
  image_over_text?: string
  comments?: number
  reposts?: number
  likes?: number
  views?: number
  is_ad?: boolean
  status?: string
}

/** Post from list (table posts, post_type=cpost) — все поля таблицы posts */
export interface CpostPostListItem {
  id: number
  user_id?: number
  domain?: string | null
  url?: string | null
  title?: string | null
  author?: string | null
  avatar?: string | null
  post_date?: string | null
  post_text?: string
  screenshot?: string | null
  images?: string[] | unknown
  image_over_text?: string | null
  comments?: number
  reposts?: number
  likes?: number
  views?: number
  is_ad?: boolean
  status?: string | null
  post_type?: string | null
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
  to_threads?: boolean
  to_dzen?: boolean
  to_instagram?: boolean
  created_at?: string
  updated_at?: string
}

/** Full post for edit (same as list item from API) */
export type CpostPostFull = CpostPostListItem

/** Payload for update (все поля таблицы posts, кроме id, user_id, post_type, created_at, updated_at) */
export interface CpostPostUpdateRequest {
  title?: string
  text?: string
  domain?: string
  url?: string
  author?: string
  avatar?: string
  post_date?: string
  screenshot?: string
  images?: string[]
  image_over_text?: string
  comments?: number
  reposts?: number
  likes?: number
  views?: number
  is_ad?: boolean
  status?: string
  to_tg?: boolean
  to_tw?: boolean
  to_wp?: boolean
  to_vk?: boolean
  to_threads?: boolean
  to_dzen?: boolean
  to_instagram?: boolean
}
