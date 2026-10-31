import type { LearnPost } from '@/data/learn/learn-store'

export type StudyPathItem = {
  slug: string
  post: LearnPost | undefined
}

export type StudyPath = {
  before: StudyPathItem[]
  after: StudyPathItem[]
}

/** Before = own prerequisites; after = articles that list this slug as a prerequisite. */
export function buildStudyPath(slug: string, prerequisites: string[], posts: LearnPost[]): StudyPath {
  const bySlug = new Map(posts.map((post) => [post.slug, post]))
  const before = prerequisites
    .filter((item) => item && item !== slug)
    .map((item) => ({ slug: item, post: bySlug.get(item) }))
  const after = posts
    .filter((post) => post.slug !== slug && post.prerequisites?.includes(slug))
    .sort((a, b) => a.order - b.order)
    .map((post) => ({ slug: post.slug, post }))
  return { before, after }
}
