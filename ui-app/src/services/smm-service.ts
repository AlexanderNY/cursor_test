import { apiClient } from './api-client'
import type {
  AnalyticsOverview,
  AnalyticsPost,
  AutomationRule,
  BestTimeSlot,
  Brand,
  BrandChannel,
  InboxItem,
  PublishJob,
} from '@/types/smm'

export const smmService = {
  async getPalette(): Promise<{
    colors: string[]
    max_own_channels: number
    tariff?: string
    limits?: Record<string, unknown>
  }> {
    const { data } = await apiClient.get('/smm/palette')
    return data
  },

  async getPlan(): Promise<{
    tariff: string
    limits: {
      features?: Record<string, boolean>
      max_targets_per_job?: number
      schedule_horizon_days?: number
      [key: string]: unknown
    }
  }> {
    const { data } = await apiClient.get('/smm/plan')
    return data
  },

  async listBrands(): Promise<Brand[]> {
    const { data } = await apiClient.get('/smm/brands')
    return data.brands ?? []
  },

  async createBrand(payload: { name: string; color: string; group_id?: number }): Promise<Brand> {
    const { data } = await apiClient.post('/smm/brands', payload)
    return data
  },

  async updateBrand(
    id: number,
    payload: { name?: string; color?: string; group_id?: number | null },
  ): Promise<Brand> {
    const { data } = await apiClient.patch(`/smm/brands/${id}`, payload)
    return data
  },

  async deleteBrand(id: number): Promise<void> {
    await apiClient.delete(`/smm/brands/${id}`)
  },

  async listChannels(brandId: number): Promise<BrandChannel[]> {
    const { data } = await apiClient.get(`/smm/brands/${brandId}/channels`)
    return data.channels ?? []
  },

  async listAllChannels(brandId?: number): Promise<(BrandChannel & { brand_name?: string; brand_color?: string })[]> {
    const { data } = await apiClient.get('/smm/channels', {
      params: brandId ? { brand_id: brandId } : undefined,
    })
    return data.channels ?? []
  },

  async updateChannel(
    brandId: number,
    channelId: number,
    payload: Partial<{
      title: string
      kind: string
      role: string
      color_override: string
      external_id: string
      publish_enabled: boolean
      collect_enabled: boolean
      discussion_external_id: string | null
      discussion_title: string | null
      comments_collect_enabled: boolean
    }>,
  ): Promise<BrandChannel> {
    const { data } = await apiClient.patch(`/smm/brands/${brandId}/channels/${channelId}`, payload)
    return data
  },

  async addChannel(
    brandId: number,
    payload: {
      network: 'tg' | 'vk'
      external_id: string
      title?: string
      kind?: string
      role?: string
      color_override?: string
    },
  ): Promise<BrandChannel> {
    const { data } = await apiClient.post(`/smm/brands/${brandId}/channels`, payload)
    return data
  },

  async deleteChannel(brandId: number, channelId: number): Promise<void> {
    await apiClient.delete(`/smm/brands/${brandId}/channels/${channelId}`)
  },

  async listInbox(params?: {
    brand_id?: number
    network?: string
    type?: string
    status?: string
    limit?: number
    cursor?: number
  }): Promise<{ items: InboxItem[]; next_cursor?: number | null }> {
    const { data } = await apiClient.get('/smm/inbox', { params })
    return data
  },

  async markInboxRead(id: number): Promise<InboxItem> {
    const { data } = await apiClient.post(`/smm/inbox/${id}/read`)
    return data
  },

  async archiveInbox(id: number): Promise<InboxItem> {
    const { data } = await apiClient.post(`/smm/inbox/${id}/archive`)
    return data
  },

  async replyInbox(id: number, text: string): Promise<InboxItem> {
    const { data } = await apiClient.post(`/smm/inbox/${id}/reply`, { text })
    return data
  },

  async editInbox(id: number, edited_text: string): Promise<InboxItem> {
    const { data } = await apiClient.patch(`/smm/inbox/${id}`, { edited_text })
    return data
  },

  async redirectInbox(
    id: number,
    payload: {
      targets: { network: string; external_id: string }[]
      use_edited?: boolean
      publish_at?: string | null
      pending_approval?: boolean
    },
  ): Promise<{ job: PublishJob; inbox_item: InboxItem }> {
    const { data } = await apiClient.post(`/smm/inbox/${id}/redirect`, payload)
    return data
  },

  async channelStats(brandId?: number | null, period = '7d'): Promise<{
    channels: {
      channel_id: number
      network: string
      external_id: string
      title?: string
      sent: number
      received: number
      failed: number
      role?: string
    }[]
    period: string
  }> {
    const { data } = await apiClient.get('/smm/analytics/channel-stats', {
      params: { brand_id: brandId ?? undefined, period },
    })
    return data
  },

  async runDueJobs(limit = 50): Promise<{ processed: number }> {
    const { data } = await apiClient.post('/smm/jobs/run-due', null, { params: { limit } })
    return data
  },

  async approveJob(id: number): Promise<PublishJob> {
    const { data } = await apiClient.post(`/smm/jobs/${id}/approve`)
    return data
  },

  async createJob(payload: {
    brand_id?: number | null
    text: string
    media_urls?: string[]
    targets?: { network: string; external_id: string }[]
    publish_at?: string | null
    adapt?: boolean
    status?: string
    adapter_overrides?: Record<string, { text?: string }>
  }): Promise<PublishJob> {
    const { data } = await apiClient.post('/smm/jobs', payload)
    return data
  },

  async listJobs(params?: {
    brand_id?: number
    from?: string
    to?: string
  }): Promise<PublishJob[]> {
    const { data } = await apiClient.get('/smm/jobs', { params })
    return data.jobs ?? []
  },

  async updateJob(
    id: number,
    payload: {
      source_text?: string
      media?: string[]
      targets?: { network: string; external_id: string }[]
      publish_at?: string | null
      status?: string
    },
  ): Promise<PublishJob> {
    const { data } = await apiClient.patch(`/smm/jobs/${id}`, payload)
    return data
  },

  async importCsv(file: File, brandId?: number | null): Promise<{
    created: number
    job_ids: number[]
    errors: { line: number; error: string }[]
  }> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/smm/jobs/import-csv', form, {
      params: brandId ? { brand_id: brandId } : undefined,
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async listAutomations(brandId?: number): Promise<AutomationRule[]> {
    const { data } = await apiClient.get('/smm/automations', {
      params: brandId ? { brand_id: brandId } : undefined,
    })
    return data.automations ?? []
  },

  async createAutomation(payload: {
    brand_id: number
    type: string
    config: Record<string, unknown>
    enabled?: boolean
  }): Promise<AutomationRule> {
    const { data } = await apiClient.post('/smm/automations', payload)
    return data
  },

  async updateAutomation(
    id: number,
    payload: Partial<{ brand_id: number; type: string; config: Record<string, unknown>; enabled: boolean }>,
  ): Promise<AutomationRule> {
    const { data } = await apiClient.patch(`/smm/automations/${id}`, payload)
    return data
  },

  async deleteAutomation(id: number): Promise<void> {
    await apiClient.delete(`/smm/automations/${id}`)
  },

  async analyticsOverview(brandId?: number | null, period = '7d'): Promise<AnalyticsOverview> {
    const { data } = await apiClient.get('/smm/analytics/overview', {
      params: { brand_id: brandId ?? undefined, period },
    })
    return data
  },

  async analyticsPosts(brandId?: number | null, sort = 'er'): Promise<AnalyticsPost[]> {
    const { data } = await apiClient.get('/smm/analytics/posts', {
      params: { brand_id: brandId ?? undefined, sort },
    })
    return data.posts ?? []
  },

  async bestTimes(brandId?: number | null, channelId?: number | null): Promise<{
    slots: BestTimeSlot[]
  }> {
    const { data } = await apiClient.get('/smm/analytics/best-times', {
      params: {
        brand_id: brandId ?? undefined,
        channel_id: channelId ?? undefined,
      },
    })
    return data
  },

  async addCompetitor(payload: {
    brand_id: number
    network: 'tg' | 'vk'
    external_id: string
    title?: string
    kind?: string
  }): Promise<BrandChannel> {
    const { data } = await apiClient.post('/smm/competitors', payload)
    return data
  },

  async competitorPosts(channelId: number): Promise<unknown[]> {
    const { data } = await apiClient.get(`/smm/competitors/${channelId}/posts`)
    return data.posts ?? []
  },

  async aiSummarize(text: string, maxLen = 500): Promise<{ summary: string; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/summarize', { text, max_len: maxLen })
    return data
  },

  async aiRewrite(
    text: string,
    opts?: { tone?: string; network?: string },
  ): Promise<{ text: string; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/rewrite', { text, ...opts })
    return data
  },

  async aiAdapt(
    text: string,
    targets: string[] = ['tg', 'vk'],
  ): Promise<{ variants: Record<string, string>; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/adapt', { text, targets })
    return data
  },
}
