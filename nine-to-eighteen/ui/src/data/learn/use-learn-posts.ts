import { useCallback, useEffect, useState } from 'react'
import {
  getLearnPostBySlug,
  isPostPublished,
  loadLearnPosts,
  type LearnPost,
} from '@/data/learn/learn-store'
import { getSortedRubrics, type LearnRubricId } from '@/data/learn'

export function useLearnPosts(opts?: { admin?: boolean }): {
  posts: LearnPost[]
  isReady: boolean
  error: string
  reload: () => void
} {
  const [posts, setPosts] = useState<LearnPost[]>([])
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState('')
  const admin = Boolean(opts?.admin)

  const reload = useCallback(() => {
    setIsReady(false)
    setError('')
    void loadLearnPosts({ admin })
      .then((list) => {
        setPosts(list)
        setIsReady(true)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить Learn')
        setPosts([])
        setIsReady(true)
      })
  }, [admin])

  useEffect(() => {
    reload()
  }, [reload])

  return { posts, isReady, error, reload }
}

export function useLearnPost(
  slug: string,
  opts?: { admin?: boolean; preview?: boolean },
): {
  post: LearnPost | undefined
  isReady: boolean
  error: string
  reload: () => void
} {
  const [post, setPost] = useState<LearnPost | undefined>()
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState('')
  const admin = Boolean(opts?.admin)
  const preview = Boolean(opts?.preview)

  const reload = useCallback(() => {
    setIsReady(false)
    setError('')
    void getLearnPostBySlug(slug, { admin, preview })
      .then((item) => {
        setPost(item)
        setIsReady(true)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить выпуск')
        setPost(undefined)
        setIsReady(true)
      })
  }, [slug, admin, preview])

  useEffect(() => {
    reload()
  }, [reload])

  return { post, isReady, error, reload }
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
  const current = track[index]
  const seasonPrefix = current.episode.replace(/\d+$/, '') || current.episode.slice(0, 1)
  const sameSeason = track.filter((post) => {
    const prefix = post.episode.replace(/\d+$/, '') || post.episode.slice(0, 1)
    return prefix === seasonPrefix
  })
  const seasonIndex = sameSeason.findIndex((post) => post.slug === slug)
  if (seasonIndex >= 0) {
    return {
      prev: sameSeason[seasonIndex - 1],
      next: sameSeason[seasonIndex + 1],
    }
  }
  return {
    prev: track[index - 1],
    next: track[index + 1],
  }
}

export function getSeasonTracks(posts: LearnPost[]): {
  id: string
  title: string
  note: string
  episodes: LearnPost[]
}[] {
  const published = getPublishedPosts(posts)
  const seasonB = published.filter((post) => post.episode.startsWith('B'))
  const seasonS01 = published.filter((post) => post.episode.startsWith('S01'))
  const seasonPy = published.filter((post) => post.episode.startsWith('PY'))
  const seasonQa = published.filter((post) => post.episode.startsWith('QA'))
  const seasonMap = published.filter((post) => post.episode.startsWith('MAP'))
  const other = published.filter((post) => {
    const ep = post.episode
    return (
      !ep.startsWith('B') &&
      !ep.startsWith('S01') &&
      !ep.startsWith('PY') &&
      !ep.startsWith('QA') &&
      !ep.startsWith('MAP')
    )
  })
  const tracks: {
    id: string
    title: string
    note: string
    episodes: LearnPost[]
  }[] = []
  if (seasonB.length > 0) {
    tracks.push({
      id: 'b',
      title: 'Сезон B · Первое приложение',
      note: 'Git → Python → React → Docker. Сквозной проект notes.',
      episodes: seasonB,
    })
  }
  if (seasonS01.length > 0) {
    tracks.push({
      id: 's01',
      title: 'Сезон 1 · Слои и стенд',
      note: 'Углубление: заявки, Postgres, Compose, Minikube.',
      episodes: seasonS01,
    })
  }
  if (seasonPy.length > 0) {
    tracks.push({
      id: 'py',
      title: 'Python · Junior → Senior',
      note: 'PY01–PY24 к собеседованию разработчика.',
      episodes: seasonPy,
    })
  }
  if (seasonQa.length > 0) {
    tracks.push({
      id: 'qa',
      title: 'QA · Junior → Senior',
      note: 'QA01–QA24: тестирование, AQA, middle и senior.',
      episodes: seasonQa,
    })
  }
  if (seasonMap.length > 0) {
    tracks.push({
      id: 'map',
      title: 'Карта · листья собеса',
      note: 'Статьи, привязанные к learning-map.',
      episodes: seasonMap,
    })
  }
  if (other.length > 0) {
    tracks.push({
      id: 'other',
      title: 'Другие выпуски',
      note: 'Вне основных сезонов',
      episodes: other,
    })
  }
  return tracks
}

export function rubricTitleById(rubricId: LearnRubricId): string {
  return getSortedRubrics().find((rubric) => rubric.id === rubricId)?.title ?? ''
}
