import axios, { AxiosError } from 'axios'
import { normalizeErrorDetail, type ApiError } from '@/services/api-client'

export type QuotaErrorDetail = {
  message: string
  resource?: string
  limit?: number
  used?: number
  upgrade_url?: string
}

const RESOURCE_LABELS: Record<string, string> = {
  monthly_posts: 'Posts / month',
  ai_calls_month: 'AI calls / month',
  max_own_channels: 'Own channels',
  max_competitor_channels: 'Competitor channels',
  max_brands: 'Brands',
  max_automations: 'Automations',
  max_templates: 'Templates',
  max_media_packs: 'Media packs',
  max_content_series: 'Content series / рубрики',
  max_team_seats: 'Team seats',
  schedule_horizon_days: 'Schedule horizon',
  storage_gb: 'Storage',
  'feature:competitors': 'Competitors',
  'feature:ai_composer': 'AI composer',
  'feature:automations': 'Automations',
  'feature:approval_workflow': 'Approval workflow',
  'feature:best_times': 'Best times',
  'feature:inbox_reply': 'Inbox reply',
  'feature:tg_listening': 'Telegram Listening',
  'feature:channel_stats': 'Channel stats',
  'feature:schedule': 'Scheduling',
}

export function quotaResourceLabel(key: string): string {
  if (RESOURCE_LABELS[key]) return RESOURCE_LABELS[key]
  if (key.startsWith('feature:')) {
    return key.slice('feature:'.length).replace(/_/g, ' ')
  }
  return key.replace(/_/g, ' ')
}

export function parseQuotaError(error: unknown): QuotaErrorDetail | null {
  if (!axios.isAxiosError(error)) return null
  const ax = error as AxiosError<ApiError>
  if (ax.response?.status !== 402) return null
  const detail = ax.response.data?.detail
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const d = detail as Record<string, unknown>
    const message =
      typeof d.message === 'string' && d.message.trim()
        ? d.message
        : normalizeErrorDetail(detail) || 'Plan limit exceeded'
    return {
      message,
      resource: typeof d.resource === 'string' ? d.resource : undefined,
      limit: typeof d.limit === 'number' ? d.limit : undefined,
      used: typeof d.used === 'number' ? d.used : undefined,
      upgrade_url: typeof d.upgrade_url === 'string' ? d.upgrade_url : '/pricing',
    }
  }
  const message = normalizeErrorDetail(detail) || 'Plan limit exceeded'
  return { message, upgrade_url: '/pricing' }
}

export function isQuotaError(error: unknown): boolean {
  return parseQuotaError(error) != null
}
