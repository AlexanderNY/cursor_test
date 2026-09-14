/** Learn article Markdown file: YAML frontmatter + structured sections. */

import type { LearnRubricId } from '@/data/learn/types'
import {
  LEARN_LEVELS,
  LEARN_PROFILES,
  hasKnowledgeMapTag,
  withKnowledgeMapTag,
  type LearnLevelId,
  type LearnProfileId,
} from '@/data/learn/labels'
import {
  EMPTY_LEARN_META,
  normalizeLearnMeta,
  type LearnPostInput,
  type LearnPostMeta,
} from '@/data/learn/learn-store'
import type { StructuredPost } from '@/data/site/structured-post'
import { EMPTY_LEARN_STRUCTURED_POST } from '@/data/site/structured-post'

const VALID_RUBRICS = new Set<LearnRubricId>([
  'architecture',
  'api',
  'data',
  'frontend',
  'tools',
])

export type LearnArticleFilePayload = LearnPostInput & {
  warnings: string[]
}

function escapeYamlScalar(value: string): string {
  if (/^[A-Za-z0-9._/-]+$/.test(value) && !/^(true|false|null)$/i.test(value)) {
    return value
  }
  return JSON.stringify(value)
}

function parseYamlScalar(raw: string): string {
  const value = raw.trim()
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    try {
      return JSON.parse(value.replace(/^'/, '"').replace(/'$/, '"')) as string
    } catch {
      return value.slice(1, -1)
    }
  }
  return value
}

function parseYamlList(raw: string): string[] {
  const text = raw.trim()
  if (text.startsWith('[') && text.endsWith(']')) {
    const inner = text.slice(1, -1).trim()
    if (!inner) {
      return []
    }
    const parts: string[] = []
    let buf = ''
    let inQuote = false
    let quoteChar = ''
    for (const ch of inner) {
      if (inQuote) {
        buf += ch
        if (ch === quoteChar) {
          inQuote = false
        }
        continue
      }
      if (ch === '"' || ch === "'") {
        inQuote = true
        quoteChar = ch
        buf += ch
        continue
      }
      if (ch === ',') {
        parts.push(parseYamlScalar(buf))
        buf = ''
        continue
      }
      buf += ch
    }
    if (buf.trim()) {
      parts.push(parseYamlScalar(buf))
    }
    return parts.filter(Boolean)
  }
  return text
    .replace(/;/g, ',')
    .split(',')
    .map((part) => parseYamlScalar(part))
    .filter(Boolean)
}

function parseBool(raw: string | undefined): boolean | null {
  if (raw == null || raw === '') {
    return null
  }
  const value = raw.trim().toLowerCase()
  if (value === 'true' || value === '1' || value === 'yes') {
    return true
  }
  if (value === 'false' || value === '0' || value === 'no') {
    return false
  }
  return null
}

function formatYamlList(values: string[]): string {
  if (values.length === 0) {
    return '[]'
  }
  return `[${values.map((value) => escapeYamlScalar(value)).join(', ')}]`
}

function splitSections(body: string): Array<{ title: string; content: string }> {
  const headingRe = /^##\s+(.+)$/gm
  const matches = [...body.matchAll(headingRe)]
  if (matches.length === 0) {
    const text = body.trim()
    return text ? [{ title: 'Введение', content: text }] : []
  }
  const sections: Array<{ title: string; content: string }> = []
  const firstIndex = matches[0].index ?? 0
  const preamble = body.slice(0, firstIndex).trim()
  if (preamble) {
    sections.push({ title: '', content: preamble })
  }
  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index]
    const title = (match[1] || '').trim()
    const start = (match.index ?? 0) + match[0].length
    const end = index + 1 < matches.length ? (matches[index + 1].index ?? body.length) : body.length
    sections.push({ title, content: body.slice(start, end).trim() })
  }
  return sections
}

