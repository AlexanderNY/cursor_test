import { apiClient, getErrorMessage } from './api-client'
import axios from 'axios'
import type {
  CreatePostRequest,
  CpostPostListItem,
  CpostPostFull,
  CpostPostUpdateRequest,
} from '@/types/create-post'

export interface CreatePostProfile {
  social_networks: {
    tg?: boolean
    tw?: boolean
    vk?: boolean
    wp?: boolean
    threads?: boolean
    instagram?: boolean
    dzen?: boolean
  }
}

/** Backend profile response uses default_platforms */
interface CpostProfileResponse {
  default_platforms?: {
    tg?: boolean
    tw?: boolean
    wp?: boolean
    vk?: boolean
  }
}

/** Backend create post payload — все поля таблицы posts */
interface CpostPostPayload {
  text: string
  title?: string
  domain?: string
  url?: string
  author?: string
  avatar?: string
  post_date?: string
  screenshot?: string
  images?: string[]
  image_over_text?: string
  comments?: number
  reposts?: number
  likes?: number
  views?: number
  is_ad?: boolean
  status?: string
  to_tg: boolean
  to_tw: boolean
  to_wp: boolean
  to_vk: boolean
  to_threads: boolean
  to_dzen: boolean
  to_instagram: boolean
}

export const createPostService = {
  async getProfile(): Promise<CreatePostProfile | null> {
    try {
      const response = await apiClient.get<CpostProfileResponse | CreatePostProfile>('/cpost/profile')
      const data = response.data
      if (!data) return null
      const platforms = 'default_platforms' in data ? data.default_platforms : (data as CreatePostProfile).social_networks
      const sn = platforms ?? { tg: false, tw: false, vk: false, wp: false, threads: false, instagram: false, dzen: false }
      return {
        social_networks: {
          tg: sn.tg ?? false,
          tw: sn.tw ?? false,
          vk: sn.vk ?? false,
          wp: sn.wp ?? false,
          threads: sn.threads ?? false,
          instagram: sn.instagram ?? false,
          dzen: sn.dzen ?? false,
        },
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw new Error(getErrorMessage(error))
    }
  },

  async saveProfile(profile: CreatePostProfile): Promise<void> {
    try {
      await apiClient.post('/cpost/profile', {
        default_platforms: {
          tg: profile.social_networks.tg ?? false,
          tw: profile.social_networks.tw ?? false,
          wp: profile.social_networks.wp ?? false,
          vk: profile.social_networks.vk ?? false,
          threads: profile.social_networks.threads ?? false,
          instagram: profile.social_networks.instagram ?? false,
          dzen: profile.social_networks.dzen ?? false,
        },
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createPost(post: CreatePostRequest): Promise<void> {
    const payload: CpostPostPayload = {
      text: post.text,
      title: post.title,
      domain: post.domain,
      url: post.url,
      author: post.author,
      avatar: post.avatar,
      post_date: post.post_date,
      screenshot: post.screenshot,
      images: post.images?.length ? post.images : undefined,
      image_over_text: post.image_over_text,
      comments: post.comments,
      reposts: post.reposts,
      likes: post.likes,
      views: post.views,
      is_ad: post.is_ad,
      status: post.status,
      to_tg: post.social_networks.tg ?? false,
      to_tw: post.social_networks.tw ?? false,
      to_wp: post.social_networks.wp ?? false,
      to_vk: post.social_networks.vk ?? false,
      to_threads: post.social_networks.threads ?? false,
      to_dzen: post.social_networks.dzen ?? false,
      to_instagram: post.social_networks.instagram ?? false,
    }
    try {
      await apiClient.post('/cpost/post', payload)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPosts(params?: { limit?: number; offset?: number }): Promise<CpostPostListItem[]> {
    const response = await apiClient.get<CpostPostListItem[]>('/cpost/posts', { params })
    return response.data ?? []
  },

  async getPost(postId: number): Promise<CpostPostFull> {
    const response = await apiClient.get<CpostPostFull>(`/cpost/post/${postId}`)
    return response.data
  },

  async updatePost(postId: number, data: CpostPostUpdateRequest): Promise<void> {
    await apiClient.put(`/cpost/post/${postId}`, {
      title: data.title,
      text: data.text,
      domain: data.domain,
      url: data.url,
      author: data.author,
      avatar: data.avatar,
      post_date: data.post_date,
      screenshot: data.screenshot,
      images: data.images,
      image_over_text: data.image_over_text,
      comments: data.comments,
      reposts: data.reposts,
      likes: data.likes,
      views: data.views,
      is_ad: data.is_ad,
      status: data.status,
      to_tg: data.to_tg,
      to_tw: data.to_tw,
      to_wp: data.to_wp,
      to_vk: data.to_vk,
      to_threads: data.to_threads,
      to_dzen: data.to_dzen,
      to_instagram: data.to_instagram,
    })
  },

  async deletePost(postId: number): Promise<void> {
    await apiClient.delete(`/cpost/post/${postId}`)
  },
}
