import { learnEpisodes } from './episodes'
import { learnRubrics } from './rubrics'
import type { LearnEpisode, LearnRubric, LearnRubricId } from './types'

export type { LearnEpisode, LearnLink, LearnRubric, LearnRubricId } from './types'
export type { LearnLevelId, LearnProfileId } from './labels'
export { learnEpisodes } from './episodes'
export { learnRubrics } from './rubrics'
export {
  LEARN_LEVELS,
  LEARN_PROFILES,
  LEARN_KNOWLEDGE_MAP_TAG,
  hasKnowledgeMapTag,
  isLearnLevelId,
  isLearnProfileId,
  levelLabel,
  normalizeLevel,
  normalizeProfiles,
  normalizeStringList,
  profileLabel,
  withKnowledgeMapTag,
} from './labels'

const episodeBySlug = new Map(learnEpisodes.map((episode) => [episode.slug, episode]))

export function getEpisodeBySlug(slug: string): LearnEpisode | undefined {
  return episodeBySlug.get(slug)
}

export function getEpisodesByRubric(rubricId: LearnRubricId): LearnEpisode[] {
  return learnEpisodes
    .filter((episode) => episode.rubricId === rubricId)
    .sort((a, b) => a.order - b.order)
}

export function getSortedRubrics(): LearnRubric[] {
  return [...learnRubrics].sort((a, b) => a.order - b.order)
}

export function getSeasonTrack(): LearnEpisode[] {
  return [...learnEpisodes].sort((a, b) => a.order - b.order)
}

export function getAdjacentEpisodes(slug: string): {
  prev: LearnEpisode | undefined
  next: LearnEpisode | undefined
} {
  const track = getSeasonTrack()
  const index = track.findIndex((episode) => episode.slug === slug)
  if (index < 0) {
    return { prev: undefined, next: undefined }
  }
  return {
    prev: track[index - 1],
    next: track[index + 1],
  }
}
