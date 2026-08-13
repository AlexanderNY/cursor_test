import type {
  TelegramAlertRule,
  TelegramChatRef,
  TelegramChatRefInput,
  ConditionsMode,
  SentimentFilter,
} from '@/types/telegram'
import { formatDateOnly } from '@/utils/date'

export const AUTH_STATUS_POLL_INTERVAL_MS = 12_000
export const MAX_ALERT_RULES = 10
export const MAX_ALERT_LIST_ITEMS = 10

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

export const SCHEDULE_MINUTES = [0, 15, 30, 45] as const
export type ScheduleMinute = (typeof SCHEDULE_MINUTES)[number]

export interface DynamicField {
  id: string
  value: string
  label?: string
}

export interface AlertRuleBlock {
  id: string
  enabled: boolean
  priority: number
  conditionsMode: ConditionsMode
  categoryFilter: string
  chatsToRead: DynamicField[]
  saveConditions: DynamicField[]
  channelToPost: string
  channelToPostTitle: string
  alertText: string
  dedupWindowSec: number
  rateLimitPerHour: string
  minTextLength: number
  includeAiSummary: boolean
  sentimentFilter: SentimentFilter | ''
  stopOnMatch: boolean
}

export function parseChatRef(input: TelegramChatRefInput | null | undefined): TelegramChatRef | null {
  if (input == null) return null
  if (typeof input === 'string') {
    const id = input.trim()
    return id ? { id } : null
  }
  const id = String(input.id || '').trim()
  if (!id) return null
  const title = (input.title || '').trim()
  return title ? { id, title } : { id }
}

export function chatRefsFromInputs(items?: TelegramChatRefInput[] | null): TelegramChatRef[] {
  if (!items?.length) return []
  const result: TelegramChatRef[] = []
  for (const item of items) {
    const ref = parseChatRef(item)
    if (ref) result.push(ref)
  }
  return result
}

export function dynamicFieldsFromChatRefs(items?: TelegramChatRefInput[] | null): DynamicField[] {
  const refs = chatRefsFromInputs(items)
  if (!refs.length) return [{ id: generateId(), value: '', label: '' }]
  return refs.map((ref) => ({
    id: generateId(),
    value: ref.id,
    label: ref.title || '',
  }))
}

export function chatRefsFromDynamicFields(fields: DynamicField[]): TelegramChatRef[] {
  return fields
    .map((field) => {
      const id = field.value.trim()
      if (!id) return null
      const title = (field.label || '').trim()
      return title ? { id, title } : { id }
    })
    .filter((item): item is TelegramChatRef => item != null)
}

export function createEmptyAlertRuleBlock(): AlertRuleBlock {
  return {
    id: generateId(),
    enabled: true,
    priority: 0,
    conditionsMode: 'any_of',
    categoryFilter: '',
    chatsToRead: [{ id: generateId(), value: '', label: '' }],
    saveConditions: [{ id: generateId(), value: '' }],
    channelToPost: '',
    channelToPostTitle: '',
    alertText: '',
    dedupWindowSec: 3600,
    rateLimitPerHour: '',
    minTextLength: 0,
    includeAiSummary: false,
    sentimentFilter: '',
    stopOnMatch: false,
  }
}

