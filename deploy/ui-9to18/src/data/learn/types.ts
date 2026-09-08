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
}

export type LearnRubric = {
  id: LearnRubricId
  title: string
  subtitle: string
  order: number
}
