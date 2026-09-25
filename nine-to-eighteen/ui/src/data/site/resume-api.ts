/** Клиент resume-api (/api/resume → :8021). */
import { getSiteAccessToken } from '@/data/site/site-auth'
import { SiteApiError } from '@/data/site/site-api'
import type { SiteUserProfile } from '@/data/site/site-api'

const API_BASE = '/api'

export type SiteResumeSkill = {
  key: string
  name: string
  level: string
  evidence: string
  sourceSlugs: string[]
  mapBranch?: string | null
  display: string
}

export type SiteResume = {
  id: string
  userId?: number
  versionName: string
  title: string
  specialization: string
  salaryAmount: number | null
  salaryCurrency: string
  employmentTypes: string[]
  workFormats: string[]
  about: string
  selectedSkillKeys: string[]
  generatedSkills: SiteResumeSkill[]
  questionnaireAnswers?: Record<string, unknown>
  createdAt?: string | null
  updatedAt: string | null
}

export type SiteResumeSummary = {
  id: string
  versionName: string
  title: string
  specialization: string
  updatedAt: string | null
}

export type SiteResumePreview = {
  profile: SiteUserProfile
  resume: SiteResume
  skills: SiteResumeSkill[]
  branchHints: string[]
  suggestedSpecialization: string | null
  completedCount: number
  completedSlugs?: string[]
  username: string
  strength?: ResumeStrength
}

export type ResumeStrengthAction = {
  id: string
  points: number
  title: string
  href?: string | null
  slug?: string
}

export type ResumeStrength = {
  score: number
  maxScore: number
  parts: Array<{
    id: string
    label: string
    points: number
    maxPoints: number
    done: boolean
    doneCount?: number
    totalRelevant?: number
    branch?: string | null
  }>
  actions: ResumeStrengthAction[]
  relevantBranch?: string | null
  doneRelevantSlugs?: string[]
  missingRelevantSlugs?: string[]
}

export type ResumeQuestionOption = { id: string; label: string }

export type ResumeQuestion = {
  id: string
  type: 'single' | 'multi' | 'text'
  required: boolean
  title: string
  hint?: string
  options?: ResumeQuestionOption[]
  maxLength?: number
  placeholder?: string
}

export type ResumeQuestionnaire = {
  version: number
  title: string
  lead: string
  questions: ResumeQuestion[]
}

