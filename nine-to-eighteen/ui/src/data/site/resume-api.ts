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
  updatedAt: string | null
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

export type SiteResumePreview = {
  profile: SiteUserProfile
  resume: SiteResume
  skills: SiteResumeSkill[]
  branchHints: string[]
  suggestedSpecialization: string | null
  completedCount: number
  username: string
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

export async function resumeGet(): Promise<SiteResume> {
  return request('/resume')
}

export async function resumePut(body: {
  title?: string
  specialization?: string
  salary_amount?: number | null
  salary_currency?: string
  employment_types?: string[]
  work_formats?: string[]
  about?: string
  selected_skill_keys?: string[]
}): Promise<SiteResume> {
  return request('/resume', {
    method: 'PUT',
    body: JSON.stringify(body),
  })
}

export async function resumeGenerate(input?: {
  selected_skill_keys?: string[]
  persist?: boolean
}): Promise<{
  skills: SiteResumeSkill[]
  branchHints: string[]
  suggestedSpecialization: string | null
  completedCount: number
}> {
  return request('/resume/generate', {
    method: 'POST',
    body: JSON.stringify(input || {}),
  })
}

export async function resumeGetPreview(): Promise<SiteResumePreview> {
  return request('/resume/preview')
}

export async function resumeGetQuestionnaire(): Promise<ResumeQuestionnaire> {
  return request('/resume/questionnaire')
}

export async function resumeApplyQuestionnaire(input: {
  answers: Record<string, unknown>
  persist?: boolean
}): Promise<{
  resume: SiteResume
  branchHints: string[]
  completedCount: number
  suggestedSpecialization: string | null
}> {
  return request('/resume/questionnaire/apply', {
    method: 'POST',
    body: JSON.stringify({
      answers: input.answers,
      persist: input.persist ?? true,
    }),
  })
}
