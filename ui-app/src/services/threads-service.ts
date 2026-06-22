import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  ThreadsConfig,
  ThreadsPostListItem,
  ThreadsPostFull,
  ThreadsAuthStatus,
  ThreadsAuthVerify,
  ThreadsSeleniumAttemptResult,
  ThreadsSeleniumSessionRow,
} from '@/types/threads'
import type { TargetSocialNetworks } from '@/components/target-social-networks'

export const threadsService = {
  async getProfile(): Promise<ThreadsConfig | null> {
    try {
      const response = await apiClient.get<ThreadsConfig>('/threads/profile')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveConfig(config: ThreadsConfig): Promise<void> {
    await apiClient.post('/threads/profile', config)
  },

  async createPost(text: string, imageFile?: File, targets?: TargetSocialNetworks): Promise<void> {
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
    }
    await apiClient.post('/threads/post', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  async getPosts(): Promise<ThreadsPostListItem[]> {
    const response = await apiClient.get<ThreadsPostListItem[]>('/threads/posts')
    return response.data
  },

  async getPost(id: number): Promise<ThreadsPostFull> {
    const response = await apiClient.get<ThreadsPostFull>(`/threads/post/${id}`)
    return response.data
  },

  async updatePost(id: number, text?: string, imageFile?: File): Promise<void> {
    const formData = new FormData()
    if (text !== undefined) {
      formData.append('text', text)
    }
    if (imageFile) {
      formData.append('image', imageFile)
    }
    await apiClient.put(`/threads/post/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  async deletePost(id: number): Promise<void> {
    await apiClient.delete(`/threads/post/${id}`)
  },

  async getAuthStatus(userId: number): Promise<ThreadsAuthStatus> {
    try {
      const response = await apiClient.get<ThreadsAuthStatus>(
        `/threads-bot/auth/status/${userId}`
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return {
          user_id: userId,
          connected: false,
          connected_effective: false,
          message: 'Profile not found',
        }
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async verifyAuth(userId: number): Promise<ThreadsAuthVerify> {
    const response = await apiClient.get<ThreadsAuthVerify>(
      `/threads-bot/auth/verify/${userId}`
    )
    return response.data
  },

  async getAuthUrl(): Promise<{ url: string }> {
    const response = await apiClient.get<{ url: string }>('/threads-bot/auth/url')
    return response.data
  },

  async reloadBot(): Promise<void> {
    try {
      await apiClient.post('/threads-bot/reload')
    } catch (error) {
      console.warn('th-bot reload failed (non-critical):', getErrorMessage(error))
    }
  },

  async seleniumAttempt(username: string, password: string): Promise<ThreadsSeleniumAttemptResult> {
    const response = await apiClient.post<ThreadsSeleniumAttemptResult>(
      '/threads-bot/selenium/attempt',
      { username, password },
      { timeout: 180_000 }
    )
    return response.data
  },

  async getSeleniumLastSession(): Promise<{ user_id: number; session: ThreadsSeleniumSessionRow | null }> {
    const response = await apiClient.get<{ user_id: number; session: ThreadsSeleniumSessionRow | null }>(
      '/threads-bot/selenium/session/last'
    )
    return response.data
  },
}
