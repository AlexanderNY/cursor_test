import type { LearnPost } from '@/data/learn/learn-store'
import { hydrateLearnStructured, learnMnemonicDrills } from '@/data/site/structured-post'
import type { MindNode } from '@/data/learning-map/parse-outline'
import { SEED_MNEMONIC_DRILLS } from '@/data/mnemonics/seed-drills'
import type { MnemonicDrillCard, MnemonicTechniqueId } from '@/data/mnemonics/types'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^\wа-яё]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48)
}

export function collectMnemonicDrillsFromPosts(posts: LearnPost[]): MnemonicDrillCard[] {
  const out: MnemonicDrillCard[] = []
  for (const post of posts) {
    const structured = hydrateLearnStructured(post.structured, {
      lab: post.lab,
      cheatsheet: post.cheatsheet,
      cheatsheetFormat: post.cheatsheetFormat,
      diagram: post.diagram,
    })
    const drills = learnMnemonicDrills(structured)
    drills.forEach((drill, index) => {
      out.push({
        ...drill,
        id: `learn/${post.slug}#mnemonic-${index}`,
        learnSlug: post.slug,
        learnTitle: post.shortTitle || post.title,
        learnHref: `/game/learn/${post.slug}`,
        episode: post.episode,
        tags: post.tags || [],
        branchId: post.slug,
        branchTitle: post.shortTitle || post.title,
      })
    })
  }
  return out
}

export function withSeedMnemonicDrills(cards: MnemonicDrillCard[]): MnemonicDrillCard[] {
  if (cards.length > 0) {
    return cards
  }
  return SEED_MNEMONIC_DRILLS.map((drill, index) => ({
    ...drill,
    id: `seed/${drill.learnSlug}#mnemonic-${index}`,
    learnHref: `/game/learn/${drill.learnSlug}`,
    tags: [drill.technique],
    branchId: drill.learnSlug,
    branchTitle: drill.learnTitle,
  }))
}

export function filterMnemonicDrills(
  cards: MnemonicDrillCard[],
  options: {
    techniques?: MnemonicTechniqueId[]
    learnSlugs?: string[]
    branchIds?: string[]
  } = {},
): MnemonicDrillCard[] {
  const techniques = options.techniques || []
  const learnSlugs = options.learnSlugs || []
  const branchIds = options.branchIds || []
  return cards.filter((card) => {
    if (techniques.length > 0 && !techniques.includes(card.technique)) {
      return false
    }
    if (learnSlugs.length > 0 && !learnSlugs.includes(card.learnSlug)) {
      return false
    }
    if (branchIds.length > 0 && !branchIds.includes(card.branchId)) {
      return false
    }
    return true
  })
}

function walkLearnSlugs(
  node: MindNode,
  path: MindNode[],
  onlyNodeId: string | null | undefined,
  out: Map<string, { branchId: string; branchTitle: string }>,
): void {
  const nextPath = [...path, node]
  const branch = nextPath[1] || node
  if (node.learnSlug) {
    const include =
      !onlyNodeId ||
      node.id === onlyNodeId ||
      nextPath.some((item) => item.id === onlyNodeId)
    if (include) {
      out.set(node.learnSlug, {
        branchId: branch.id,
        branchTitle: branch.title,
      })
    }
  }
  for (const child of node.children) {
    walkLearnSlugs(child, nextPath, onlyNodeId, out)
  }
}

/** Collect drills for a map leaf / branch from linked Learn posts. */
export function collectMnemonicDrillsForMap(
  root: MindNode,
  posts: LearnPost[],
  options: { nodeId?: string | null } = {},
): MnemonicDrillCard[] {
  const slugMeta = new Map<string, { branchId: string; branchTitle: string }>()
  walkLearnSlugs(root, [], options.nodeId, slugMeta)
  if (slugMeta.size === 0) {
    return []
  }
  const postsBySlug = new Map(posts.map((post) => [post.slug, post]))
  const out: MnemonicDrillCard[] = []
  for (const [slug, meta] of slugMeta) {
    const post = postsBySlug.get(slug)
    if (!post) {
      continue
    }
    const structured = hydrateLearnStructured(post.structured, {
      lab: post.lab,
      cheatsheet: post.cheatsheet,
      cheatsheetFormat: post.cheatsheetFormat,
      diagram: post.diagram,
    })
    learnMnemonicDrills(structured).forEach((drill, index) => {
      out.push({
        ...drill,
        id: `map/${meta.branchId}/${slug}#mnemonic-${index}-${slugify(drill.title)}`,
        learnSlug: post.slug,
        learnTitle: post.shortTitle || post.title,
        learnHref: `/game/learn/${post.slug}`,
        episode: post.episode,
        tags: post.tags || [],
        branchId: meta.branchId,
        branchTitle: meta.branchTitle,
      })
    })
  }
  return out
}

const PROGRESS_KEY = '9to18.mnemonics.progress'

export function loadMnemonicProgress(): Record<string, number> {
  try {
    const raw = localStorage.getItem(PROGRESS_KEY)
    if (!raw) {
      return {}
    }
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {}
    }
    const out: Record<string, number> = {}
    for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof value === 'number' && Number.isFinite(value)) {
        out[key] = value
      }
    }
    return out
  } catch {
    return {}
  }
}

export function markMnemonicDone(cardId: string): void {
  const next = loadMnemonicProgress()
  next[cardId] = Date.now()
  try {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(next))
  } catch {
    /* ignore quota */
  }
}
