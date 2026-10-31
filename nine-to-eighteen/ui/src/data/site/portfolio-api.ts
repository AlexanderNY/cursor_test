/** Клиент portfolio-api (/api/portfolio → :8022). */
import {
  clearSiteAuthSessionOnAuthFailure,
  getSiteAccessToken,
} from '@/data/site/site-auth'
import { SiteApiError } from '@/data/site/site-api'

const API_BASE = '/api'

export type PortfolioProfile = {
  handle: string
  headline: string
  summary: string
  isPublished: boolean
  pinnedResumeId: string | null
  publicPath: string
  updatedAt: string | null
  contactPhone: string
  contactEmail: string
  contactUrl: string
}

export type PortfolioLearnRef = {
  slug: string
  title: string
  episode: string
}

export type PortfolioCase = {
  id: string
  sortOrder: number
  title: string
  role: string
  problem: string
  work: string
  outcome: string
  stack: string[]
  repoUrl: string
  demoUrl: string
  learnSlugs: string[]
  learn: PortfolioLearnRef[]
  certTrackId: string
  certTrackTitle: string
  updatedAt: string | null
  blurb: string
  hasCover: boolean
}

export type PortfolioCaseInput = {
  title: string
  role: string
  problem: string
  work: string
  outcome: string
  stack: string[]
  repo_url: string
  demo_url: string
  learn_slugs: string[]
  cert_track_id: string
  blurb: string
}

export type PortfolioGithubProject = {
  name: string
  url: string
  description: string
  language: string
  selected: boolean
}

export type PortfolioResumeOption = {
  id: string
  versionName: string
  title: string
  specialization: string
}

export type PortfolioCertTrack = {
  id: string
  title: string
  earned: boolean
  done: number
  total: number
}

export type PortfolioSources = {
  displayName: string
  githubProjects: PortfolioGithubProject[]
  learn: PortfolioLearnRef[]
  resumes: PortfolioResumeOption[]
  certTracks: PortfolioCertTrack[]
}

export type PublicPortfolioCase = {
  id: string
  title: string
  role: string
  problem: string
  work: string
  outcome: string
  stack: string[]
  repoUrl: string
  demoUrl: string
  learn: PortfolioLearnRef[]
  certTrackTitle: string
  certCode: string
  blurb: string
  hasCover: boolean
}

export type PortfolioContacts = {
  phone: string
  email: string
  url: string
}

export type PublicPortfolio = {
  handle: string
  displayName: string
  headline: string
  summary: string
  city: string
  contacts: PortfolioContacts
  pinnedResume: {
    versionName: string
    title: string
    specialization: string
    about: string
  } | null
  cases: PublicPortfolioCase[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getSiteAccessToken()
  const headers = new Headers(init?.headers)
  if (!headers.has('Content-Type') && init?.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const data = (await response.json()) as { detail?: unknown }
      if (typeof data.detail === 'string') {
        detail = data.detail
      }
    } catch {
      /* ignore */
    }
    clearSiteAuthSessionOnAuthFailure(response.status, detail)
    throw new SiteApiError(detail || `HTTP ${response.status}`, response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export async function portfolioGetMine(): Promise<{
  portfolio: PortfolioProfile | null
  cases: PortfolioCase[]
}> {
  return request('/portfolio/me')
}

export async function portfolioSaveMine(body: {
  handle: string
  headline: string
  summary: string
  is_published: boolean
  pinned_resume_id: string | null
  contact_phone: string
  contact_email: string
  contact_url: string
}): Promise<{ portfolio: PortfolioProfile | null }> {
  return request('/portfolio/me', {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export async function portfolioSources(): Promise<PortfolioSources> {
  return request('/portfolio/sources')
}

export async function portfolioCreateCase(body: PortfolioCaseInput): Promise<PortfolioCase> {
  return request('/portfolio/cases', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function portfolioUpdateCase(
  caseId: string,
  body: PortfolioCaseInput,
): Promise<PortfolioCase> {
  return request(`/portfolio/cases/${encodeURIComponent(caseId)}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export async function portfolioDeleteCase(caseId: string): Promise<void> {
  await request(`/portfolio/cases/${encodeURIComponent(caseId)}`, { method: 'DELETE' })
}

export async function portfolioReorder(ids: string[]): Promise<void> {
  await request('/portfolio/cases/reorder', {
    method: 'POST',
    body: JSON.stringify({ ids }),
  })
}

export async function portfolioGetPublic(handle: string): Promise<PublicPortfolio> {
  return request(`/portfolio/p/${encodeURIComponent(handle)}`)
}

export function portfolioPublicCoverUrl(handle: string, caseId: string): string {
  return `${API_BASE}/portfolio/p/${encodeURIComponent(handle)}/covers/${encodeURIComponent(caseId)}`
}

async function readError(response: Response): Promise<string> {
  let detail = response.statusText
  try {
    const data = (await response.json()) as { detail?: unknown }
    if (typeof data.detail === 'string') {
      detail = data.detail
    }
  } catch {
    /* ignore */
  }
  clearSiteAuthSessionOnAuthFailure(response.status, detail)
  return detail || `HTTP ${response.status}`
}

export async function portfolioUploadCover(caseId: string, file: File): Promise<void> {
  const token = getSiteAccessToken()
  const form = new FormData()
  form.append('cover', file)
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(
    `${API_BASE}/portfolio/cases/${encodeURIComponent(caseId)}/cover`,
    { method: 'POST', headers, body: form },
  )
  if (!response.ok) {
    throw new SiteApiError(await readError(response), response.status)
  }
}

export async function portfolioDeleteCover(caseId: string): Promise<void> {
  await request(`/portfolio/cases/${encodeURIComponent(caseId)}/cover`, { method: 'DELETE' })
}

export async function portfolioFetchCover(caseId: string): Promise<string | null> {
  const token = getSiteAccessToken()
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(
    `${API_BASE}/portfolio/cases/${encodeURIComponent(caseId)}/cover`,
    { headers },
  )
  if (response.status === 404) {
    return null
  }
  if (!response.ok) {
    throw new SiteApiError(await readError(response), response.status)
  }
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}