function parseQuiz(block: string): StructuredPost['quiz'] {
  const chunks = block.split(/^###\s+/m)
  const items: StructuredPost['quiz'] = []
  for (const chunk of chunks) {
    const text = chunk.trim()
    if (!text) {
      continue
    }
    const lines = text.split(/\r?\n/)
    const question = (lines[0] || '').trim()
    const rest = lines.slice(1).join('\n').trim()
    const answerMatch = /\*\*Ответ:\*\*\s*([^\n]+)/i.exec(rest)
    const explainMatch = /\*\*Пояснение:\*\*\s*([\s\S]*?)(?=\n\*\*|\s*$)/i.exec(rest)
    const answer = answerMatch?.[1]?.trim() || ''
    const explain = explainMatch?.[1]?.trim() || ''
    if (question || answer) {
      items.push({ question, answer, explain })
    }
  }
  return items
}

function parseAnki(block: string): StructuredPost['anki'] {
  const chunks = block.split(/^###\s+/m)
  const items: StructuredPost['anki'] = []
  for (const chunk of chunks) {
    const text = chunk.trim()
    if (!text) {
      continue
    }
    const lines = text.split(/\r?\n/)
    const front = (lines[0] || '').replace(/^Front:\s*/i, '').trim()
    const rest = lines.slice(1).join('\n').trim()
    const backMatch = /^Back:\s*([\s\S]*)$/im.exec(rest)
    const back = (backMatch?.[1] || rest).trim()
    if (front || back) {
      items.push({ front, back })
    }
  }
  return items
}

function parseLinks(block: string): LearnPostInput['links'] {
  const links: LearnPostInput['links'] = []
  for (const line of block.split(/\r?\n/)) {
    const trimmed = line.trim().replace(/^[-*]\s+/, '').trim()
    if (!trimmed) {
      continue
    }
    const md = /\[([^\]]+)\]\(([^)]+)\)/.exec(trimmed)
    if (md) {
      links.push({ label: md[1].trim(), href: md[2].trim() })
      continue
    }
    if (trimmed.includes('|')) {
      const [label, ...rest] = trimmed.split('|')
      links.push({ label: label.trim(), href: rest.join('|').trim() || '#' })
      continue
    }
    links.push({ label: trimmed, href: '#' })
  }
  return links
}

function parseSummary(block: string): string[] {
  return block
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[-*]\s+/, '').trim())
    .filter(Boolean)
}

