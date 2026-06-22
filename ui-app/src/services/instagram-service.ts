import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  InstagramFollowingUser,
  InstagramProfile,
  InstagramPost,
  InstagramPostListItem,
  InstagramPostFull,
} from '@/types/instagram'

export const instagramService = {
  async getProfile(): Promise<InstagramProfile | null> {
    try {
      const response = await apiClient.get<InstagramProfile>('/instagram/profile')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: Partial<InstagramProfile>): Promise<InstagramProfile> {
    const response = await apiClient.post<InstagramProfile>('/instagram/profile', profile)
    return response.data
  },

  /** Живая проверка входа (instagram-bot); требует JWT, X-User-Id выставляет gateway. */
  async loginTest(followingLimit = 50): Promise<{
    ok: boolean
    message?: string
    instagram_user_id?: number | null
    following?: InstagramFollowingUser[]
    following_count?: number
    auth_method?: 'instagrapi' | 'selenium'
    selenium_status?: string | null
    /** S3 key (содержит diag) и/или base64 PNG без префикса data: при ошибке Selenium */
    selenium_diagnostic_s3_key?: string | null
    selenium_diagnostic_image_base64?: string | null
  }> {
    const response = await apiClient.post<{
      ok: boolean
      message?: string
      instagram_user_id?: number | null
      following?: InstagramFollowingUser[]
      following_count?: number
      auth_method?: 'instagrapi' | 'selenium'
      selenium_status?: string | null
      selenium_diagnostic_image_base64?: string | null
      selenium_diagnostic_s3_key?: string | null
      detail?: string
    }>('/instagram-bot/login-test', {}, {
      params: { following_limit: followingLimit },
      timeout: 320_000,
    })
    return response.data
  },

  async createPost(post: InstagramPost): Promise<unknown> {
    await apiClient.post('/instagram/post', post)
  },

  async createPostWithFiles(formData: FormData): Promise<unknown> {
    await apiClient.post('/instagram/post', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  async getPosts(limit = 50, offset = 0): Promise<InstagramPostListItem[]> {
    const response = await apiClient.get<InstagramPostListItem[]>('/instagram/posts', {
      params: { limit, offset },
    })
    return response.data
  },

  async getPost(id: number): Promise<InstagramPostFull> {
    const response = await apiClient.get<InstagramPostFull>(`/instagram/post/${id}`)
    return response.data
  },

  async updatePost(
    id: number,
    data: { caption?: string; images?: string[]; status?: string }
  ): Promise<InstagramPostFull> {
    const response = await apiClient.put<InstagramPostFull>(`/instagram/post/${id}`, data)
    return response.data
  },

  async deletePost(id: number): Promise<InstagramPostFull> {
    const response = await apiClient.delete<InstagramPostFull>(`/instagram/post/${id}`)
    return response.data
  },
}
