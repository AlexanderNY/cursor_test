import { apiClient } from './api-client'
import type {
  AiAssistAction,
  AiAssistActionId,
  AiProcessParams,
  AiProcessResponse,
  AnalyticsOverview,
  AnalyticsPost,
  AutomationRule,
  BestTimeSlot,
  Brand,
  BrandChannel,
  ChannelStatsResponse,
  CompetitorCompare,
  CompetitorDigest,
  CompetitorDiff,
  CompetitorPost,
  InboxItem,
  PublishJob,
} from '@/types/smm'

export type ChannelsValidationIssue = {
  channel_id: number
  network?: string
  external_id?: string
  title?: string | null
  role?: string
  severity: 'error' | 'warning'
  code: string
  message: string
}

export type ChannelsValidationResult = {
  ok: boolean
  brand_id: number
  checked: number
  accessible: number
  errors: number
  warnings: number
  issues: ChannelsValidationIssue[]
}

export type ChannelsImportResult = {
  ok: boolean
  created: number
  updated: number
  skipped: number
  total: number
  errors: { index: number; error: string; network?: string; external_id?: string }[]
  warnings: string[]
  validation?: ChannelsValidationResult
}

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

  async createBrand(payload: {
    name: string
    color: string
    group_id?: number
    tone_of_voice?: string
    style_notes?: string
    prompt_snippets?: { title: string; text: string }[]
  }): Promise<Brand> {
    const { data } = await apiClient.post('/smm/brands', payload)
    return data
  },

  async updateBrand(
    id: number,
    payload: {
      name?: string
      color?: string
      group_id?: number | null
      tone_of_voice?: string | null
      style_notes?: string | null
      prompt_snippets?: { title: string; text: string }[]
    },
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

  async exportChannels(brandId?: number | null): Promise<{
    format: string
    version: number
    exported_at: string
    brand_id?: number | null
    channels: Record<string, unknown>[]
  }> {
    const { data } = await apiClient.get('/smm/channels/export', {
      params: brandId ? { brand_id: brandId } : undefined,
    })
    return data
  },

  async importChannels(
    brandId: number,
    payload: { channels: Record<string, unknown>[]; update_existing?: boolean },
  ): Promise<ChannelsImportResult> {
    const { data } = await apiClient.post('/smm/channels/import', payload, {
      params: { brand_id: brandId },
    })
    return data
  },

  async importChannelsFile(
    brandId: number,
    file: File,
    updateExisting = true,
  ): Promise<ChannelsImportResult> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/smm/channels/import-file', form, {
      params: { brand_id: brandId, update_existing: updateExisting },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async validateChannels(
    brandId: number,
    recheckAuth = true,
  ): Promise<ChannelsValidationResult> {
    const { data } = await apiClient.post('/smm/channels/validate', null, {
      params: { brand_id: brandId, recheck_auth: recheckAuth },
    })
    return data
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
      alert_enabled: boolean
      save_conditions: string[]
      conditions_mode: BrandChannel['conditions_mode']
      processing: BrandChannel['processing']
      publish_targets: number[]
      alert_delivery: BrandChannel['alert_delivery']
      alert_rules: BrandChannel['alert_rules']
      url_config: BrandChannel['url_config']
    }>,
  ): Promise<BrandChannel> {
    const { data } = await apiClient.patch(`/smm/brands/${brandId}/channels/${channelId}`, payload)
    return data
  },

  async getChannel(channelId: number): Promise<BrandChannel> {
    const { data } = await apiClient.get(`/smm/channels/${channelId}`)
    return data
  },

  async addChannel(
    brandId: number,
    payload: {
      network: import('@/types/smm').BrandNetwork | 'twitter' | 'wordpress'
      external_id?: string
      title?: string
      kind?: string
      role?: string
      color_override?: string
      /** Initial page URL when network === 'url' */
      url?: string
    },
  ): Promise<BrandChannel> {
    const { data } = await apiClient.post(`/smm/brands/${brandId}/channels`, payload)
    return data
  },

  async bindChannel(
    channelId: number,
    payload?: {
      external_id?: string
      title?: string
      from_profile?: boolean
    },
  ): Promise<BrandChannel> {
    const { data } = await apiClient.post(`/smm/channels/${channelId}/bind`, payload ?? {})
    return data
  },

  async channelStatus(channelId: number): Promise<{
    channel_id: number
    network: string
    connected: boolean
    auth_status?: string
    setup_url?: string
    last_publish_day?: string | null
    last_collect_day?: string | null
    sent_total?: number
    received_total?: number
    platform_connected?: boolean
  }> {
    const { data } = await apiClient.get(`/smm/channels/${channelId}/status`)
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

  async channelStats(brandId?: number | null, period = '7d'): Promise<ChannelStatsResponse> {
    const { data } = await apiClient.get('/smm/analytics/channel-stats', {
      params: { brand_id: brandId ?? undefined, period },
    })
    return {
      period: data.period ?? period,
      days: data.days,
      totals: data.totals ?? {
        collected: 0,
        processed: 0,
        sent: 0,
        failed: 0,
        alerts_sent: 0,
      },
      by_network: data.by_network ?? [],
      by_brand: data.by_brand ?? [],
      channels: data.channels ?? [],
    }
  },

  async runDueJobs(limit = 50): Promise<{ processed: number }> {
    const { data } = await apiClient.post('/smm/jobs/run-due', null, { params: { limit } })
    return data
  },

  async approveJob(id: number): Promise<PublishJob> {
    const { data } = await apiClient.post(`/smm/jobs/${id}/approve`)
    return data
  },

  async rejectJob(id: number, comment?: string): Promise<PublishJob> {
    const { data } = await apiClient.post(`/smm/jobs/${id}/reject`, { comment })
    return data
  },

  async assignJob(id: number, assigned_to: number | null): Promise<PublishJob> {
    const { data } = await apiClient.post(`/smm/jobs/${id}/assign`, { assigned_to })
    return data
  },

  async bulkApproveJobs(jobIds: number[]): Promise<{
    approved: number
    job_ids: number[]
    errors: { job_id: number; error: string }[]
  }> {
    const { data } = await apiClient.post('/smm/jobs/bulk-approve', { job_ids: jobIds })
    return data
  },

  async bulkRescheduleJobs(
    jobIds: number[],
    publish_at: string,
  ): Promise<{
    updated: number
    job_ids: number[]
    errors: { job_id: number; error: string }[]
  }> {
    const { data } = await apiClient.post('/smm/jobs/bulk-reschedule', {
      job_ids: jobIds,
      publish_at,
    })
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
    assigned_to?: number | null
  }): Promise<PublishJob> {
    const { data } = await apiClient.post('/smm/jobs', payload)
    return data
  },

  async listJobs(params?: {
    brand_id?: number
    from?: string
    to?: string
    status?: string
    statuses?: string
    channel_id?: number
    network?: string
    assigned_to?: number
    assigned_to_me?: boolean
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
      assigned_to?: number | null
      rejection_comment?: string | null
    },
  ): Promise<PublishJob> {
    const { data } = await apiClient.patch(`/smm/jobs/${id}`, payload)
    return data
  },

  async importCsv(file: File, brandId?: number | null): Promise<{
    created: number
    job_ids: number[]
    errors: { line: number; error: string }[]
    status?: string
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

  async runAutomation(
    id: number,
    limit = 10,
  ): Promise<{ created: number; job_ids: number[]; skipped: number; status: string }> {
    const { data } = await apiClient.post(`/smm/automations/${id}/run`, null, {
      params: { limit },
    })
    return data
  },

  async deleteAutomation(id: number): Promise<void> {
    await apiClient.delete(`/smm/automations/${id}`)
  },

  async analyticsOverview(
    brandId?: number | null,
    period = '7d',
    channelId?: number | null,
  ): Promise<AnalyticsOverview> {
    const { data } = await apiClient.get('/smm/analytics/overview', {
      params: {
        brand_id: brandId ?? undefined,
        period,
        channel_id: channelId ?? undefined,
      },
    })
    return data
  },

  async analyticsPosts(
    brandId?: number | null,
    sort = 'er',
    channelId?: number | null,
  ): Promise<AnalyticsPost[]> {
    const { data } = await apiClient.get('/smm/analytics/posts', {
      params: {
        brand_id: brandId ?? undefined,
        sort,
        channel_id: channelId ?? undefined,
      },
    })
    return data.posts ?? []
  },

  async analyticsMessages(
    brandId?: number | null,
    period = '7d',
    channelId?: number | null,
    limit = 50,
  ): Promise<{
    posts: AnalyticsPost[]
    events: {
      id: string
      direction: string
      network: string
      post_id?: number
      created_at?: string
      channel_title?: string
      text?: string
      status?: string
    }[]
  }> {
    const { data } = await apiClient.get('/smm/analytics/messages', {
      params: {
        brand_id: brandId ?? undefined,
        period,
        channel_id: channelId ?? undefined,
        limit,
      },
    })
    return data
  },

  async analyticsGrowth(brandId?: number | null): Promise<{
    points: { date: string; subscribers: number }[]
    subscriber_growth: number
  }> {
    const { data } = await apiClient.get('/smm/analytics/growth', {
      params: { brand_id: brandId ?? undefined },
    })
    return data
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
    network: 'tg' | 'vk' | 'url'
    external_id?: string
    title?: string
    kind?: string
    url?: string
    alert_enabled?: boolean
    sync_interval_min?: number
  }): Promise<BrandChannel> {
    const { data } = await apiClient.post('/smm/competitors', payload)
    return data
  },

  async listCompetitors(brandId?: number | null): Promise<BrandChannel[]> {
    const { data } = await apiClient.get('/smm/competitors', {
      params: { brand_id: brandId ?? undefined },
    })
    return data.competitors ?? []
  },

  async updateCompetitor(
    channelId: number,
    payload: {
      alert_enabled?: boolean
      alert_delivery?: BrandChannel['alert_delivery']
      sync_interval_min?: number
    },
  ): Promise<BrandChannel> {
    const { data } = await apiClient.patch(`/smm/competitors/${channelId}`, payload)
    return data
  },

  async competitorPosts(channelId: number): Promise<CompetitorPost[]> {
    const { data } = await apiClient.get(`/smm/competitors/${channelId}/posts`)
    return data.posts ?? []
  },

  async competitorDigest(
    channelId: number,
    period: '24h' | '7d' = '24h',
    withAi = true,
  ): Promise<CompetitorDigest> {
    const { data } = await apiClient.get(`/smm/competitors/${channelId}/digest`, {
      params: { period, with_ai: withAi },
    })
    return data
  },

  async competitorDiff(channelId: number, since?: string): Promise<CompetitorDiff> {
    const { data } = await apiClient.get(`/smm/competitors/${channelId}/diff`, {
      params: { since: since || undefined },
    })
    return data
  },

  async competitorCompare(
    brandId: number,
    competitorChannelId: number,
    period: string = '7d',
  ): Promise<CompetitorCompare> {
    const { data } = await apiClient.get('/smm/competitors/compare', {
      params: {
        brand_id: brandId,
        competitor_channel_id: competitorChannelId,
        period,
      },
    })
    return data
  },

  async aiSummarize(text: string, maxLen = 500): Promise<{ summary: string; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/summarize', { text, max_len: maxLen })
    return data
  },

  async aiRewrite(
    text: string,
    opts?: { tone?: string; network?: string; brand_id?: number | null },
  ): Promise<{ text: string; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/rewrite', { text, ...opts })
    return data
  },

  async aiAdapt(
    text: string,
    targets: string[] = ['tg', 'vk'],
    opts?: { brand_id?: number | null; tone?: string },
  ): Promise<{ variants: Record<string, string>; limits?: Record<string, number>; fallback?: boolean }> {
    const { data } = await apiClient.post('/smm/ai/adapt', {
      text,
      targets,
      brand_id: opts?.brand_id ?? undefined,
      tone: opts?.tone,
    })
    return data
  },

  async getAiUsage(): Promise<import('@/types/smm').AiUsage> {
    const { data } = await apiClient.get('/smm/ai/usage')
    return data
  },

  async getUsageSummary(): Promise<import('@/types/smm').UsageSummary> {
    const { data } = await apiClient.get('/smm/usage')
    return data
  },

  async getAiActions(): Promise<AiAssistAction[]> {
    const { data } = await apiClient.get('/smm/ai/actions')
    return data.actions ?? []
  },

  async aiProcess(payload: {
    action: AiAssistActionId
    text: string
    params?: AiProcessParams
    source?: 'inbox' | 'post'
    source_id?: number
    brand_id?: number | null
  }): Promise<AiProcessResponse> {
    const { data } = await apiClient.post('/smm/ai/process', payload)
    return data
  },

  async listTemplates(
    brandId: number,
    kind?: import('@/types/smm').TemplateKind,
  ): Promise<import('@/types/smm').ContentTemplate[]> {
    const { data } = await apiClient.get(`/smm/brands/${brandId}/templates`, {
      params: kind ? { kind } : undefined,
    })
    return data.templates ?? []
  },

  async createTemplate(
    brandId: number,
    payload: {
      kind: import('@/types/smm').TemplateKind
      title: string
      body?: string
      metadata?: Record<string, unknown>
    },
  ): Promise<import('@/types/smm').ContentTemplate> {
    const { data } = await apiClient.post(`/smm/brands/${brandId}/templates`, payload)
    return data
  },

  async updateTemplate(
    id: number,
    payload: Partial<{
      kind: import('@/types/smm').TemplateKind
      title: string
      body: string
      metadata: Record<string, unknown>
    }>,
  ): Promise<import('@/types/smm').ContentTemplate> {
    const { data } = await apiClient.patch(`/smm/templates/${id}`, payload)
    return data
  },

  async deleteTemplate(id: number): Promise<void> {
    await apiClient.delete(`/smm/templates/${id}`)
  },

  async applyTemplate(
    id: number,
    payload?: { job_id?: number; current_text?: string },
  ): Promise<import('@/types/smm').TemplateApplyResult> {
    const { data } = await apiClient.post(`/smm/templates/${id}/apply`, payload ?? {})
    return data
  },

  async listMediaPacks(brandId: number): Promise<import('@/types/smm').MediaPack[]> {
    const { data } = await apiClient.get(`/smm/brands/${brandId}/media-packs`)
    return data.media_packs ?? []
  },

  async createMediaPack(
    brandId: number,
    payload: { title: string; object_keys?: string[]; caption?: string },
  ): Promise<import('@/types/smm').MediaPack> {
    const { data } = await apiClient.post(`/smm/brands/${brandId}/media-packs`, payload)
    return data
  },

  async updateMediaPack(
    id: number,
    payload: Partial<{ title: string; object_keys: string[]; caption: string }>,
  ): Promise<import('@/types/smm').MediaPack> {
    const { data } = await apiClient.patch(`/smm/media-packs/${id}`, payload)
    return data
  },

  async deleteMediaPack(id: number): Promise<void> {
    await apiClient.delete(`/smm/media-packs/${id}`)
  },

  async applyMediaPack(
    id: number,
    payload?: { job_id?: number; merge?: boolean },
  ): Promise<import('@/types/smm').MediaPackApplyResult> {
    const { data } = await apiClient.post(`/smm/media-packs/${id}/apply`, payload ?? {})
    return data
  },

  async buildUtmUrl(
    baseUrl: string,
    params?: Record<string, string>,
  ): Promise<{ url: string }> {
    const { data } = await apiClient.post('/smm/library/utm/build', {
      base_url: baseUrl,
      params,
    })
    return data
  },

  async republishVariant(
    jobId: number,
    payload?: { pending_approval?: boolean; network?: string },
  ): Promise<{
    source_job_id: number
    job: PublishJob
    ai_used: boolean
    tone?: string | null
  }> {
    const { data } = await apiClient.post(`/smm/jobs/${jobId}/republish-variant`, payload ?? {})
    return data
  },

  async platformStatus(): Promise<import('@/types/smm').PlatformStatusResponse> {
    const { data } = await apiClient.get('/smm/platform-status')
    return data
  },

  async recheckChannelAuth(channelId: number): Promise<BrandChannel> {
    const { data } = await apiClient.post(`/smm/channels/${channelId}/auth/recheck`)
    return data
  },

  async onboardingState(): Promise<import('@/types/smm').OnboardingState> {
    const { data } = await apiClient.get('/smm/onboarding/state')
    return data
  },

  async skipOnboarding(): Promise<import('@/types/smm').OnboardingState> {
    const { data } = await apiClient.post('/smm/onboarding/skip')
    return data
  },

  async seedDemoWorkspace(force = false): Promise<{
    seed: { seeded: boolean; already?: boolean; brand_id?: number; reason?: string }
    state: import('@/types/smm').OnboardingState
  }> {
    const { data } = await apiClient.post('/smm/onboarding/seed-demo', null, {
      params: { force },
    })
    return data
  },
}
