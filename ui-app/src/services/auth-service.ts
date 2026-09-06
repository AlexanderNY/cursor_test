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
  BillingPlanRequest,
  PromoCode,
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

  async getGrowthSummary(limit = 50): Promise<{
    total_registrations: number
    s01_registrations: number
    by_campaign: Array<{ utm_campaign: string; registrations: number }>
  }> {
    const response = await apiClient.get('/auth/admin/growth/summary', {
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

  async createCheckoutSession(plan: 'standard' | 'full'): Promise<string> {
    const response = await apiClient.post<{ url: string }>('/auth/billing/checkout-session', {
      plan,
    })
    return response.data.url
  },

  async createPlanRequest(plan: 'standard' | 'full', promoCode?: string): Promise<BillingPlanRequest> {
    const { data } = await apiClient.post<BillingPlanRequest>('/auth/billing/requests', {
      plan,
      promo_code: promoCode || undefined,
    })
    return data
  },

  async listMyPlanRequests(): Promise<BillingPlanRequest[]> {
    const { data } = await apiClient.get<{ requests: BillingPlanRequest[] }>('/auth/billing/requests')
    return data.requests ?? []
  },

  async previewPromo(code: string, plan: string): Promise<{
    code: string
    discount_percent?: number | null
    discount_amount: number
    list_price: number
    final_price: number
    currency: string
    description?: string | null
  }> {
    const { data } = await apiClient.get('/auth/billing/promo/preview', { params: { code, plan } })
    return data
  },

  async adminCreatePlanRequest(
    userId: number,
    plan: 'free' | 'standard' | 'full',
    promoCode?: string,
  ): Promise<BillingPlanRequest> {
    const { data } = await apiClient.post<BillingPlanRequest>('/auth/billing/admin/requests', {
      user_id: userId,
      plan,
      promo_code: promoCode || undefined,
    })
    return data
  },

  async adminListPlanRequests(status?: string): Promise<BillingPlanRequest[]> {
    const { data } = await apiClient.get<{ requests: BillingPlanRequest[] }>(
      '/auth/billing/admin/requests',
      { params: status ? { status } : undefined },
    )
    return data.requests ?? []
  },

  async adminSendInvoice(requestId: number, paymentNote?: string): Promise<BillingPlanRequest> {
    const { data } = await apiClient.post<BillingPlanRequest>(
      `/auth/billing/admin/requests/${requestId}/invoice`,
      { payment_note: paymentNote || undefined },
    )
    return data
  },

  async adminApplyPlanRequest(requestId: number): Promise<BillingPlanRequest> {
    const { data } = await apiClient.post<BillingPlanRequest>(
      `/auth/billing/admin/requests/${requestId}/apply`,
    )
    return data
  },

  async adminRejectPlanRequest(requestId: number, comment?: string): Promise<BillingPlanRequest> {
    const { data } = await apiClient.post<BillingPlanRequest>(
      `/auth/billing/admin/requests/${requestId}/reject`,
      { comment: comment || undefined },
    )
    return data
  },

  async adminListPromoCodes(): Promise<PromoCode[]> {
    const { data } = await apiClient.get<{ promo_codes: PromoCode[] }>('/auth/billing/admin/promo-codes')
    return data.promo_codes ?? []
  },

  async adminCreatePromoCode(payload: {
    code: string
    description?: string
    discount_percent?: number
    discount_amount?: number
    applies_to_tariff?: string
    max_redemptions?: number
    is_active?: boolean
  }): Promise<PromoCode> {
    const { data } = await apiClient.post<PromoCode>('/auth/billing/admin/promo-codes', payload)
    return data
  },

  async adminUpdatePromoCode(id: number, payload: Partial<PromoCode>): Promise<PromoCode> {
    const { data } = await apiClient.patch<PromoCode>(`/auth/billing/admin/promo-codes/${id}`, payload)
    return data
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
    role_in_group: 'admin' | 'editor' | 'analyst' | 'manager' | 'author' = 'editor'
  ): Promise<void> {
    await apiClient.post(`/auth/groups/${groupId}/members`, { email, role_in_group })
  },

  async createGroupInvite(
    groupId: number,
    data: {
      email?: string
      role_in_group?: 'admin' | 'editor' | 'analyst' | 'manager' | 'author'
      expires_days?: number
    } = {}
  ): Promise<import('@/types/auth').InviteActionResponse> {
    const response = await apiClient.post(`/auth/groups/${groupId}/invites`, {
      email: data.email?.trim() || undefined,
      role_in_group: data.role_in_group ?? 'editor',
      expires_days: data.expires_days ?? 7,
    })
    return response.data
  },

  async listGroupInvites(groupId: number): Promise<import('@/types/auth').GroupInviteResponse[]> {
    const response = await apiClient.get(`/auth/groups/${groupId}/invites`)
    return response.data
  },

  async revokeGroupInvite(groupId: number, inviteId: number): Promise<void> {
    await apiClient.delete(`/auth/groups/${groupId}/invites/${inviteId}`)
  },

  async peekInvite(token: string): Promise<import('@/types/auth').InvitePeekResponse> {
    const response = await apiClient.get(`/auth/groups/invites/${encodeURIComponent(token)}`)
    return response.data
  },

  async acceptInvite(token: string): Promise<import('@/types/auth').AcceptInviteResponse> {
    const response = await apiClient.post(`/auth/groups/invites/${encodeURIComponent(token)}/accept`)
    return response.data
  },

  async removeGroupMember(groupId: number, userId: number): Promise<void> {
    await apiClient.delete(`/auth/groups/${groupId}/members/${userId}`)
  },

  async getAllGroups(): Promise<GroupResponse[]> {
    const response = await apiClient.get<GroupResponse[]>('/auth/groups')
    return response.data
  },
}