export type ResumeExportResult = {
  format: 'pdf' | 'docx'
  fileName: string
  downloadUrl: string
  expiresAt?: string
  fileId?: string
  bytes?: number
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
    throw new SiteApiError(detail || `HTTP ${response.status}`, response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export async function resumeList(): Promise<SiteResumeSummary[]> {
  const data = await request<{ items: SiteResumeSummary[] }>('/resume')
  return data.items || []
}

export async function resumeCreate(input?: {
  version_name?: string
  copy_from?: string
}): Promise<SiteResume> {
  return request('/resume', {
    method: 'POST',
    body: JSON.stringify(input || {}),
  })
}

export async function resumeGet(resumeId: string): Promise<SiteResume> {
  return request(`/resume/${encodeURIComponent(resumeId)}`)
}

export async function resumePut(
  resumeId: string,
  body: {
    version_name?: string
    title?: string
    specialization?: string
    salary_amount?: number | null
    salary_currency?: string
    employment_types?: string[]
    work_formats?: string[]
    about?: string
    selected_skill_keys?: string[]
  },
): Promise<SiteResume> {
  return request(`/resume/${encodeURIComponent(resumeId)}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export async function resumeDelete(resumeId: string): Promise<void> {
  await request(`/resume/${encodeURIComponent(resumeId)}`, { method: 'DELETE' })
}

export async function resumeGenerate(
  resumeId: string,
  input?: {
    selected_skill_keys?: string[]
    persist?: boolean
  },
): Promise<{
  skills: SiteResumeSkill[]
  branchHints: string[]
  suggestedSpecialization: string | null
  completedCount: number
}> {
  return request(`/resume/${encodeURIComponent(resumeId)}/generate`, {
    method: 'POST',
    body: JSON.stringify(input || {}),
  })
}

export async function resumeGetPreview(resumeId: string): Promise<SiteResumePreview> {
  return request(`/resume/${encodeURIComponent(resumeId)}/preview`)
}

export async function resumeGetQuestionnaire(): Promise<ResumeQuestionnaire> {
  return request('/resume/questionnaire')
}

export async function resumeApplyQuestionnaire(
  resumeId: string,
  input: {
    answers: Record<string, unknown>
    persist?: boolean
  },
): Promise<{
  resume: SiteResume
  branchHints: string[]
  completedCount: number
  suggestedSpecialization: string | null
}> {
  return request(`/resume/${encodeURIComponent(resumeId)}/questionnaire/apply`, {
    method: 'POST',
    body: JSON.stringify({
      answers: input.answers,
      persist: input.persist ?? true,
    }),
  })
}

export async function resumeExport(
  resumeId: string,
  format: 'pdf' | 'docx',
): Promise<ResumeExportResult> {
  return request(`/resume/${encodeURIComponent(resumeId)}/export`, {
    method: 'POST',
    body: JSON.stringify({ format }),
  })
}

export type SkillGapItem = {
  skillKey: string
  learnSlugs: string[]
  reason: string
  cta: string
}

export type SkillGapResult = {
  summary: string
  gaps: SkillGapItem[]
  targetRole: string
}

export async function resumeImproveAbout(
  resumeId: string,
  input?: { text?: string; persist?: boolean },
): Promise<{ about: string; persisted: boolean }> {
  return request(`/resume/${encodeURIComponent(resumeId)}/ai/improve-about`, {
    method: 'POST',
    body: JSON.stringify({
      text: input?.text,
      persist: input?.persist ?? true,
    }),
  })
}

export async function resumeSkillGap(
  resumeId: string,
  input?: { target_role?: string },
): Promise<SkillGapResult> {
  return request(`/resume/${encodeURIComponent(resumeId)}/ai/skill-gap`, {
    method: 'POST',
    body: JSON.stringify({ target_role: input?.target_role }),
  })
}

export async function resumeCoverLetter(
  resumeId: string,
  vacancyText: string,
): Promise<{ letter: string }> {
  return request(`/resume/${encodeURIComponent(resumeId)}/ai/cover-letter`, {
    method: 'POST',
    body: JSON.stringify({ vacancy_text: vacancyText }),
  })
}

export type MockInterviewQuestion = {
  id: string
  skillKey: string
  question: string
  hint: string
}

export async function resumeMockInterviewStart(
  resumeId: string,
  count = 5,
): Promise<{ questions: MockInterviewQuestion[] }> {
  return request(`/resume/${encodeURIComponent(resumeId)}/ai/mock-interview`, {
    method: 'POST',
    body: JSON.stringify({ count }),
  })
}

export async function resumeMockInterviewEvaluate(
  resumeId: string,
  input: { question: string; answer: string; skill_key?: string },
): Promise<{ score: number; feedback: string; passed: boolean }> {
  return request(`/resume/${encodeURIComponent(resumeId)}/ai/mock-interview/evaluate`, {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export type ResumeAdminSettings = {
  rateLimits: {
    ai: { requests: number; windowSec: number }
    generate: { requests: number; windowSec: number }
    preview: { requests: number; windowSec: number }
    export: { requests: number; windowSec: number }
  }
  ai: {
    enabled: boolean
    serviceUrl: string
    model: string
    timeoutSec: number
  }
  strength: {
    photoPoints: number
    aboutPoints: number
    aboutMinLen: number
    learnPointsPerModule: number
    maxScore: number
  }
  features: {
    exportEnabled: boolean
    aiImproveAbout: boolean
    aiSkillGap: boolean
    aiCoverLetter: boolean
    aiMockInterview: boolean
  }
}

export type ResumeAdminSettingsResponse = {
  settings: ResumeAdminSettings
  defaults: ResumeAdminSettings
  envOnly: string[]
}

export async function resumeAdminGetSettings(): Promise<ResumeAdminSettingsResponse> {
  return request('/resume/admin/settings')
}

export async function resumeAdminPutSettings(
  settings: ResumeAdminSettings,
): Promise<ResumeAdminSettingsResponse> {
  return request('/resume/admin/settings', {
    method: 'PUT',
    body: JSON.stringify({ settings }),
  })
}

/** Скачать файл экспорта (JWT). Возвращает object URL. */
export async function resumeDownloadExport(downloadUrl: string): Promise<{
  objectUrl: string
  blob: Blob
}> {
  const token = getSiteAccessToken()
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const url = downloadUrl.startsWith('http')
    ? downloadUrl
    : downloadUrl.startsWith('/api/')
      ? downloadUrl
      : `${API_BASE}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`
  const response = await fetch(url, { headers })
  if (!response.ok) {
    throw new SiteApiError(`Download failed (${response.status})`, response.status)
  }
  const blob = await response.blob()
  return { objectUrl: URL.createObjectURL(blob), blob }
}
