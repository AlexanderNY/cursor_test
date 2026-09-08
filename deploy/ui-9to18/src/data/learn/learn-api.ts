/** Learn API client for 9to18 → gateway /learn/* */

import type { LearnPost, LearnPostInput } from '@/data/learn/learn-store'
import { getLearnAccessToken } from '@/data/learn/learn-auth'
import { getSiteAccessToken } from '@/data/site/site-auth'
import { normalizeStructuredPost, hydrateLearnStructured } from '@/data/site/structured-post'

const API_BASE = '/api'

export class LearnApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function resolveAuthToken(): string | null {
  return getLearnAccessToken() || getSiteAccessToken()
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  opts?: { auth?: boolean },
): Promise<T> {
  const headers = new Headers(init.headers || {})
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (opts?.auth !== false) {
    const token = resolveAuthToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const data = (await response.json()) as { detail?: unknown }
      if (typeof data.detail === 'string') {
        detail = data.detail
      } else if (data.detail != null) {
        detail = JSON.stringify(data.detail)
      }
    } catch {
      /* ignore */
    }
    throw new LearnApiError(detail || `HTTP ${response.status}`, response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

function normalizePost(raw: Record<string, unknown>): LearnPost {
  const theoryFormat =
    raw.theoryFormat === 'html' || raw.theory_format === 'html' ? 'html' : 'markdown'
  const labFormat = raw.labFormat === 'html' || raw.lab_format === 'html' ? 'html' : 'markdown'
  const cheatsheetFormat =
    raw.cheatsheetFormat === 'html' || raw.cheatsheet_format === 'html' ? 'html' : 'markdown'
  const lab = String(raw.lab || '')
  const cheatsheet = String(raw.cheatsheet || '')
  const diagram = String(raw.diagram || '')
  const structured = hydrateLearnStructured(normalizeStructuredPost(raw.structured), {
    lab,
    cheatsheet,
    cheatsheetFormat,
    diagram,
  })
  return {
    slug: String(raw.slug || ''),
    episode: String(raw.episode || ''),
    title: String(raw.title || ''),
    shortTitle: String(raw.shortTitle || raw.short_title || ''),
    rubricId: (raw.rubricId || raw.rubric_id || 'architecture') as LearnPost['rubricId'],
    order: Number(raw.order ?? raw.sort_order ?? 0),
    theory: String(raw.theory || ''),
    lab,
    cheatsheet,
    diagram,
    links: Array.isArray(raw.links)
      ? (raw.links as Array<{ label?: string; href?: string }>).map((link) => ({
          label: String(link.label || ''),
          href: String(link.href || '#'),
        }))
      : [],
    structured,
    theoryFormat,
    labFormat,
    cheatsheetFormat,
    publishedAt: String(raw.publishedAt || raw.published_at || new Date().toISOString()),
    updatedAt: String(raw.updatedAt || raw.updated_at || new Date().toISOString()),
  }
}

export async function apiListPublishedPosts(): Promise<LearnPost[]> {
  const data = await request<{ posts: Record<string, unknown>[] }>('/learn/posts', {}, { auth: false })
  return (data.posts || []).map(normalizePost)
}

export async function apiGetPublishedPost(
  slug: string,
  opts?: { preview?: boolean },
): Promise<LearnPost | undefined> {
  const preview = Boolean(opts?.preview)
  const qs = preview ? '?preview=1' : ''
  try {
    const data = await request<Record<string, unknown>>(
      `/learn/posts/${encodeURIComponent(slug)}${qs}`,
      {},
      // Preview needs JWT so gateway can set X-User-Role for unpublished posts.
      { auth: preview },
    )
    return normalizePost(data)
  } catch (error) {
    if (error instanceof LearnApiError && error.status === 404) {
      return undefined
    }
    throw error
  }
}

export async function apiListAdminPosts(): Promise<LearnPost[]> {
  const data = await request<{ posts: Record<string, unknown>[] }>('/learn/admin/posts')
  return (data.posts || []).map(normalizePost)
}

export async function apiSavePost(input: LearnPostInput): Promise<LearnPost> {
  const data = await request<Record<string, unknown>>('/learn/admin/posts', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  return normalizePost(data)
}

export async function apiDeletePost(slug: string): Promise<void> {
  await request(`/learn/admin/posts/${encodeURIComponent(slug)}`, { method: 'DELETE' })
}

export async function apiResetToSeed(): Promise<LearnPost[]> {
  const data = await request<{ posts: Record<string, unknown>[] }>('/learn/admin/reset-to-seed', {
    method: 'POST',
  })
  return (data.posts || []).map(normalizePost)
}

export async function apiScheduleAll(
  startIso: string,
  intervalDays: number,
): Promise<LearnPost[]> {
  const data = await request<{ posts: Record<string, unknown>[] }>('/learn/admin/schedule', {
    method: 'POST',
    body: JSON.stringify({ startIso, intervalDays }),
  })
  return (data.posts || []).map(normalizePost)
}

export async function apiLogin(
  username: string,
  password: string,
): Promise<{ access_token: string; refresh_token: string }> {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }, { auth: false })
}

export async function apiGetProfile(): Promise<{ role?: string; username?: string }> {
  return request('/auth/profile')
}

export async function apiSubmitContact(input: {
  name: string
  email: string
  message: string
}): Promise<{ ok: boolean; id: number }> {
  return request('/learn/contact', {
    method: 'POST',
    body: JSON.stringify(input),
  }, { auth: false })
}

export async function apiGetPromo(): Promise<Record<string, unknown>> {
  return request('/learn/promo', {}, { auth: false })
}

export async function apiSavePromo(
  input: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return request('/learn/admin/promo', {
    method: 'PUT',
    body: JSON.stringify(input),
  })
}
