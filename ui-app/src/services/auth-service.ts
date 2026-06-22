import { apiClient, getErrorMessage } from './api-client'
import type { 
  TokenResponse, 
  User, 
  UserRole,
  LoginCredentials, 
  RegisterCredentials, 
  ProfileUpdate,
  RoleTariffHistoryEntry,
  GroupResponse,
  BillingPlanDefinition,
  BillingMeResponse,
  BillingEventRow,
  AdminAuditLogEntry,
} from '@/types'

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    try {
      const response = await apiClient.post<TokenResponse>('/auth/login', credentials)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async register(credentials: RegisterCredentials): Promise<TokenResponse> {
    try {
      const response = await apiClient.post<TokenResponse>('/auth/register', credentials)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async logout(refreshToken: string): Promise<void> {
    try {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async logoutAll(): Promise<void> {
    try {
      await apiClient.post('/auth/all-logout')
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getProfile(): Promise<User> {
    try {
      const response = await apiClient.get<User>('/auth/profile')
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async updateProfile(data: ProfileUpdate): Promise<User> {
    try {
      const response = await apiClient.post<User>('/auth/profile', data)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async resetPassword(email: string): Promise<void> {
    try {
      await apiClient.post('/auth/reset-password', { email })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    try {
      await apiClient.post('/auth/reset-password/confirm', { 
        token, 
        new_password: newPassword 
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async refreshTokens(refreshToken: string): Promise<TokenResponse> {
    try {
      const response = await apiClient.post<TokenResponse>('/auth/refresh', { 
        refresh_token: refreshToken 
      })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async verifyEmail(code: string): Promise<void> {
    try {
      await apiClient.post('/auth/verify', { code })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getUsers(params?: { tariff?: string; subscription_status?: string }): Promise<User[]> {
    try {
      const response = await apiClient.get<User[]>('/auth/users', { params })
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async exportUsersCsv(params?: { tariff?: string; subscription_status?: string }): Promise<void> {
    try {
      const response = await apiClient.get('/auth/users/export', {
        params,
        responseType: 'blob',
      })
      const blob = response.data as Blob
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'users_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getAdminAuditLog(limit = 100): Promise<AdminAuditLogEntry[]> {
    const response = await apiClient.get<AdminAuditLogEntry[]>('/auth/admin/audit-log', {
      params: { limit },
    })
    return response.data
  },

  async getBillingPlans(): Promise<BillingPlanDefinition[]> {
    const response = await apiClient.get<{ plans: BillingPlanDefinition[] }>('/auth/billing/plans')
    return response.data.plans
  },

  async getBillingMe(): Promise<BillingMeResponse> {
    const response = await apiClient.get<BillingMeResponse>('/auth/billing/me')
    return response.data
  },

  async getBillingEvents(limit = 50): Promise<BillingEventRow[]> {
    const response = await apiClient.get<BillingEventRow[]>('/auth/billing/events', {
      params: { limit },
    })
    return response.data
  },

  async createBillingPortalSession(): Promise<string> {
    const response = await apiClient.post<{ url: string }>('/auth/billing/customer-portal', {})
    return response.data.url
  },

  async updateUser(
    userId: number,
    data: { role?: UserRole; tariff?: string; is_blocked?: boolean }
  ): Promise<User> {
    try {
      const response = await apiClient.patch<User>(`/auth/users/${userId}`, data)
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getRoleTariffHistory(userId: number): Promise<RoleTariffHistoryEntry[]> {
    try {
      const response = await apiClient.get<RoleTariffHistoryEntry[]>(
        `/auth/users/${userId}/role-tariff-history`
      )
      return response.data
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  },

  async getMyGroup(): Promise<GroupResponse> {
    const response = await apiClient.get<GroupResponse>('/auth/groups/my')
    return response.data
  },

  async createGroup(name: string, description?: string): Promise<GroupResponse> {
    const response = await apiClient.post<GroupResponse>('/auth/groups', {
      name,
      ...(description?.trim() ? { description: description.trim() } : {}),
    })
    return response.data
  },

  async createGroupAsAdmin(name: string, description?: string): Promise<GroupResponse> {
    const response = await apiClient.post<GroupResponse>('/auth/groups/admin', {
      name,
      ...(description?.trim() ? { description: description.trim() } : {}),
    })
    return response.data
  },

  async updateGroup(
    groupId: number,
    data: { name?: string; description?: string | null }
  ): Promise<GroupResponse> {
    const payload: Record<string, string> = {}
    if (data.name !== undefined) payload.name = data.name
    if (data.description !== undefined) payload.description = data.description ?? ''
    const response = await apiClient.patch<GroupResponse>(`/auth/groups/${groupId}`, payload)
    return response.data
  },

  async addGroupMember(
    groupId: number,
    email: string,
    role_in_group: 'manager' | 'author' = 'author'
  ): Promise<void> {
    await apiClient.post(`/auth/groups/${groupId}/members`, { email, role_in_group })
  },

  async removeGroupMember(groupId: number, userId: number): Promise<void> {
    await apiClient.delete(`/auth/groups/${groupId}/members/${userId}`)
  },

  async getAllGroups(): Promise<GroupResponse[]> {
    const response = await apiClient.get<GroupResponse[]>('/auth/groups')
    return response.data
  },
}


