import { apiClient, getErrorMessage } from './api-client'
import type {
  HealthcheckResponse,
  StatisticsResponse,
  UserStatisticsResponse,
  ScheduleResponse,
  ServicesStatusResponse,
  PostsTablesResponse,
  PostsListResponse,
  ProcessorRunResponse,
  PostingDiagnosticsResponse,
  StorageFilesResponse,
  StorageDeleteResponse,
  StoragePresignedUrlResponse,
  RuntimeLocationResponse,
} from '@/types/core'

export const coreService = {
  async getHealthcheck(): Promise<HealthcheckResponse> {
    try {
      const response = await apiClient.get<HealthcheckResponse>('/core/healthchecks')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getStatistics(): Promise<StatisticsResponse> {
    try {
      const response = await apiClient.get<StatisticsResponse>('/core/statistics')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getUsersStatistics(): Promise<UserStatisticsResponse> {
    try {
      const response = await apiClient.get<UserStatisticsResponse>('/core/users-statistics')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getGroupStatistics(): Promise<UserStatisticsResponse> {
    try {
      const response = await apiClient.get<UserStatisticsResponse>('/core/group-statistics')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getSchedule(): Promise<ScheduleResponse> {
    try {
      const response = await apiClient.get<ScheduleResponse>('/core/schedule')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async startDiscovery(): Promise<{ status: string; message: string; changed: boolean }> {
    try {
      const response = await apiClient.post<{ status: string; message: string; changed: boolean }>('/core/start-discovery')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async startBot(platforms: string[]): Promise<{ status: string; message: string; results: Record<string, any> }> {
    try {
      const response = await apiClient.post<{ status: string; message: string; results: Record<string, any> }>('/core/start-bot', { platforms })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getServicesStatus(): Promise<ServicesStatusResponse> {
    try {
      const response = await apiClient.get<ServicesStatusResponse>('/core/admin/services-status')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPostsTablesOverview(): Promise<PostsTablesResponse> {
    try {
      const response = await apiClient.get<PostsTablesResponse>('/core/admin/posts-tables')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPostsList(limit = 500, offset = 0, status?: string): Promise<PostsListResponse> {
    try {
      const response = await apiClient.get<PostsListResponse>('/core/admin/posts', {
        params: { limit, offset, ...(status ? { status } : {}) },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async runProcessorCycle(): Promise<ProcessorRunResponse> {
    try {
      const response = await apiClient.post<ProcessorRunResponse>('/core/admin/processor/run')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async runCollectCycle(): Promise<ProcessorRunResponse> {
    try {
      const response = await apiClient.post<ProcessorRunResponse>('/core/admin/collect/run')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async runDistributeCycle(): Promise<ProcessorRunResponse> {
    try {
      const response = await apiClient.post<ProcessorRunResponse>('/core/admin/distribute/run')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getPostingDiagnostics(): Promise<PostingDiagnosticsResponse> {
    try {
      const response = await apiClient.get<PostingDiagnosticsResponse>('/core/admin/posting-diagnostics')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getStorageFiles(params?: {
    prefix?: string
    limit?: number
    continuation_token?: string
    key_contains?: string
  }): Promise<StorageFilesResponse> {
    try {
      const response = await apiClient.get<StorageFilesResponse>('/core/admin/storage/files', {
        params: params ?? {},
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getStoragePresignedUrl(key: string, expiresIn = 3600): Promise<StoragePresignedUrlResponse> {
    try {
      const response = await apiClient.get<StoragePresignedUrlResponse>('/core/admin/storage/presigned-url', {
        params: { key, expires_in: expiresIn },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async deleteStorageFile(key: string): Promise<StorageDeleteResponse> {
    try {
      const response = await apiClient.delete<StorageDeleteResponse>('/core/admin/storage/files', {
        params: { key },
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getRuntimeLocation(): Promise<RuntimeLocationResponse> {
    try {
      const response = await apiClient.get<RuntimeLocationResponse>('/core/admin/runtime-location')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },
}
