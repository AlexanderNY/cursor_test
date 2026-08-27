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
}

export type LearnRubric = {
  id: LearnRubricId
  title: string
  subtitle: string
  order: number
}