export function parseLearnArticleFile(
  text: string,
  fallback: Partial<LearnPostInput> = {},
): LearnArticleFilePayload {
  const warnings: string[] = []
  const source = text.replace(/^\uFEFF/, '')
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/.exec(source)
  const meta: Record<string, string> = {}
  let body = source
  if (match) {
    for (const line of match[1].split(/\r?\n/)) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) {
        continue
      }
      const colon = trimmed.indexOf(':')
      if (colon <= 0) {
        continue
      }
      const key = trimmed.slice(0, colon).trim().toLowerCase()
      meta[key] = trimmed.slice(colon + 1).trim()
    }
    body = match[2]
  } else {
    warnings.push('Нет YAML frontmatter — метаданные будут из fallback')
  }

  const metaList = (key: string): string[] =>
    meta[key] != null && meta[key] !== '' ? parseYamlList(meta[key]) : []

  let rubric = (meta.rubric || meta.rubricid || fallback.rubricId || 'architecture')
    .trim()
    .toLowerCase() as LearnRubricId
  if (!VALID_RUBRICS.has(rubric)) {
    warnings.push(`Неизвестная рубрика '${rubric}', поставлено architecture`)
    rubric = 'architecture'
  }

  for (const raw of metaList('profiles')) {
    if (!LEARN_PROFILES.some((p) => p.id === raw.trim().toLowerCase())) {
      warnings.push(`Пропущен неизвестный профиль: ${raw}`)
    }
  }
  const levelRaw = (meta.level || '').trim().toLowerCase()
  if (levelRaw && !LEARN_LEVELS.some((l) => l.id === levelRaw)) {
    warnings.push(`Неизвестный уровень '${levelRaw}'`)
  }

  let intro = ''
  const sections: StructuredPost['sections'] = []
  const diagrams: StructuredPost['diagrams'] = []
  let quiz: StructuredPost['quiz'] = []
  let anki: StructuredPost['anki'] = []
  let summary: string[] = []
  let lab = ''
  let cheatsheetHtml = ''
  const appendixParts: string[] = []
  let links: LearnPostInput['links'] = []

  for (const { title, content } of splitSections(body)) {
    const lower = title.toLowerCase()
    if (!title || lower === 'введение' || lower === 'intro') {
      if (!title && content) {
        appendixParts.push(content)
      } else {
        intro = intro ? `${intro}\n\n${content}` : content
      }
      continue
    }
    if (lower.startsWith('раздел:') || lower.startsWith('section:')) {
      const heading = title.includes(':') ? title.split(':').slice(1).join(':').trim() : title
      sections.push({ heading, body: content })
      continue
    }
    if (lower === 'лаба' || lower === 'lab' || lower === 'лабораторная') {
      lab = content
      continue
    }
    if (lower.startsWith('схема:') || lower.startsWith('diagram:')) {
      const caption = title.includes(':') ? title.split(':').slice(1).join(':').trim() : title
      const mermaidMatch = /```mermaid\s*([\s\S]*?)```/i.exec(content)
      diagrams.push({
        caption: caption || 'Схема',
        mermaid: (mermaidMatch?.[1] || content).trim(),
      })
      continue
    }
    if (lower === 'тест' || lower === 'quiz' || lower === 'тест:') {
      quiz = [...quiz, ...parseQuiz(content)]
      continue
    }
    if (lower === 'шпаргалка' || lower === 'cheatsheet') {
      cheatsheetHtml = content
      continue
    }
    if (lower === 'anki' || lower === 'карточки') {
      anki = [...anki, ...parseAnki(content)]
      continue
    }
    if (lower === 'итоги' || lower === 'summary' || lower === 'выводы') {
      summary = [...summary, ...parseSummary(content)]
      continue
    }
    if (lower === 'ссылки' || lower === 'links') {
      links = [...links, ...parseLinks(content)]
      continue
    }
    appendixParts.push(`## ${title}\n\n${content}`.trim())
    warnings.push(`Неизвестный раздел '## ${title}' → appendix`)
  }

  const structured: StructuredPost = {
    version: 1,
    intro: intro.trim(),
    sections: sections.length > 0 ? sections : [{ heading: 'Основная часть', body: '' }],
    diagrams,
    quiz,
    anki,
    summary: summary.length > 0 ? summary : [''],
    lab: lab.trim() || undefined,
    cheatsheetHtml: cheatsheetHtml.trim() || undefined,
    appendix: appendixParts.length > 0 ? appendixParts.join('\n\n').trim() : undefined,
  }

  const theoryParts = [intro.trim()]
  for (const section of sections) {
    if (section.heading.trim()) {
      theoryParts.push(`## ${section.heading.trim()}`)
    }
    if (section.body.trim()) {
      theoryParts.push(section.body.trim())
    }
  }

  const order = Number(meta.order ?? fallback.order ?? 0)
  const durationMin = Number(meta.durationmin ?? meta.duration_min ?? fallback.durationMin ?? 0)
  if (meta.order != null && Number.isNaN(order)) {
    warnings.push('order не число — 0')
  }
  if ((meta.durationmin || meta.duration_min) && Number.isNaN(durationMin)) {
    warnings.push('durationMin не число — 0')
  }

  const metaFields = normalizeLearnMeta({
    profiles: metaList('profiles').length ? metaList('profiles') : fallback.profiles,
    level: meta.level || fallback.level || '',
    tags: metaList('tags').length ? metaList('tags') : fallback.tags,
    excerpt: parseYamlScalar(meta.excerpt || fallback.excerpt || ''),
    durationMin: Number.isFinite(durationMin) ? Math.max(0, durationMin) : 0,
    prerequisites: metaList('prerequisites').length
      ? metaList('prerequisites')
      : fallback.prerequisites,
    author: parseYamlScalar(meta.author || fallback.author || ''),
    authorUrl: parseYamlScalar(meta.authorurl || meta.author_url || fallback.authorUrl || ''),
    coverUrl: parseYamlScalar(meta.coverurl || meta.cover_url || fallback.coverUrl || ''),
    seoTitle: parseYamlScalar(meta.seotitle || meta.seo_title || fallback.seoTitle || ''),
    seoDescription: parseYamlScalar(
      meta.seodescription || meta.seo_description || fallback.seoDescription || '',
    ),
    seoKeywords: metaList('seokeywords').length
      ? metaList('seokeywords')
      : metaList('seo_keywords').length
        ? metaList('seo_keywords')
        : fallback.seoKeywords,
    canonicalUrl: parseYamlScalar(
      meta.canonicalurl || meta.canonical_url || fallback.canonicalUrl || '',
    ),
  })

  const onMapFlag = parseBool(
    meta.onknowledgemap || meta.on_knowledge_map || meta['on-knowledge-map'],
  )
  if (onMapFlag != null) {
    metaFields.tags = withKnowledgeMapTag(metaFields.tags, onMapFlag)
  }

  const firstDiagram = diagrams.find((d) => d.mermaid.trim())?.mermaid || ''

  return {
    slug: (meta.slug || fallback.slug || '').trim().toLowerCase(),
    episode: (meta.episode || fallback.episode || '').trim(),
    title: parseYamlScalar(meta.title || fallback.title || ''),
    shortTitle: parseYamlScalar(meta.shorttitle || meta.short_title || fallback.shortTitle || ''),
    rubricId: rubric,
    order: Number.isFinite(order) ? order : 0,
    theory: theoryParts.filter(Boolean).join('\n\n'),
    lab: lab.trim(),
    cheatsheet: cheatsheetHtml.trim(),
    diagram: firstDiagram,
    links: links.length > 0 ? links : fallback.links || [],
    structured,
    theoryFormat: 'markdown',
    labFormat: 'markdown',
    cheatsheetFormat: 'html',
    publishedAt:
      (meta.publishedat || meta.published_at || fallback.publishedAt || new Date().toISOString()).trim(),
    ...metaFields,
    warnings,
  }
}

