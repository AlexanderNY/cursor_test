export interface GameOptionInput {
  option_index: number
  option_text: string
  is_correct: boolean
}

export interface GameOption extends GameOptionInput {
  id: number
}

export type GameModeType = 'quiz' | 'menu'

export interface GameMode {
  id: number
  bot_id: number
  code: string
  title: string
  is_active: boolean
  questions_per_game: number
  mode_type: GameModeType
}

export interface GameModeCreate {
  bot_id: number
  code: string
  title: string
  questions_per_game?: number
  is_active?: boolean
  mode_type?: GameModeType
}

export interface GameModeUpdate {
  title?: string
  is_active?: boolean
  questions_per_game?: number
  mode_type?: GameModeType
}

export interface GameQuestion {
  id: number
  mode_id: number
  prompt_text: string
  image_file_id?: string | null
  image_url?: string | null
  is_active: boolean
}

export interface GameQuestionDetail extends GameQuestion {
  options: GameOption[]
}

export interface GameQuestionCreate {
  mode_id: number
  prompt_text: string
  image_file_id?: string | null
  image_url?: string | null
  options: GameOptionInput[]
}

export interface GameQuestionUpdate {
  prompt_text?: string
  image_file_id?: string | null
  image_url?: string | null
  is_active?: boolean
}

export interface GameMediaAsset {
  id: number
  filename: string
  s3_key: string
  original_filename?: string | null
  title: string
  description?: string | null
  content_type?: string | null
  size_bytes: number
  created_at: string
  public_url: string
}

export interface GameMediaUpdate {
  title?: string
  description?: string | null
}

export interface GameLeaderboardEntry {
  telegram_user_id: number
  username?: string | null
  score: number
  correct_count: number
  total_questions: number
  duration_sec?: number | null
  finished_at?: string | null
}

export interface GameSessionStats {
  session_id: number
  telegram_user_id: number
  username?: string | null
  first_name?: string | null
  mode_id: number
  mode_title: string
  correct_count: number
  total_questions: number
  score: number
  duration_sec?: number | null
  finished_at?: string | null
}

export interface GameBot {
  id: number
  name: string
  username?: string | null
  token: string
  token_masked: string
  is_active: boolean
  is_polling: boolean
  created_at?: string | null
}

export interface GameBotCreate {
  name: string
  token: string
  is_active?: boolean
}

export interface GameBotUpdate {
  name?: string
  token?: string
  is_active?: boolean
}

export type DiagnosticStatus = 'ok' | 'warning' | 'error'

export interface DiagnosticCheck {
  key: string
  label: string
  status: DiagnosticStatus
  message: string
}

export interface GameBotDiagnostics {
  bot_id: number
  bot_name: string
  collected_at: string
  overall_status: DiagnosticStatus
  checks: DiagnosticCheck[]
  hints: string[]
}

export interface GameMenuNode {
  id: number
  mode_id: number
  parent_id?: number | null
  title: string
  body_text?: string | null
  image_url?: string | null
  image_file_id?: string | null
  price: number
  sort_order: number
  is_active: boolean
}

export interface GameMenuNodeCreate {
  mode_id: number
  parent_id?: number | null
  title: string
  body_text?: string | null
  image_url?: string | null
  sort_order?: number
  is_active?: boolean
  price?: number
}

export interface GameMenuNodeUpdate {
  parent_id?: number | null
  title?: string
  body_text?: string | null
  image_url?: string | null
  sort_order?: number
  is_active?: boolean
  price?: number
}

export interface GameMenuOrderItem {
  id: number
  node_id?: number | null
  title: string
  quantity: number
  unit_price?: number
  line_total?: number
}

export interface GameMenuOrder {
  id: number
  order_number: string
  bot_id: number
  mode_id: number
  mode_title: string
  telegram_user_id: number
  username?: string | null
  first_name?: string | null
  status: string
  created_at?: string | null
  total_amount?: number
  total_quantity: number
  items?: GameMenuOrderItem[]
}
