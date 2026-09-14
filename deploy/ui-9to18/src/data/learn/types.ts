export type LearnRubricId =
  | 'architecture'
  | 'api'
  | 'data'
  | 'frontend'
  | 'tools'

export type LearnLink = {
  label: string
  href: string
}

export type LearnEpisode = {
  slug: string
  episode: string
  title: string
  shortTitle: string
  rubricId: LearnRubricId
  order: number
  theory: string
  lab: string
  links: LearnLink[]
  diagram: string
  cheatsheet: string
  /** Unified article body (intro/sections/quiz/anki). Optional on local seed until migrated. */
  structured?: import('@/data/site/structured-post').StructuredPost | null
  profiles?: import('@/data/learn/labels').LearnProfileId[]
  level?: import('@/data/learn/labels').LearnLevelId | ''
  tags?: string[]
  excerpt?: string
  durationMin?: number
  prerequisites?: string[]
  author?: string
  authorUrl?: string
  coverUrl?: string
  seoTitle?: string
  seoDescription?: string
  seoKeywords?: string[]
  canonicalUrl?: string
}

export type LearnRubric = {
  id: LearnRubricId
  title: string
  subtitle: string
  order: number
}
