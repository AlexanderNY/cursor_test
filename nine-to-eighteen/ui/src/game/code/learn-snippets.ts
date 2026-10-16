import { extractPythonBlocks } from '@/game/code/sandbox-pyodide'
import type { LearnPost } from '@/data/learn/learn-store'

export type LearnPythonSnippet = {
  slug: string
  episode: string
  title: string
  shortTitle: string
  blockIndex: number
  code: string
  source: 'lab' | 'theory'
}

/** Collect runnable ```python blocks from Python Learn posts. */
export function collectLearnPythonSnippets(posts: LearnPost[]): LearnPythonSnippet[] {
  const snippets: LearnPythonSnippet[] = []
  for (const post of posts) {
    if (!post.episode?.toUpperCase().startsWith('PY')) {
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
    const labBlocks = extractPythonBlocks(lab)
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
    const theoryBlocks = extractPythonBlocks(theory)
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
