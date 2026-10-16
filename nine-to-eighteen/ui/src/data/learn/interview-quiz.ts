/** Interview quiz sourced from Learn articles.
 * Questions and correct answers are taken verbatim from
 * «Частые вопросы с собеседования». A pair is kept only when the answer
 * text is present in that article.
 */

export const INTERVIEW_TRACKS = [
  { id: 'all', label: 'Все' },
  { id: 'python', label: 'Python' },
  { id: 'sql', label: 'SQL' },
  { id: 'java', label: 'Java' },
  { id: 'javascript', label: 'JavaScript' },
  { id: 'redis', label: 'Redis' },
  { id: 'qa', label: 'QA' },
  { id: 'sa', label: 'Аналитика' },
  { id: 'product', label: 'Продукт' },
] as const

export type InterviewTrackId = (typeof INTERVIEW_TRACKS)[number]['id']

export type InterviewArticle = {
  slug: string
  title: string
  episode: string
  tags: string[]
  theory: string
  structured: {
    intro: string
    sections: Array<{ heading: string; body: string }>
  } | null
}

export type InterviewItem = {
  question: string
  answer: string
  quote: string
  episodeSlug: string
  episodeTitle: string
  episodeCode: string
  track: Exclude<InterviewTrackId, 'all'> | 'other'
}

export type InterviewQuizQuestion = {
  id: string
  prompt: string
  options: string[]
  correctIndex: number
  episodeSlug: string
  episodeTitle: string
  episodeCode: string
  answer: string
}

const PAIR_RE =
  /\*\*Вопрос\.\*\*\s*([\s\S]*?)\s*\*\*Ответ\.\*\*\s*([\s\S]*?)(?=\n\s*\*\*Вопрос\.\*\*|$)/gi

const TRACK_ORDER: Array<Exclude<InterviewTrackId, 'all'>> = [
  'python',
  'javascript',
  'java',
  'qa',
  'sa',
  'product',
  'redis',
  'sql',
]

