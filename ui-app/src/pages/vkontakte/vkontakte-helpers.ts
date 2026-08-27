import { formatDateOnly } from '@/utils/date'

export const VK_MAX_LENGTH = 15985
export const AUTH_STATUS_POLL_INTERVAL_MS = 15_000

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

export interface DynamicField {
  id: string
  value: string
}

export function htmlToPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return (div.textContent ?? div.innerText ?? '').trim()
}

export function imagePreviewUrl(url: string, apiBaseUrl: string, origin: string): string {
  if (url.startsWith('http')) return url
  return `${origin}${apiBaseUrl}${url.startsWith('/') ? '' : '/'}${url}`
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
