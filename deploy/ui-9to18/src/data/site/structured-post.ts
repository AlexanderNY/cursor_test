/** Unified article format for service blogs: reading + quiz + anki. */

export type StructuredSection = {
  heading: string
  body: string
}

export type StructuredDiagram = {
  caption: string
  mermaid: string
}

export type StructuredQuizItem = {
  question: string
  answer: string
  explain: string
}

export type StructuredAnkiItem = {
  front: string
  back: string
}

export type StructuredPost = {
  version: 1
  intro: string
  sections: StructuredSection[]
  diagrams: StructuredDiagram[]
  quiz: StructuredQuizItem[]
  anki: StructuredAnkiItem[]
  summary: string[]
  /** Optional free markdown appendix (legacy / extras) */
  appendix?: string
}

export const EMPTY_STRUCTURED_POST: StructuredPost = {
  version: 1,
  intro: '',
  sections: [{ heading: '', body: '' }],
  diagrams: [],
  quiz: [{ question: '', answer: '', explain: '' }],
  anki: [{ front: '', back: '' }],
  summary: [''],
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object' && !Array.isArray(value)
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function normalizeQuiz(raw: unknown): StructuredQuizItem[] {
  if (!Array.isArray(raw)) {
    return []
  }
  return raw.map((item) => {
    const row = isRecord(item) ? item : {}
    return {
      question: asString(row.question),
      answer: asString(row.answer),
      explain: asString(row.explain),
    }
  })
}

function normalizeAnki(raw: unknown): StructuredAnkiItem[] {
  if (!Array.isArray(raw)) {
    return []
  }
  return raw.map((item) => {
    const row = isRecord(item) ? item : {}
    return {
      front: asString(row.front),
      back: asString(row.back),
    }
  })
}

export function normalizeStructuredPost(raw: unknown): StructuredPost | null {
  if (!isRecord(raw)) {
    return null
  }
  if (raw.version !== 1 && raw.version !== '1') {
    return null
  }
  const sections = Array.isArray(raw.sections)
    ? raw.sections.map((item) => {
        const row = isRecord(item) ? item : {}
        return { heading: asString(row.heading), body: asString(row.body) }
      })
    : []
  const diagrams = Array.isArray(raw.diagrams)
    ? raw.diagrams.map((item) => {
        const row = isRecord(item) ? item : {}
        return { caption: asString(row.caption), mermaid: asString(row.mermaid) }
      })
    : []
  const summary = Array.isArray(raw.summary)
    ? raw.summary.map((item) => asString(item))
    : []
  return {
    version: 1,
    intro: asString(raw.intro),
    sections: sections.length > 0 ? sections : [{ heading: '', body: '' }],
    diagrams,
    quiz: normalizeQuiz(raw.quiz),
    anki: normalizeAnki(raw.anki),
    summary: summary.length > 0 ? summary : [''],
    appendix: asString(raw.appendix) || undefined,
  }
}

export function parsePostBody(body: string): {
  structured: StructuredPost | null
  legacyMarkdown: string
} {
  const text = (body || '').trim()
  if (!text.startsWith('{')) {
    return { structured: null, legacyMarkdown: body || '' }
  }
  try {
    const parsed = JSON.parse(text) as unknown
    const structured = normalizeStructuredPost(parsed)
    if (structured) {
      return { structured, legacyMarkdown: '' }
    }
  } catch {
    /* legacy markdown that happens to start with { */
  }
  return { structured: null, legacyMarkdown: body || '' }
}

export function serializeStructuredPost(post: StructuredPost): string {
  const cleaned: StructuredPost = {
    version: 1,
    intro: post.intro.trim(),
    sections: post.sections
      .map((s) => ({ heading: s.heading.trim(), body: s.body.trim() }))
      .filter((s) => s.heading || s.body),
    diagrams: post.diagrams
      .map((d) => ({ caption: d.caption.trim(), mermaid: d.mermaid.trim() }))
      .filter((d) => d.caption || d.mermaid),
    quiz: post.quiz
      .map((q) => ({
        question: q.question.trim(),
        answer: q.answer.trim(),
        explain: q.explain.trim(),
      }))
      .filter((q) => q.question || q.answer),
    anki: post.anki
      .map((a) => ({ front: a.front.trim(), back: a.back.trim() }))
      .filter((a) => a.front || a.back),
    summary: post.summary.map((s) => s.trim()).filter(Boolean),
  }
  if (post.appendix?.trim()) {
    cleaned.appendix = post.appendix.trim()
  }
  if (cleaned.sections.length === 0) {
    cleaned.sections = [{ heading: '', body: '' }]
  }
  return JSON.stringify(cleaned, null, 2)
}

export function structuredExcerpt(post: StructuredPost, maxLen = 220): string {
  const raw = post.intro || post.sections[0]?.body || post.summary[0] || ''
  const plain = raw.replace(/\s+/g, ' ').trim()
  if (plain.length <= maxLen) {
    return plain
  }
  const cut = plain.slice(0, maxLen + 1)
  const at = cut.lastIndexOf(' ')
  return `${(at > 80 ? cut.slice(0, at) : plain.slice(0, maxLen)).trim()}…`
}

export function ensureAnkiFromQuiz(post: StructuredPost): StructuredAnkiItem[] {
  const existing = post.anki.filter((a) => a.front.trim() && a.back.trim())
  if (existing.length > 0) {
    return existing
  }
  const fromQuiz = post.quiz
    .filter((q) => q.question.trim() && q.answer.trim())
    .map((q) => ({
      front: q.question.trim(),
      back: q.explain.trim()
        ? `${q.answer.trim()}\n\n${q.explain.trim()}`
        : q.answer.trim(),
    }))
  const fromSummary = post.summary
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => ({ front: `Итог: ${s.slice(0, 80)}${s.length > 80 ? '…' : ''}`, back: s }))
  return [...fromQuiz, ...fromSummary]
}

export function validateStructuredPost(post: StructuredPost): string[] {
  const errors: string[] = []
  if (!post.intro.trim() || post.intro.trim().length < 40) {
    errors.push('Введение: минимум ~40 символов')
  }
  const hasSection = post.sections.some((s) => s.body.trim())
  if (!hasSection) {
    errors.push('Основная часть: нужен хотя бы один раздел с текстом')
  }
  const quizOk = post.quiz.some((q) => q.question.trim() && q.answer.trim())
  const ankiOk = post.anki.some((a) => a.front.trim() && a.back.trim())
  if (!quizOk && !ankiOk) {
    errors.push('Нужен тест (вопрос+ответ) или хотя бы одна anki-карточка')
  }
  return errors
}

export function legacyBodyToStructured(markdown: string): StructuredPost {
  return {
    ...EMPTY_STRUCTURED_POST,
    intro: '',
    sections: [{ heading: 'Основная часть', body: markdown }],
    quiz: [],
    anki: [],
    summary: [],
    appendix: undefined,
  }
}
