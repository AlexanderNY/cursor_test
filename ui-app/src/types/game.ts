export interface GameOptionInput {
  option_index: number
  option_text: string
  is_correct: boolean
}

export interface GameOption extends GameOptionInput {
  id: number
}

export interface GameMode {
  id: number
  code: string
  title: string
  is_active: boolean
  questions_per_game: number
}

export interface GameModeCreate {
  code: string
  title: string
  questions_per_game: number
  is_active?: boolean
}

export interface GameModeUpdate {
  title?: string
  is_active?: boolean
  questions_per_game?: number
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
