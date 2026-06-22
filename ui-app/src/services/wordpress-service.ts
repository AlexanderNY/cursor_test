import { apiClient, getErrorMessage } from './api-client'
import type {
  WordPressProfile,
  WordPressPublishProfile,
  WordPressCollectProfile,
  WordPressPost,
  WordPressPostListItem,
  WordPressPostFull,
} from '@/types/wordpress'

export const wordpressService = {
  /** Объединенный профиль (обратная совместимость) */
  async getProfile(): Promise<WordPressProfile> {
    try {
      const response = await apiClient.get<WordPressProfile>('/wp/profile')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: WordPressProfile): Promise<void> {
    try {
      await apiClient.post('/wp/profile', profile)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPublishProfile(): Promise<WordPressPublishProfile> {
    try {
      const response = await apiClient.get<WordPressPublishProfile>('/wp/publish-profile')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async savePublishProfile(profile: WordPressPublishProfile): Promise<void> {
    try {
      await apiClient.post('/wp/publish-profile', profile)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getCollectProfile(): Promise<WordPressCollectProfile> {
    try {
      const response = await apiClient.get<WordPressCollectProfile>('/wp/collect-profile')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async saveCollectProfile(profile: WordPressCollectProfile): Promise<void> {
    try {
      await apiClient.post('/wp/collect-profile', profile)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createPost(post: WordPressPost): Promise<void> {
    try {
      await apiClient.post('/wp/post', post)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPost(id: number): Promise<WordPressPostFull> {
    try {
      const response = await apiClient.get<WordPressPostFull>(`/wp/post/${id}`)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updatePost(id: number, post: WordPressPost): Promise<void> {
    try {
      await apiClient.put(`/wp/post/${id}`, post)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deletePost(id: number): Promise<void> {
    try {
      await apiClient.delete(`/wp/post/${id}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPosts(): Promise<WordPressPostListItem[]> {
    try {
      const response = await apiClient.get<WordPressPostListItem[]>('/wp/posts')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
