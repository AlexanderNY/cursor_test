import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type { TelegramConfig, TelegramPost, TelegramPostListItem, TelegramPostFull } from '@/types/telegram'
import type { TargetSocialNetworks } from '@/components/target-social-networks'

export interface TgAuthStatus {
  user_id: number
  auth_state: string
  message: string
}

export interface TgAuthResponse {
  success: boolean
  message?: string
  error?: string
  requires_password?: boolean
}

export const telegramService = {
  async getProfile(): Promise<TelegramConfig | null> {
    try {
      const response = await apiClient.get<TelegramConfig>('/tg/profile')
      return response.data
    } catch (error) {
      // Если профиль не найден, возвращаем null
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveConfig(config: TelegramConfig): Promise<void> {
    try {
      await apiClient.post('/tg/profile', config)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createPost(text: string, imageFile?: File, targets?: TargetSocialNetworks): Promise<void> {
    try {
      const formData = new FormData()
      formData.append('text', text)
      if (imageFile) {
        formData.append('image', imageFile)
      }
      if (targets) {
        formData.append('to_tg', String(targets.tg))
        formData.append('to_tw', String(targets.tw))
        formData.append('to_wp', String(targets.wp))
        formData.append('to_vk', String(targets.vk))
        formData.append('to_threads', String(targets.threads))
        formData.append('to_dzen', String(targets.dzen))
        formData.append('to_instagram', String(targets.instagram))
      }

      await apiClient.post('/tg/post', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPosts(): Promise<TelegramPostListItem[]> {
    try {
      const response = await apiClient.get<TelegramPostListItem[]>('/tg/posts')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPost(id: number): Promise<TelegramPostFull> {
    try {
      const response = await apiClient.get<TelegramPostFull>(`/tg/post/${id}`)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updatePost(id: number, text?: string, imageFile?: File): Promise<void> {
    try {
      const formData = new FormData()
      if (text !== undefined) {
        formData.append('text', text)
      }
      if (imageFile) {
        formData.append('image', imageFile)
      }
      
      await apiClient.put(`/tg/post/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deletePost(id: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/post/${id}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getAuthStatus(userId: number): Promise<TgAuthStatus> {
    try {
      const response = await apiClient.get<TgAuthStatus>(`/tg-bot/auth/status/${userId}`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return { user_id: userId, auth_state: 'unknown', message: 'Profile not found' }
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async submitAuthCode(userId: number, code: string): Promise<TgAuthResponse> {
    try {
      const response = await apiClient.post<TgAuthResponse>('/tg-bot/auth/code', { user_id: userId, code })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async submitAuthPassword(userId: number, password: string): Promise<TgAuthResponse> {
    try {
      const response = await apiClient.post<TgAuthResponse>('/tg-bot/auth/password', { user_id: userId, password })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async reloadBot(): Promise<void> {
    try {
      await apiClient.post('/tg-bot/reload')
    } catch (error) {
      // Reload — best-effort; не блокируем пользователя если tg-bot недоступен
      console.warn('tg-bot reload failed (non-critical):', getErrorMessage(error))
    }
  },

  /** Список доступных клиенту каналов (id, title). Требует авторизации и запущенного tg-bot. */
  async getAvailableChannels(userId: number): Promise<Array<{ id: number; title: string }>> {
    const response = await apiClient.get<Array<{ id: number; title: string }>>(`/tg-bot/channels/${userId}`)
    return response.data
  },
}
