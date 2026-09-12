import { apiClient, getErrorMessage } from './api-client'
import type {
  RoadmapItem,
  RoadmapItemCreate,
  RoadmapItemUpdate,
  RoadmapListResponse,
  RoadmapVoteResponse,
} from '@/types/core'

export const roadmapService = {
  async listItems(): Promise<RoadmapListResponse> {
    try {
      const response = await apiClient.get<RoadmapListResponse>('/core/roadmap')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createItem(data: RoadmapItemCreate): Promise<RoadmapItem> {
    try {
      const response = await apiClient.post<RoadmapItem>('/core/roadmap', data)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateItem(itemId: number, data: RoadmapItemUpdate): Promise<RoadmapItem> {
    try {
      const response = await apiClient.patch<RoadmapItem>(`/core/roadmap/${itemId}`, data)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteItem(itemId: number): Promise<void> {
    try {
      await apiClient.delete(`/core/roadmap/${itemId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async toggleVote(itemId: number): Promise<RoadmapVoteResponse> {
    try {
      const response = await apiClient.post<RoadmapVoteResponse>(`/core/roadmap/${itemId}/vote`)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
