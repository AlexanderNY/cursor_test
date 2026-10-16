import { extractSqlBlocks } from '@/game/sql/sandbox-sqlite'
import type { LearnPost } from '@/data/learn/learn-store'

export type LearnSqlSnippet = {
  slug: string
  episode: string
  title: string
  shortTitle: string
  blockIndex: number
  code: string
  source: 'lab' | 'theory'
}

/** Collect ```sql blocks from SQL Learn posts (episode SQL*). */
export function collectLearnSqlSnippets(posts: LearnPost[]): LearnSqlSnippet[] {
  const snippets: LearnSqlSnippet[] = []
  for (const post of posts) {
    if (!post.episode?.toUpperCase().startsWith('SQL')) {
      continue
    }
    const lab =
      post.structured?.lab?.trim() ||
      post.lab?.trim() ||
      ''
    const theory =
      post.structured?.sections?.map((section) => section.body).join('\n\n') ||
      post.theory ||
      ''
    const labBlocks = extractSqlBlocks(lab)
    labBlocks.forEach((code, blockIndex) => {
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
    const theoryBlocks = extractSqlBlocks(theory)
    theoryBlocks.forEach((code, blockIndex) => {
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
