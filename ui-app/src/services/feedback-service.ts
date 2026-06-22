import { apiClient, getErrorMessage } from './api-client'
import type { Feedback, FeedbackResponse, FeedbackCreate } from '@/types/core'

export const feedbackService = {
  async submitFeedback(data: FeedbackCreate): Promise<Feedback> {
    try {
      const response = await apiClient.post<Feedback>('/core/feedback', data)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getFeedbackList(): Promise<FeedbackResponse> {
    try {
      const response = await apiClient.get<FeedbackResponse>('/core/feedback')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteFeedback(feedbackId: number): Promise<void> {
    try {
      await apiClient.delete(`/core/feedback/${feedbackId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
