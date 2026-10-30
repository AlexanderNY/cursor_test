import type { LearnPost } from '@/data/learn/learn-store'
import { collectInterviewItems } from '@/data/learn/interview-quiz'
import {
  buildRecallSession,
  interviewRecallId,
  readRecallStore,
} from '@/data/learn/recall'
import { practiceForSlug, type PracticeLink } from '@/game/practice/links'

export const SLOT_MS = 25 * 60 * 1000
export const SLOT_STORAGE_KEY = 'learn-slot-v1'
export const SLOT_QUESTION_COUNT = 3

export type SlotQuestion = {
  kind: 'question'
  id: string
  prompt: string
  answer: string
  episodeSlug: string
  episodeTitle: string
  episodeCode: string
}

export type SlotTrainer = {
  kind: 'trainer'
  href: string
  label: string
}

export type SlotStar = { kind: 'star' }

export type SlotStep = SlotStar | SlotQuestion | SlotTrainer

export type SlotRun = {
  startedAt: number
  endsAt: number
  profile: string
  level: string
  steps: SlotStep[]
  index: number
  attempted: string[]
}

const TRAINER_BY_PROFILE: Record<string, PracticeLink> = {
  developer: {
    href: '/game/code?tab=tasks&task=mutable-default',
    label: 'Python: общий список по умолчанию',
  },
  tester: {
    href: '/game/practice?task=broken-api',
    label: 'QA: сломанный ответ API',
  },
  analyst: {
    href: '/game/practice?task=user-story',
    label: 'История и критерии приёмки',
  },
  product_owner: {
    href: '/game/practice?task=user-story',
    label: 'История и критерии приёмки',
  },
  devops: {
    href: '/game/git?task=init-commit',
    label: 'Git: первый commit',
  },
}

export function slotStepKey(step: SlotStep): string {
  if (step.kind === 'star') {
    return 'star'
  }
  if (step.kind === 'trainer') {
    return `trainer:${step.href}`
  }
  return step.id
}

function trainerFor(slugs: string[], profile: string): SlotTrainer {
  for (const slug of slugs) {
    const link = practiceForSlug(slug)
    if (link && !link.href.includes('task=star')) {
      return { kind: 'trainer', href: link.href, label: link.label }
    }
  }
  const fallback = TRAINER_BY_PROFILE[profile] || TRAINER_BY_PROFILE.developer
  return { kind: 'trainer', href: fallback.href, label: fallback.label }
}

export function createSlotRun(
  posts: LearnPost[],
  profile: string,
  level: string,
  now = Date.now(),
): SlotRun {
  const matched = posts.filter((post) => {
    if (profile && !(post.profiles || []).some((id) => id === profile)) {
      return false
    }
    if (level && post.level !== level) {
      return false
    }
    return true
  })
  const cards = collectInterviewItems(matched).map((item) => ({
    id: interviewRecallId(item.episodeSlug, item.question),
    prompt: item.question,
    answer: item.answer,
    episodeSlug: item.episodeSlug,
    episodeTitle: item.episodeTitle,
    episodeCode: item.episodeCode,
  }))
  const picked = buildRecallSession(cards, readRecallStore(), now).slice(0, SLOT_QUESTION_COUNT)
  const questions: SlotQuestion[] = picked.map((item) => ({ kind: 'question', ...item }))
  const steps: SlotStep[] = [
    { kind: 'star' },
    ...questions,
    trainerFor(questions.map((item) => item.episodeSlug), profile),
  ]
  return {
    startedAt: now,
    endsAt: now + SLOT_MS,
    profile,
    level,
    steps,
    index: 0,
    attempted: [],
  }
}

function isSlotStep(value: unknown): value is SlotStep {
  if (!value || typeof value !== 'object') {
    return false
  }
  const row = value as Record<string, unknown>
  if (row.kind === 'star') {
    return true
  }
  if (row.kind === 'trainer') {
    return typeof row.href === 'string' && typeof row.label === 'string'
  }
  if (row.kind !== 'question') {
    return false
  }
  return (
    typeof row.id === 'string' &&
    typeof row.prompt === 'string' &&
    typeof row.answer === 'string' &&
    typeof row.episodeSlug === 'string' &&
    typeof row.episodeTitle === 'string' &&
    typeof row.episodeCode === 'string'
  )
}

export function parseSlotRun(raw: unknown): SlotRun | null {
  if (!raw || typeof raw !== 'object') {
    return null
  }
  const row = raw as Record<string, unknown>
  if (typeof row.startedAt !== 'number' || typeof row.endsAt !== 'number') {
    return null
  }
  if (typeof row.index !== 'number' || !Array.isArray(row.steps) || row.steps.length === 0) {
    return null
  }
  if (!row.steps.every(isSlotStep)) {
    return null
  }
  const attempted = Array.isArray(row.attempted)
    ? row.attempted.filter((item): item is string => typeof item === 'string')
    : []
  return {
    startedAt: row.startedAt,
    endsAt: row.endsAt,
    profile: typeof row.profile === 'string' ? row.profile : '',
    level: typeof row.level === 'string' ? row.level : '',
    steps: row.steps,
    index: Math.min(Math.max(0, row.index), row.steps.length),
    attempted,
  }
}

export function readSlotRun(): SlotRun | null {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    return parseSlotRun(JSON.parse(window.sessionStorage.getItem(SLOT_STORAGE_KEY) || 'null'))
  } catch {
    return null
  }
}

export function writeSlotRun(run: SlotRun | null): void {
  if (run) {
    window.sessionStorage.setItem(SLOT_STORAGE_KEY, JSON.stringify(run))
    return
  }
  window.sessionStorage.removeItem(SLOT_STORAGE_KEY)
}

export function formatSlotLeft(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}
