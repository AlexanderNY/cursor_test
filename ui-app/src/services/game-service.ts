import { apiClient, getErrorMessage } from './api-client'
import type {
  GameMode,
  GameModeCreate,
  GameModeUpdate,
  GameQuestion,
  GameQuestionCreate,
  GameQuestionDetail,
  GameQuestionUpdate,
  GameOptionInput,
} from '@/types/game'

export const gameService = {
  async listModes(includeInactive = true): Promise<GameMode[]> {
    try {
      const response = await apiClient.get<GameMode[]>(
        `/tg/game/admin/modes?include_inactive=${includeInactive}`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createMode(body: GameModeCreate): Promise<GameMode> {
    try {
      const response = await apiClient.post<GameMode>('/tg/game/admin/modes', body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateMode(modeId: number, body: GameModeUpdate): Promise<GameMode> {
    try {
      const response = await apiClient.patch<GameMode>(`/tg/game/admin/modes/${modeId}`, body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async listQuestions(modeId: number): Promise<GameQuestion[]> {
    try {
      const response = await apiClient.get<GameQuestion[]>(
        `/tg/game/admin/modes/${modeId}/questions`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getQuestion(questionId: number): Promise<GameQuestionDetail> {
    try {
      const response = await apiClient.get<GameQuestionDetail>(
        `/tg/game/admin/questions/${questionId}`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createQuestion(body: GameQuestionCreate): Promise<GameQuestion> {
    try {
      const response = await apiClient.post<GameQuestion>('/tg/game/admin/questions', body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateQuestion(questionId: number, body: GameQuestionUpdate): Promise<GameQuestion> {
    try {
      const response = await apiClient.patch<GameQuestion>(
        `/tg/game/admin/questions/${questionId}`,
        body,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async replaceOptions(questionId: number, options: GameOptionInput[]): Promise<void> {
    try {
      await apiClient.put(`/tg/game/admin/questions/${questionId}/options`, { options })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