export function normalizeQuizText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[`*_>#]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function textAppearsIn(haystack: string, needle: string): boolean {
  const sample = normalizeQuizText(needle)
  if (sample.length < 12) {
    return false
  }
  return normalizeQuizText(haystack).includes(sample)
}

export function interviewTrackOf(tags: string[]): InterviewItem['track'] {
  const set = new Set(tags.map((tag) => tag.trim().toLowerCase()))
  if (set.has('js')) {
    set.add('javascript')
  }
  for (const track of TRACK_ORDER) {
    if (set.has(track)) {
      return track
    }
  }
  return 'other'
}

function flatten(value: string): string {
  return value.replace(/\s+/g, ' ').trim()
}

/** Verbatim slice of the article answer, short enough for an option. */
export function quoteFromAnswer(answer: string): string {
  const flat = flatten(answer)
  if (flat.length <= 280) {
    return flat
  }
  const end = flat.search(/[.!?](\s|$)/)
  if (end >= 40 && end <= 280) {
    return flat.slice(0, end + 1).trim()
  }
  const cut = flat.slice(0, 240)
  const space = cut.lastIndexOf(' ')
  return (space > 40 ? cut.slice(0, space) : cut).trim()
}

function interviewSectionTexts(article: InterviewArticle): string[] {
  const sections = article.structured?.sections ?? []
  const fromStructured = sections
    .filter((section) => /собеседован/i.test(section.heading))
    .map((section) => section.body.trim())
    .filter(Boolean)
  if (fromStructured.length > 0) {
    return fromStructured
  }
  const theory = article.theory || ''
  const found: string[] = []
  const headingRe = /^##\s+[^\n]*собеседован[^\n]*\n+([\s\S]*?)(?=^##\s+|\s*$)/gim
  for (const match of theory.matchAll(headingRe)) {
    const body = (match[1] || '').trim()
    if (body) {
      found.push(body)
    }
  }
  return found
}

function articleCorpus(article: InterviewArticle): string {
  const parts = [article.structured?.intro || '', article.theory || '']
  for (const section of article.structured?.sections ?? []) {
    parts.push(section.heading, section.body)
  }
  return parts.join('\n')
}

function parsePairs(sectionBody: string): Array<{ question: string; answer: string }> {
  const pairs: Array<{ question: string; answer: string }> = []
  for (const match of sectionBody.matchAll(PAIR_RE)) {
    const question = flatten(match[1] || '')
    const answer = flatten(match[2] || '')
    if (question.length < 8 || answer.length < 24) {
      continue
    }
    pairs.push({ question, answer })
  }
  return pairs
}

export function collectInterviewItems(articles: InterviewArticle[]): InterviewItem[] {
  const items: InterviewItem[] = []
  const seen = new Set<string>()
  for (const article of articles) {
    const corpus = articleCorpus(article)
    const track = interviewTrackOf(article.tags)
    for (const sectionBody of interviewSectionTexts(article)) {
      for (const pair of parsePairs(sectionBody)) {
        if (!textAppearsIn(sectionBody, pair.answer) || !textAppearsIn(corpus, pair.answer)) {
          continue
        }
        const quote = quoteFromAnswer(pair.answer)
        if (!textAppearsIn(pair.answer, quote) || !textAppearsIn(corpus, quote)) {
          continue
        }
        const key = `${article.slug}::${normalizeQuizText(pair.question)}`
        if (seen.has(key)) {
          continue
        }
        seen.add(key)
        items.push({
          question: pair.question,
          answer: pair.answer,
          quote,
          episodeSlug: article.slug,
          episodeTitle: article.title,
          episodeCode: article.episode,
          track,
        })
      }
    }
  }
  return items
}

function hashSeed(text: string, seed: number): number {
  let state = seed >>> 0 || 1
  for (let index = 0; index < text.length; index += 1) {
    state = Math.imul(state ^ text.charCodeAt(index), 16777619) >>> 0
  }
  return state || 1
}

export function shuffleWithSeed<T>(items: T[], seed: number): T[] {
  const copy = [...items]
  let state = seed >>> 0 || 1
  const next = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0
    return state / 0x100000000
  }
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(next() * (index + 1))
    const current = copy[index]
    copy[index] = copy[swap]
    copy[swap] = current
  }
  return copy
}

export function countByTrack(items: InterviewItem[]): Record<InterviewTrackId, number> {
  const counts = Object.fromEntries(INTERVIEW_TRACKS.map((track) => [track.id, 0])) as Record<
    InterviewTrackId,
    number
  >
  for (const item of items) {
    counts.all += 1
    if (item.track !== 'other') {
      counts[item.track] += 1
    }
  }
  return counts
}

export function buildInterviewQuiz(
  items: InterviewItem[],
  options: { track: InterviewTrackId; size: number; seed: number },
): InterviewQuizQuestion[] {
  const pool =
    options.track === 'all' ? items : items.filter((item) => item.track === options.track)
  if (pool.length === 0) {
    return []
  }
  const picked = shuffleWithSeed(pool, options.seed).slice(0, Math.min(options.size, pool.length))
  const questions: InterviewQuizQuestion[] = []
  picked.forEach((item, index) => {
    const sameArticle = pool.filter(
      (other) =>
        other.episodeSlug === item.episodeSlug &&
        normalizeQuizText(other.quote) !== normalizeQuizText(item.quote),
    )
    const sameTrack = pool.filter(
      (other) =>
        other.track === item.track &&
        other.episodeSlug !== item.episodeSlug &&
        normalizeQuizText(other.quote) !== normalizeQuizText(item.quote),
    )
    const anywhere = pool.filter(
      (other) => normalizeQuizText(other.quote) !== normalizeQuizText(item.quote),
    )
    const distractorPool = [...sameArticle, ...sameTrack, ...anywhere]
    const distractors: string[] = []
    const used = new Set<string>([normalizeQuizText(item.quote)])
    for (const candidate of shuffleWithSeed(distractorPool, hashSeed(item.question, options.seed + index))) {
      const key = normalizeQuizText(candidate.quote)
      if (used.has(key)) {
        continue
      }
      if (!textAppearsIn(candidate.answer, candidate.quote)) {
        continue
      }
      used.add(key)
      distractors.push(candidate.quote)
      if (distractors.length >= 3) {
        break
      }
    }
    if (distractors.length < 1) {
      return
    }
    const choices = shuffleWithSeed([item.quote, ...distractors], hashSeed(item.episodeSlug, options.seed + index + 3))
    const correctIndex = choices.findIndex(
      (choice) => normalizeQuizText(choice) === normalizeQuizText(item.quote),
    )
    if (correctIndex < 0) {
      return
    }
    questions.push({
      id: `${item.episodeSlug}-${index}-${options.seed}`,
      prompt: item.question,
      options: choices,
      correctIndex,
      episodeSlug: item.episodeSlug,
      episodeTitle: item.episodeTitle,
      episodeCode: item.episodeCode,
      answer: item.answer,
    })
  })
  return questions
}
