import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type { CustomURLSettings, UrlPostListItem } from '@/types/custom-url'

export const customURLService = {
  async getSettings(): Promise<CustomURLSettings | null> {
    try {
      const response = await apiClient.get<CustomURLSettings>('/curl/settings')
      return response.data
    } catch (error) {
      // Если настройки не найдены, возвращаем null
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveSettings(settings: CustomURLSettings): Promise<void> {
    try {
      await apiClient.post('/curl/settings', settings)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPosts(params?: { limit?: number; offset?: number }): Promise<UrlPostListItem[]> {
    try {
      const response = await apiClient.get<UrlPostListItem[]>('/curl/posts', { params })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
