import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  TwitterProfile,
  TwitterPost,
  TwPostRow,
  TwitterOAuthStatus,
  TwitterFollowingResponse,
  TwitterSeleniumVerifyResponse,
} from '@/types/twitter'

export const twitterService = {
  async getProfile(): Promise<TwitterProfile | null> {
    try {
      const response = await apiClient.get<TwitterProfile>('/tw/profile')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: TwitterProfile): Promise<void> {
    try {
      await apiClient.post('/tw/profile', profile)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createPost(post: TwitterPost): Promise<void> {
    try {
      await apiClient.post('/tw/post', post)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPosts(limit = 50, offset = 0): Promise<TwPostRow[]> {
    try {
      const response = await apiClient.get<TwPostRow[]>('/tw/posts', {
        params: { limit, offset },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getOAuthUrl(): Promise<string> {
    const response = await apiClient.get<{ url: string }>('/tw/oauth/url')
    return response.data.url
  },

  async getOAuthStatus(): Promise<TwitterOAuthStatus> {
    const response = await apiClient.get<TwitterOAuthStatus>('/tw/oauth/status')
    return response.data
  },

  async getFollowing(params?: {
    max_results?: number
    pagination_token?: string
  }): Promise<TwitterFollowingResponse> {
    try {
      const response = await apiClient.get<TwitterFollowingResponse>('/tw/following', {
        params: {
          max_results: params?.max_results ?? 50,
          pagination_token: params?.pagination_token,
        },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  /** Проверка входа через Selenium (tw-bot); учётные данные только из БД; до ~5 мин. */
  async verifySelenium(): Promise<TwitterSeleniumVerifyResponse> {
    try {
      const response = await apiClient.post<TwitterSeleniumVerifyResponse>(
        '/tw-bot/verify-selenium',
        {},
        { timeout: 300_000 }
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
