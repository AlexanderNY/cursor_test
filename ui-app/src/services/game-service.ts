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
  GameMediaAsset,
  GameMediaUpdate,
  GameLeaderboardEntry,
  GameSessionStats,
  GameBot,
  GameBotCreate,
  GameBotUpdate,
  GameMenuNode,
  GameMenuNodeCreate,
  GameMenuNodeUpdate,
  GameMenuOrder,
} from '@/types/game'

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function isRateLimitError(message: string): boolean {
  const normalized = message.toLowerCase()
  return normalized.includes('rate limit') || normalized.includes('429')
}

export const gameService = {
  async listBots(): Promise<GameBot[]> {
    try {
      const response = await apiClient.get<GameBot[]>('/tg/game/admin/bots')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createBot(body: GameBotCreate): Promise<GameBot> {
    try {
      const response = await apiClient.post<GameBot>('/tg/game/admin/bots', body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateBot(botId: number, body: GameBotUpdate): Promise<GameBot> {
    try {
      const response = await apiClient.patch<GameBot>(`/tg/game/admin/bots/${botId}`, body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteBot(botId: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/game/admin/bots/${botId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async listModes(includeInactive = true, botId?: number): Promise<GameMode[]> {
    try {
      const botParam = botId ? `&bot_id=${botId}` : ''
      const response = await apiClient.get<GameMode[]>(
        `/tg/game/admin/modes?include_inactive=${includeInactive}${botParam}`,
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

  async deleteMode(modeId: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/game/admin/modes/${modeId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async listMenuNodes(modeId: number): Promise<GameMenuNode[]> {
    try {
      const response = await apiClient.get<GameMenuNode[]>(
        `/tg/game/admin/modes/${modeId}/menu-nodes`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createMenuNode(body: GameMenuNodeCreate): Promise<GameMenuNode> {
    try {
      const response = await apiClient.post<GameMenuNode>('/tg/game/admin/menu-nodes', body)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createMenuNodeWithRetry(
    body: GameMenuNodeCreate,
    maxAttempts = 5,
  ): Promise<GameMenuNode> {
    let lastError: Error | null = null
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        return await this.createMenuNode(body)
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Ошибка создания')
        if (!isRateLimitError(lastError.message) || attempt === maxAttempts) {
          throw lastError
        }
        await sleep(1000 * attempt)
      }
    }
    throw lastError ?? new Error('Ошибка создания')
  },

  async updateMenuNode(nodeId: number, body: GameMenuNodeUpdate): Promise<GameMenuNode> {
    try {
      const response = await apiClient.patch<GameMenuNode>(
        `/tg/game/admin/menu-nodes/${nodeId}`,
        body,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteMenuNode(nodeId: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/game/admin/menu-nodes/${nodeId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async listOrders(modeId?: number, botId?: number, limit = 100): Promise<GameMenuOrder[]> {
    try {
      const params = new URLSearchParams({ limit: String(limit) })
      if (modeId) params.set('mode_id', String(modeId))
      if (botId) params.set('bot_id', String(botId))
      const response = await apiClient.get<GameMenuOrder[]>(
        `/tg/game/admin/orders?${params.toString()}`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getOrder(orderId: number): Promise<GameMenuOrder> {
    try {
      const response = await apiClient.get<GameMenuOrder>(`/tg/game/admin/orders/${orderId}`)
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

  async createQuestionWithRetry(
    body: GameQuestionCreate,
    maxAttempts = 5,
  ): Promise<GameQuestion> {
    let lastError: Error | null = null
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        return await this.createQuestion(body)
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Ошибка создания')
        if (!isRateLimitError(lastError.message) || attempt === maxAttempts) {
          throw lastError
        }
        await sleep(1000 * attempt)
      }
    }
    throw lastError ?? new Error('Ошибка создания')
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

  async deleteQuestion(questionId: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/game/admin/questions/${questionId}`)
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

  async listMedia(): Promise<GameMediaAsset[]> {
    try {
      const response = await apiClient.get<GameMediaAsset[]>('/tg/game/admin/media')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async uploadMedia(file: File, title?: string, description?: string): Promise<GameMediaAsset> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (title) formData.append('title', title)
      if (description) formData.append('description', description)
      const response = await apiClient.post<GameMediaAsset>('/tg/game/admin/media', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateMedia(assetId: number, body: GameMediaUpdate): Promise<GameMediaAsset> {
    try {
      const response = await apiClient.patch<GameMediaAsset>(
        `/tg/game/admin/media/${assetId}`,
        body,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteMedia(assetId: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/game/admin/media/${assetId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  mediaPreviewUrl(filename: string): string {
    return `/api/tg/game/media/${encodeURIComponent(filename)}`
  },

  async listLeaderboard(limit = 50): Promise<GameLeaderboardEntry[]> {
    try {
      const response = await apiClient.get<GameLeaderboardEntry[]>(
        `/tg/game/admin/rating?limit=${limit}`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async listSessions(modeId?: number, limit = 100): Promise<GameSessionStats[]> {
    try {
      const modeParam = modeId ? `&mode_id=${modeId}` : ''
      const response = await apiClient.get<GameSessionStats[]>(
        `/tg/game/admin/sessions?limit=${limit}${modeParam}`,
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
