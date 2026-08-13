import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  TelegramConfig,
  TelegramPostListItem,
  TelegramPostFull,
  TgAnalyticsOverview,
  TgAnalyticsChannelItem,
  TgAnalyticsKeywordItem,
  TgAnalyticsAlertItem,
  TgAnalyticsTimelinePoint,
  TgAnalyticsSentimentBreakdown,
  TgAnalyticsEngagement,
  TgPostTemplate,
} from '@/types/telegram'
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

export interface CreatePostOptions {
  publishAt?: string | null
  targetChannels?: string[]
  targetGroups?: string[]
}

export interface GetPostsParams {
  limit?: number
  offset?: number
  status?: string
  dateFrom?: string
  dateTo?: string
}

export const telegramService = {
  async getProfile(): Promise<TelegramConfig | null> {
    try {
      const response = await apiClient.get<TelegramConfig>('/tg/profile')
      return response.data
    } catch (error) {
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

  async createPost(
    text: string,
    imageFile?: File,
    targets?: TargetSocialNetworks,
    options?: CreatePostOptions,
  ): Promise<void> {
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
      if (options?.publishAt) {
        formData.append('publish_at', options.publishAt)
      }
      if (options?.targetChannels?.length) {
        formData.append('target_channels', JSON.stringify(options.targetChannels))
      }
      if (options?.targetGroups?.length) {
        formData.append('target_groups', JSON.stringify(options.targetGroups))
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

  async getPosts(params?: GetPostsParams): Promise<TelegramPostListItem[]> {
    try {
      const query = new URLSearchParams()
      if (params?.limit != null) query.set('limit', String(params.limit))
      if (params?.offset != null) query.set('offset', String(params.offset))
      if (params?.status) query.set('status', params.status)
      if (params?.dateFrom) query.set('date_from', params.dateFrom)
      if (params?.dateTo) query.set('date_to', params.dateTo)
      const qs = query.toString()
      const response = await apiClient.get<TelegramPostListItem[]>(
        `/tg/posts${qs ? `?${qs}` : ''}`,
      )
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

  async updatePost(
    id: number,
    text?: string,
    imageFile?: File,
    options?: {
      publishAt?: string | null
      clearPublishAt?: boolean
      targetChannels?: string[]
      status?: string
    },
  ): Promise<void> {
    try {
      const formData = new FormData()
      if (text !== undefined) {
        formData.append('text', text)
      }
      if (imageFile) {
        formData.append('image', imageFile)
      }
      if (options?.clearPublishAt) {
        formData.append('clear_publish_at', 'true')
      } else if (options?.publishAt) {
        formData.append('publish_at', options.publishAt)
      }
      if (options?.targetChannels) {
        formData.append('target_channels', JSON.stringify(options.targetChannels))
      }
      if (options?.status) {
        formData.append('status', options.status)
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

  async approvePost(id: number, publishAt?: string | null): Promise<void> {
    try {
      const formData = new FormData()
      if (publishAt) {
        formData.append('publish_at', publishAt)
      }
      await apiClient.post(`/tg/post/${id}/approve`, formData)
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

  async editPublishedPost(userId: number, postId: number, text: string): Promise<void> {
    try {
      await apiClient.post(`/tg-bot/published/${postId}/edit`, {
        user_id: userId,
        text,
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deletePublishedPost(userId: number, postId: number): Promise<void> {
    try {
      await apiClient.post(`/tg-bot/published/${postId}/delete`, {
        user_id: userId,
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getTemplates(): Promise<TgPostTemplate[]> {
    try {
      const response = await apiClient.get<TgPostTemplate[]>('/tg/templates')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createTemplate(name: string, text: string, hashtags = ''): Promise<TgPostTemplate> {
    try {
      const response = await apiClient.post<TgPostTemplate>('/tg/templates', {
        name,
        text,
        hashtags,
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteTemplate(id: number): Promise<void> {
    try {
      await apiClient.delete(`/tg/templates/${id}`)
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
      const response = await apiClient.post<TgAuthResponse>('/tg-bot/auth/code', {
        user_id: userId,
        code,
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async submitAuthPassword(userId: number, password: string): Promise<TgAuthResponse> {
    try {
      const response = await apiClient.post<TgAuthResponse>('/tg-bot/auth/password', {
        user_id: userId,
        password,
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async reloadBot(): Promise<void> {
    try {
      await apiClient.post('/tg-bot/reload')
    } catch (error) {
      console.warn('tg-bot reload failed (non-critical):', getErrorMessage(error))
    }
  },

  async getAvailableChannels(userId: number): Promise<Array<{ id: number; title: string }>> {
    const response = await apiClient.get<Array<{ id: number; title: string }>>(
      `/tg-bot/channels/${userId}`,
    )
    return response.data
  },

  async getAnalyticsOverview(period = '7d'): Promise<TgAnalyticsOverview> {
    const response = await apiClient.get<TgAnalyticsOverview>(
      `/tg/analytics/overview?period=${period}`,
    )
    return response.data
  },

  async getAnalyticsChannels(period = '7d', limit = 10): Promise<TgAnalyticsChannelItem[]> {
    const response = await apiClient.get<TgAnalyticsChannelItem[]>(
      `/tg/analytics/channels?period=${period}&limit=${limit}`,
    )
    return response.data
  },

  async getAnalyticsKeywords(period = '7d', limit = 20): Promise<TgAnalyticsKeywordItem[]> {
    const response = await apiClient.get<TgAnalyticsKeywordItem[]>(
      `/tg/analytics/keywords?period=${period}&limit=${limit}`,
    )
    return response.data
  },

  async getAnalyticsAlerts(period = '7d', limit = 10): Promise<TgAnalyticsAlertItem[]> {
    const response = await apiClient.get<TgAnalyticsAlertItem[]>(
      `/tg/analytics/alerts?period=${period}&limit=${limit}`,
    )
    return response.data
  },

  async getAnalyticsTimeline(
    period = '7d',
    granularity = 'hour',
  ): Promise<TgAnalyticsTimelinePoint[]> {
    const response = await apiClient.get<TgAnalyticsTimelinePoint[]>(
      `/tg/analytics/timeline?period=${period}&granularity=${granularity}`,
    )
    return response.data
  },

  async getAnalyticsSentiment(period = '7d'): Promise<TgAnalyticsSentimentBreakdown> {
    const response = await apiClient.get<TgAnalyticsSentimentBreakdown>(
      `/tg/analytics/sentiment?period=${period}`,
    )
    return response.data
  },

  async getAnalyticsEngagement(period = '7d', limit = 10): Promise<TgAnalyticsEngagement> {
    const response = await apiClient.get<TgAnalyticsEngagement>(
      `/tg/analytics/engagement?period=${period}&limit=${limit}`,
    )
    return response.data
  },
}