export function mapAlertRulesFromProfile(rules?: TelegramAlertRule[]): AlertRuleBlock[] {
  if (rules && rules.length > 0) {
    return rules.map((rule) => ({
      id: rule.id || generateId(),
      enabled: rule.enabled ?? true,
      priority: rule.priority ?? 0,
      conditionsMode: rule.conditions_mode || 'any_of',
      categoryFilter: rule.category_filter || '',
      chatsToRead: dynamicFieldsFromChatRefs(rule.chats_to_read),
      saveConditions: (rule.save_conditions?.length ? rule.save_conditions : ['']).map((value) => ({
        id: generateId(),
        value,
      })),
      channelToPost: rule.channel_to_post || '',
      channelToPostTitle: rule.channel_to_post_title || '',
      alertText: rule.alert_text || '',
      dedupWindowSec: rule.dedup_window_sec ?? 3600,
      rateLimitPerHour: rule.rate_limit_per_hour != null ? String(rule.rate_limit_per_hour) : '',
      minTextLength: rule.min_text_length ?? 0,
      includeAiSummary: rule.include_ai_summary ?? false,
      sentimentFilter: rule.sentiment_filter || '',
      stopOnMatch: rule.stop_on_match ?? false,
    }))
  }
  return [createEmptyAlertRuleBlock()]
}

export function serializeAlertRules(rules: AlertRuleBlock[]): TelegramAlertRule[] {
  return rules
    .map((block) => ({
      id: block.id,
      enabled: block.enabled,
      priority: block.priority,
      conditions_mode: block.conditionsMode,
      category_filter: block.categoryFilter.trim() || undefined,
      chats_to_read: chatRefsFromDynamicFields(block.chatsToRead),
      save_conditions: block.saveConditions.map((field) => field.value.trim()).filter(Boolean),
      channel_to_post: block.channelToPost.trim() || undefined,
      channel_to_post_title: block.channelToPostTitle.trim() || undefined,
      alert_text: block.alertText.trim().slice(0, 1000) || undefined,
      dedup_window_sec: block.dedupWindowSec,
      rate_limit_per_hour: block.rateLimitPerHour.trim() ? Number(block.rateLimitPerHour) : undefined,
      min_text_length: block.minTextLength,
      include_ai_summary: block.includeAiSummary,
      sentiment_filter: block.sentimentFilter || undefined,
      stop_on_match: block.stopOnMatch,
    }))
    .filter(
      (rule) =>
        rule.chats_to_read.length > 0 &&
        rule.save_conditions.length > 0 &&
        rule.channel_to_post &&
        rule.alert_text,
    )
    .slice(0, MAX_ALERT_RULES)
}


export function validateAlertRules(alertEnabled: boolean, rules: AlertRuleBlock[]): string | null {
  for (const block of rules) {
    if (!block.enabled) continue
    const hasAnyField =
      block.chatsToRead.some((field) => field.value.trim()) ||
      block.saveConditions.some((field) => field.value.trim()) ||
      block.channelToPost.trim() ||
      block.alertText.trim()
    const hasAllFields =
      block.chatsToRead.some((field) => field.value.trim()) &&
      block.saveConditions.some((field) => field.value.trim()) &&
      block.channelToPost.trim() &&
      block.alertText.trim()
    if (hasAnyField && !hasAllFields) {
      return 'Заполните все поля для включённых правил Alerting или отключите правило.'
    }
  }
  if (alertEnabled && serializeAlertRules(rules).length === 0) {
    return 'Добавьте хотя бы одно полное правило Alerting или отключите alerting.'
  }
  return null
}

export function toDatetimeLocalValue(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function fromDatetimeLocalValue(value: string): string | null {
  if (!value.trim()) return null
  return new Date(value).toISOString()
}

export function getWeekStart(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  return d
}

export function getWeekRange(weekStart: Date): { dateFrom: string; dateTo: string } {
  const from = new Date(weekStart)
  from.setHours(0, 0, 0, 0)
  const to = new Date(weekStart)
  to.setDate(to.getDate() + 6)
  to.setHours(23, 59, 59, 999)
  return { dateFrom: from.toISOString(), dateTo: to.toISOString() }
}

export function formatWeekLabel(weekStart: Date): string {
  const end = new Date(weekStart)
  end.setDate(end.getDate() + 6)
  return `${formatDateOnly(weekStart)} – ${formatDateOnly(end)}`
}

export interface AvailableChannel {
  id: number
  title: string
}

export function channelIdToString(id: number): string {
  return String(id)
}
