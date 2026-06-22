import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  VKontakteProfile,
  VKontaktePost,
  VKontaktePostListItem,
  VKontaktePostFull,
  VKAuthStatus,
  VKSubscriptionsResult,
  VKSeleniumVerifyResponse,
} from '@/types/vkontakte'

export const vkontakteService = {
  async getProfile(): Promise<VKontakteProfile | null> {
    try {
      const response = await apiClient.get<VKontakteProfile>('/vk/profile')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: Partial<VKontakteProfile>): Promise<VKontakteProfile> {
    const response = await apiClient.post<VKontakteProfile>('/vk/profile', profile)
    return response.data
  },

  async createPost(post: VKontaktePost): Promise<unknown> {
    await apiClient.post('/vk/post', post)
  },

  async getPosts(limit = 50, offset = 0): Promise<VKontaktePostListItem[]> {
    const response = await apiClient.get<VKontaktePostListItem[]>('/vk/posts', {
      params: { limit, offset },
    })
    return response.data
  },

  async getPost(id: number): Promise<VKontaktePostFull> {
    const response = await apiClient.get<VKontaktePostFull>(`/vk/post/${id}`)
    return response.data
  },

  async updatePost(
    id: number,
    data: { text?: string; images?: string[]; attachments?: unknown[]; status?: string }
  ): Promise<VKontaktePostFull> {
    const response = await apiClient.put<VKontaktePostFull>(`/vk/post/${id}`, data)
    return response.data
  },

  async deletePost(id: number): Promise<VKontaktePostFull> {
    const response = await apiClient.delete<VKontaktePostFull>(`/vk/post/${id}`)
    return response.data
  },

  /**
   * Загружает изображение с ПК. Возвращает относительный путь (/vk/uploads/xxx) для сохранения в посте.
   * vk-bot скачивает файл по CORE_SERVICE_URL + путь. Превью в UI строится из origin + baseURL + путь.
   */
  async uploadImage(file: File): Promise<string> {
    const formData = new FormData()
    formData.append('image', file)
    const response = await apiClient.post<{ url: string }>('/vk/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const path = response.data.url
    return path.startsWith('/') ? path : `/${path}`
  },

  /** URL редиректа на oauth.vk.com (требуется JWT, X-User-Id через gateway). */
  async getAuthUrl(): Promise<{ url: string }> {
    const response = await apiClient.get<{ url: string }>('/vk/oauth/url')
    return response.data
  },

  /** Статус сохранённого пользовательского OAuth-токена VK. */
  async getAuthStatus(_userId?: number): Promise<VKAuthStatus> {
    const response = await apiClient.get<VKAuthStatus>('/vk/oauth/status')
    return response.data
  },

  /** Подписки на сообщества (OAuth) или проверка групп по токену сообщества (groups.getById). */
  async getSubscriptions(): Promise<VKSubscriptionsResult> {
    const response = await apiClient.get<VKSubscriptionsResult>('/vk/subscriptions')
    return response.data
  },

  /** Резервный вход: Selenium + веб-парсинг сообществ (vk-bot). Пароль не хранится на клиенте после запроса. */
  async verifySelenium(login: string, password: string): Promise<VKSeleniumVerifyResponse> {
    const response = await apiClient.post<VKSeleniumVerifyResponse>(
      '/vk-bot/verify-selenium',
      { login, password },
      { timeout: 240_000 }
    )
    return response.data
  },
}
