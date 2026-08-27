import { useCallback, useEffect, useState } from 'react'
import {
  getLearnPostBySlug,
  isPostPublished,
  loadLearnPosts,
  type LearnPost,
} from '@/data/learn/learn-store'
import { getSortedRubrics, type LearnRubricId } from '@/data/learn'

export function useLearnPosts(): {
  posts: LearnPost[]
  isReady: boolean
  reload: () => void
} {
  const [posts, setPosts] = useState<LearnPost[]>([])
  const [isReady, setIsReady] = useState(false)

  const reload = useCallback(() => {
    setPosts(loadLearnPosts())
    setIsReady(true)
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  return { posts, isReady, reload }
}

export function useLearnPost(slug: string): {
  post: LearnPost | undefined
  isReady: boolean
  reload: () => void
} {
  const [post, setPost] = useState<LearnPost | undefined>()
  const [isReady, setIsReady] = useState(false)

  const reload = useCallback(() => {
    setPost(getLearnPostBySlug(slug))
    setIsReady(true)
  }, [slug])

  useEffect(() => {
    reload()
  }, [reload])

  return { post, isReady, reload }
}

export function getPublishedPosts(posts: LearnPost[]): LearnPost[] {
  return posts.filter((post) => isPostPublished(post)).sort((a, b) => a.order - b.order)
}

export function getPostsByRubric(posts: LearnPost[], rubricId: LearnRubricId): LearnPost[] {
  return posts.filter((post) => post.rubricId === rubricId).sort((a, b) => a.order - b.order)
}

export function getAdjacentPosts(
  posts: LearnPost[],
  slug: string,
): { prev: LearnPost | undefined; next: LearnPost | undefined } {
  const track = [...posts].sort((a, b) => a.order - b.order)
  const index = track.findIndex((post) => post.slug === slug)
  if (index < 0) {
    return { prev: undefined, next: undefined }
  }
  return {
    prev: track[index - 1],
    next: track[index + 1],
  }
}

export function rubricTitleById(rubricId: LearnRubricId): string {
  return getSortedRubrics().find((rubric) => rubric.id === rubricId)?.title ?? ''
}
