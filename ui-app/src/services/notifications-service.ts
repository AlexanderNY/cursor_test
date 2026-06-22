import { apiClient, getErrorMessage } from './api-client'
import type { Notification, NotificationResponse, NotificationCreate } from '@/types/core'

export const notificationsService = {
  async getNotifications(): Promise<NotificationResponse> {
    try {
      const response = await apiClient.get<NotificationResponse>('/core/notifications')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async createNotification(notification: NotificationCreate): Promise<Notification> {
    try {
      const response = await apiClient.post<Notification>('/core/notifications', notification)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteNotification(notificationId: number): Promise<void> {
    try {
      await apiClient.delete(`/core/notifications/${notificationId}`)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