export function serializeLearnArticleFile(post: LearnPostInput): string {
  const structured = post.structured || EMPTY_LEARN_STRUCTURED_POST
  const meta = normalizeLearnMeta(post)
  const front = [
    '---',
    `slug: ${escapeYamlScalar(post.slug.trim())}`,
    `title: ${escapeYamlScalar(post.title.trim())}`,
    `shortTitle: ${escapeYamlScalar(post.shortTitle.trim())}`,
    `episode: ${escapeYamlScalar(post.episode.trim())}`,
    `rubric: ${escapeYamlScalar(post.rubricId)}`,
    `order: ${post.order || 0}`,
    `publishedAt: ${escapeYamlScalar(post.publishedAt)}`,
    `profiles: ${formatYamlList(meta.profiles)}`,
    `level: ${escapeYamlScalar(meta.level)}`,
    `tags: ${formatYamlList(meta.tags)}`,
    `onKnowledgeMap: ${hasKnowledgeMapTag(meta.tags) ? 'true' : 'false'}`,
    `durationMin: ${meta.durationMin || 0}`,
    `excerpt: ${escapeYamlScalar(meta.excerpt)}`,
    `prerequisites: ${formatYamlList(meta.prerequisites)}`,
    `author: ${escapeYamlScalar(meta.author)}`,
    `authorUrl: ${escapeYamlScalar(meta.authorUrl)}`,
    `coverUrl: ${escapeYamlScalar(meta.coverUrl)}`,
    `seoTitle: ${escapeYamlScalar(meta.seoTitle)}`,
    `seoDescription: ${escapeYamlScalar(meta.seoDescription)}`,
    `seoKeywords: ${formatYamlList(meta.seoKeywords)}`,
    `canonicalUrl: ${escapeYamlScalar(meta.canonicalUrl)}`,
    '---',
    '',
  ].join('\n')

  const parts: string[] = []
  if (structured.intro.trim()) {
    parts.push(`## Введение\n\n${structured.intro.trim()}`)
  }
  for (const section of structured.sections) {
    const heading = section.heading.trim() || 'Основная часть'
    parts.push(`## Раздел: ${heading}\n\n${section.body.trim()}`)
  }
  if ((structured.lab || post.lab || '').trim()) {
    parts.push(`## Лаба\n\n${(structured.lab || post.lab || '').trim()}`)
  }
  for (const diagram of structured.diagrams) {
    if (!diagram.mermaid.trim()) {
      continue
    }
    parts.push(
      `## Схема: ${diagram.caption.trim() || 'Схема'}\n\n\`\`\`mermaid\n${diagram.mermaid.trim()}\n\`\`\``,
    )
  }
  const quizItems = structured.quiz.filter((q) => q.question.trim() || q.answer.trim())
  if (quizItems.length > 0) {
    const quizBlocks = ['## Тест', '']
    for (const item of quizItems) {
      quizBlocks.push(`### ${item.question.trim()}`)
      quizBlocks.push('')
      quizBlocks.push(`**Ответ:** ${item.answer.trim()}`)
      quizBlocks.push('')
      if (item.explain.trim()) {
        quizBlocks.push(`**Пояснение:** ${item.explain.trim()}`)
        quizBlocks.push('')
      }
    }
    parts.push(quizBlocks.join('\n').trim())
  }
  const cheatsheet = (structured.cheatsheetHtml || post.cheatsheet || '').trim()
  if (cheatsheet) {
    parts.push(`## Шпаргалка\n\n${cheatsheet}`)
  }
  const ankiItems = structured.anki.filter((a) => a.front.trim() || a.back.trim())
  if (ankiItems.length > 0) {
    const ankiBlocks = ['## Anki', '']
    for (const item of ankiItems) {
      ankiBlocks.push(`### Front: ${item.front.trim()}`)
      ankiBlocks.push('')
      ankiBlocks.push(`Back: ${item.back.trim()}`)
      ankiBlocks.push('')
    }
    parts.push(ankiBlocks.join('\n').trim())
  }
  const summaryItems = structured.summary.map((s) => s.trim()).filter(Boolean)
  if (summaryItems.length > 0) {
    parts.push(`## Итоги\n\n${summaryItems.map((item) => `- ${item}`).join('\n')}`)
  }
  if (post.links.length > 0) {
    const linkLines = ['## Ссылки', '']
    for (const link of post.links) {
      linkLines.push(`- [${link.label || link.href}](${link.href || '#'})`)
    }
    parts.push(linkLines.join('\n'))
  }
  if (structured.appendix?.trim()) {
    parts.push(structured.appendix.trim())
  }

  return `${front}${parts.join('\n\n').trim()}\n`
}

export function downloadLearnArticleFile(post: LearnPostInput): void {
  const filenameBase = (post.slug || post.title || 'learn-article')
    .trim()
    .replace(/[^\w.-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
  const blob = new Blob([serializeLearnArticleFile(post)], {
    type: 'text/markdown;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${filenameBase || 'learn-article'}.md`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function downloadLearnArticleTemplate(markdown: string): void {
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'learn-article-template.md'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error || new Error('Не удалось прочитать файл'))
    reader.readAsText(file, 'UTF-8')
  })
}

export type { LearnPostMeta, LearnProfileId, LearnLevelId }
export { EMPTY_LEARN_META }
