import { getSiteAccessToken } from '@/data/site/site-auth'

const API_BASE = '/api'

export class SiteApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export type SiteApp = {
  slug: string
  title: string
  subtitle: string
  description: string
  accent: string
  emoji: string
  externalHref: string
  appPath: string
  isVisible: boolean
  sortOrder: number
}

export type SitePost = {
  id: number
  appSlug: string
  slug: string
  title: string
  body: string
  isPublished: boolean
  publishedAt: string
}

export type SiteUser = {
  id: number
  email: string
  username: string
  siteRole: 'user' | 'site_admin'
  appAdmin: string[]
}

export type SiteAppWrite = {
  title?: string
  subtitle?: string
  description?: string
  accent?: string
  emoji?: string
  external_href?: string
  app_path?: string
  is_visible?: boolean
  sort_order?: number
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
    const token = getSiteAccessToken()
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
    throw new SiteApiError(detail || `HTTP ${response.status}`, response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export async function siteRegister(input: {
  email: string
  username: string
  password: string
}): Promise<{ access_token: string; user: SiteUser }> {
  return request(
    '/site/auth/register',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
    { auth: false },
  )
}

export async function siteLogin(input: {
  login: string
  password: string
}): Promise<{ access_token: string; user: SiteUser }> {
  return request(
    '/site/auth/login',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
    { auth: false },
  )
}

export async function siteGetMe(): Promise<SiteUser> {
  return request('/site/me')
}

export async function siteListApps(): Promise<SiteApp[]> {
  const data = await request<{ apps: SiteApp[] }>('/site/apps', {}, { auth: false })
  return data.apps || []
}

/** Все плашки включая скрытые (супер-админ). */
export async function siteAdminListApps(): Promise<SiteApp[]> {
  const data = await request<{ apps: SiteApp[] }>('/site/admin/apps')
  return data.apps || []
}

export async function siteReorderApps(slugs: string[]): Promise<SiteApp[]> {
  const data = await request<{ apps: SiteApp[] }>('/site/admin/apps/reorder', {
    method: 'PUT',
    body: JSON.stringify({ slugs }),
  })
  return data.apps || []
}

export async function siteCreateApp(body: {
  slug: string
  title: string
  subtitle?: string
  description?: string
  accent?: string
  emoji?: string
  external_href?: string
  app_path?: string
  is_visible?: boolean
}): Promise<SiteApp> {
  return request('/site/apps', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function siteDeleteApp(slug: string): Promise<void> {
  await request(`/site/apps/${encodeURIComponent(slug)}`, { method: 'DELETE' })
}

export async function siteGetApp(slug: string): Promise<SiteApp> {
  return request(`/site/apps/${encodeURIComponent(slug)}`)
}

export async function sitePatchApp(slug: string, body: SiteAppWrite): Promise<SiteApp> {
  return request(`/site/apps/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function siteListPosts(slug: string): Promise<SitePost[]> {
  const data = await request<{ posts: SitePost[] }>(
    `/site/apps/${encodeURIComponent(slug)}/posts`,
  )
  return data.posts || []
}

export async function siteGetPost(appSlug: string, postSlug: string): Promise<SitePost> {
  return request(
    `/site/apps/${encodeURIComponent(appSlug)}/posts/${encodeURIComponent(postSlug)}`,
    {},
    { auth: false },
  )
}

export async function siteSavePost(
  appSlug: string,
  postSlug: string,
  body: { slug: string; title: string; body: string; is_published: boolean },
): Promise<SitePost> {
  return request(
    `/site/apps/${encodeURIComponent(appSlug)}/posts/${encodeURIComponent(postSlug)}`,
    {
      method: 'PUT',
      body: JSON.stringify(body),
    },
  )
}

export async function siteDeletePost(appSlug: string, postSlug: string): Promise<void> {
  await request(
    `/site/apps/${encodeURIComponent(appSlug)}/posts/${encodeURIComponent(postSlug)}`,
    { method: 'DELETE' },
  )
}

export async function siteSubmitContact(input: {
  name: string
  email: string
  message: string
  app_slug?: string
}): Promise<{ ok: boolean }> {
  return request(
    '/site/contact',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
    { auth: false },
  )
}

export async function siteGetPromo(): Promise<Record<string, unknown>> {
  return request('/site/promo', {}, { auth: false })
}

export async function siteSavePromo(
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return request('/site/promo', {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export type SiteLearningMap = {
  source: 'default' | 'custom'
  markdown: string
  updatedAt: string | null
  updatedBy: string | null
  chars: number
}

function normalizeLearningMap(raw: Record<string, unknown>): SiteLearningMap {
  const source = raw.source === 'custom' ? 'custom' : 'default'
  return {
    source,
    markdown: String(raw.markdown || ''),
    updatedAt: raw.updated_at != null ? String(raw.updated_at) : null,
    updatedBy: raw.updated_by != null ? String(raw.updated_by) : null,
    chars: Number(raw.chars) || String(raw.markdown || '').length,
  }
}

export async function siteGetLearningMap(): Promise<SiteLearningMap> {
  const raw = await request<Record<string, unknown>>('/site/learning-map', {}, { auth: false })
  return normalizeLearningMap(raw)
}

export async function siteSaveLearningMap(markdown: string): Promise<SiteLearningMap> {
  const raw = await request<Record<string, unknown>>('/site/learning-map', {
    method: 'PUT',
    body: JSON.stringify({ markdown }),
  })
  return normalizeLearningMap(raw)
}

export async function siteResetLearningMap(): Promise<SiteLearningMap> {
  const raw = await request<Record<string, unknown>>('/site/learning-map', {
    method: 'DELETE',
  })
  return normalizeLearningMap(raw)
}

export async function siteAssignAdmin(input: {
  username: string
  app_slug: string
}): Promise<{ ok: boolean }> {
  return request('/site/admin/assign', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function siteUnassignAdmin(input: {
  username: string
  app_slug: string
}): Promise<{ ok: boolean }> {
  return request('/site/admin/unassign', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export type SiteContact = {
  id: number
  appSlug: string
  name: string
  email: string
  message: string
  status: 'new' | 'read' | 'done'
  createdAt: string
}

export async function siteListContacts(status?: string): Promise<SiteContact[]> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : ''
  const data = await request<{ contacts: SiteContact[] }>(`/site/admin/contacts${qs}`)
  return data.contacts || []
}

export async function sitePatchContact(
  id: number,
  status: 'new' | 'read' | 'done',
): Promise<SiteContact> {
  return request(`/site/admin/contacts/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export type SiteAdminUser = {
  id: number
  email: string
  username: string
  siteRole: 'user' | 'site_admin'
  isActive: boolean
  appAdmin: string[]
  createdAt?: string
}

export async function siteListUsers(): Promise<SiteAdminUser[]> {
  const data = await request<{ users: SiteAdminUser[] }>('/site/admin/users')
  return data.users || []
}

export async function sitePatchUser(
  userId: number,
  body: { site_role?: 'user' | 'site_admin'; is_active?: boolean; password?: string },
): Promise<SiteAdminUser> {
  return request(`/site/admin/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function siteChangePassword(input: {
  current_password: string
  new_password: string
}): Promise<{ ok: boolean }> {
  return request('/site/me/password', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function siteForgotPassword(login: string): Promise<{
  ok: boolean
  detail?: string
  resetToken?: string
}> {
  return request(
    '/site/auth/forgot-password',
    {
      method: 'POST',
      body: JSON.stringify({ login }),
    },
    { auth: false },
  )
}

export async function siteResetPassword(input: {
  token: string
  new_password: string
}): Promise<{ ok: boolean }> {
  return request(
    '/site/auth/reset-password',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
    { auth: false },
  )
}

export type SiteLearnProgressItem = {
  slug: string
  completedAt: string
}

export async function siteGetLearnProgress(): Promise<SiteLearnProgressItem[]> {
  const data = await request<{ items: SiteLearnProgressItem[] }>('/site/learn/progress')
  return data.items || []
}

export async function siteSetLearnProgress(
  slug: string,
  completed: boolean,
): Promise<{ slug: string; completed: boolean; completedAt: string | null }> {
  return request('/site/learn/progress', {
    method: 'PUT',
    body: JSON.stringify({ slug, completed }),
  })
}

export type SiteLatestPost = {
  appSlug: string
  postSlug: string
  title: string
  excerpt: string
  publishedAt: string
  appTitle: string
  emoji: string
  accent: string
  href: string
}

export async function siteListLatestPosts(limit = 5): Promise<SiteLatestPost[]> {
  const data = await request<{ items: SiteLatestPost[] }>(
    `/site/posts/latest?limit=${encodeURIComponent(String(limit))}`,
    {},
    { auth: false },
  )
  return data.items || []
}

export type SiteStudySummary = {
  quiz: {
    attempts: number
    scoreSum: number
    totalSum: number
    avgPercent: number
    lastAt: string | null
    recent: Array<{
      sourceKey: string
      score: number
      total: number
      finishedAt: string
    }>
  }
  anki: {
    cards: number
    due: number
    learning: number
  }
}

export async function siteGetStudySummary(): Promise<SiteStudySummary> {
  return request('/site/study/summary')
}

export async function siteSubmitQuizAttempt(input: {
  source_type: 'post' | 'learn' | 'quiz_page'
  source_key: string
  score: number
  total: number
  answers?: unknown[]
}): Promise<{ id: number; score: number; total: number; finishedAt: string }> {
  return request('/site/study/quiz', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export type SiteAnkiCardState = {
  cardId: string
  front: string
  back: string
  sourceKey: string
  ease: number
  intervalDays: number
  repetitions: number
  dueAt: string
  updatedAt: string
}

export async function siteListAnkiCards(): Promise<SiteAnkiCardState[]> {
  const data = await request<{ cards: SiteAnkiCardState[] }>('/site/study/anki')
  return data.cards || []
}

export async function siteReviewAnkiCard(input: {
  card_id: string
  front?: string
  back?: string
  source_key?: string
  ease: 1 | 2 | 3 | 4
}): Promise<{ cardId: string; dueAt: string; intervalDays: number; repetitions: number }> {
  return request('/site/study/anki', {
    method: 'PUT',
    body: JSON.stringify(input),
  })
}
