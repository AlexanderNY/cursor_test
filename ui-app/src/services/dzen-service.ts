import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  DzenProfile,
  DzenPost,
  DzenPostListItem,
  DzenPostFull,
  DzenVerifyResponse,
} from '@/types/dzen'

export const dzenService = {
  async getProfile(): Promise<DzenProfile | null> {
    try {
      const response = await apiClient.get<DzenProfile>('/dzen/profile')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: Partial<DzenProfile>): Promise<DzenProfile> {
    const response = await apiClient.post<DzenProfile>('/dzen/profile', profile)
    return response.data
  },

  async createPost(post: DzenPost): Promise<unknown> {
    await apiClient.post('/dzen/post', post)
  },

  async createPostWithFiles(formData: FormData): Promise<unknown> {
    await apiClient.post('/dzen/post', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  async getPosts(limit = 50, offset = 0): Promise<DzenPostListItem[]> {
    const response = await apiClient.get<DzenPostListItem[]>('/dzen/posts', {
      params: { limit, offset },
    })
    return response.data
  },

  async getPost(id: number): Promise<DzenPostFull> {
    const response = await apiClient.get<DzenPostFull>(`/dzen/post/${id}`)
    return response.data
  },

  async updatePost(
    id: number,
    data: { text?: string; title?: string; images?: string[]; videos?: string[]; status?: string }
  ): Promise<DzenPostFull> {
    const response = await apiClient.put<DzenPostFull>(`/dzen/post/${id}`, data)
    return response.data
  },

  async deletePost(id: number): Promise<DzenPostFull> {
    const response = await apiClient.delete<DzenPostFull>(`/dzen/post/${id}`)
    return response.data
  },

  async verifyYandexStart(): Promise<DzenVerifyResponse> {
    const response = await apiClient.post<DzenVerifyResponse>('/dzen-bot/verify-yandex/start', {}, { timeout: 180_000 })
    return response.data
  },

  async verifyYandexPushCode(code: string): Promise<DzenVerifyResponse> {
    const response = await apiClient.post<DzenVerifyResponse>(
      '/dzen-bot/verify-yandex/push-code',
      { code: code.trim() },
      { timeout: 300_000 }
    )
    return response.data
  },

  async fetchVerifyPendingDiag(): Promise<{ diag_image_url?: string | null; error?: string | null }> {
    const response = await apiClient.get<{ diag_image_url?: string | null; error?: string | null }>(
      '/dzen-bot/verify-yandex/pending-diag',
      { timeout: 45_000 }
    )
    return response.data
  },
}
