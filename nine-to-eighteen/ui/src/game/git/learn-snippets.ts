import { extractGitBlocks } from '@/game/git/sandbox-git'
import type { LearnPost } from '@/data/learn/learn-store'

export type LearnGitSnippet = {
  slug: string
  episode: string
  title: string
  shortTitle: string
  blockIndex: number
  code: string
  source: 'lab' | 'theory'
}

const GIT_SLUGS = new Set([
  'b01-karta',
  'b05-api-check',
  's01e03-git',
  'qa-pytest-ci-git',
])

function isGitPost(post: LearnPost): boolean {
  if (post.episode?.toUpperCase().startsWith('GIT')) return true
  if (GIT_SLUGS.has(post.slug)) return true
  return (post.tags || []).includes('git')
}

/** Collect ```bash blocks with git from Git Learn posts. */
export function collectLearnGitSnippets(posts: LearnPost[]): LearnGitSnippet[] {
  const snippets: LearnGitSnippet[] = []
  for (const post of posts) {
    if (!isGitPost(post)) continue
    const lab = post.structured?.lab?.trim() || post.lab?.trim() || ''
    const theory =
      post.structured?.sections?.map((section) => section.body).join('\n\n') ||
      post.theory ||
      ''
    extractGitBlocks(lab).forEach((code, blockIndex) => {
      snippets.push({
        slug: post.slug,
        episode: post.episode,
        title: post.title,
        shortTitle: post.shortTitle || post.title,
        blockIndex,
        code,
        source: 'lab',
      })
    })
    extractGitBlocks(theory).forEach((code, blockIndex) => {
      snippets.push({
        slug: post.slug,
        episode: post.episode,
        title: post.title,
        shortTitle: post.shortTitle || post.title,
        blockIndex,
        code,
        source: 'theory',
      })
    })
  }
  return snippets.sort((a, b) => {
    const ep = a.episode.localeCompare(b.episode, undefined, { numeric: true })
    if (ep !== 0) return ep
    if (a.source !== b.source) return a.source === 'lab' ? -1 : 1
    return a.blockIndex - b.blockIndex
  })
}
