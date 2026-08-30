/** Markdown-файл статьи сайта с YAML-frontmatter. */

export type SitePostFilePayload = {
  slug: string
  title: string
  body: string
  isPublished: boolean
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

function parseBool(raw: string | undefined, fallback: boolean): boolean {
  if (raw == null || raw === '') {
    return fallback
  }
  const value = raw.trim().toLowerCase()
  if (value === 'true' || value === '1' || value === 'yes') {
    return true
  }
  if (value === 'false' || value === '0' || value === 'no') {
    return false
  }
  return fallback
}

export function serializeSitePostFile(post: SitePostFilePayload): string {
  const front = [
    '---',
    `slug: ${escapeYamlScalar(post.slug.trim())}`,
    `title: ${escapeYamlScalar(post.title.trim())}`,
    `published: ${post.isPublished ? 'true' : 'false'}`,
    '---',
    '',
  ].join('\n')
  return `${front}${post.body.replace(/^\uFEFF/, '')}`
}

export function parseSitePostFile(
  text: string,
  fallback: Partial<SitePostFilePayload> = {},
): SitePostFilePayload {
  const source = text.replace(/^\uFEFF/, '')
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/.exec(source)
  if (!match) {
    return {
      slug: fallback.slug || '',
      title: fallback.title || '',
      body: source,
      isPublished: fallback.isPublished ?? true,
    }
  }

  const meta: Record<string, string> = {}
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
    meta[key] = parseYamlScalar(trimmed.slice(colon + 1))
  }

  return {
    slug: meta.slug || fallback.slug || '',
    title: meta.title || fallback.title || '',
    body: match[2].replace(/^\r?\n/, ''),
    isPublished: parseBool(meta.published ?? meta.is_published, fallback.isPublished ?? true),
  }
}

export function downloadSitePostFile(post: SitePostFilePayload): void {
  const filenameBase = (post.slug || post.title || 'post')
    .trim()
    .replace(/[^\w.-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
  const blob = new Blob([serializeSitePostFile(post)], {
    type: 'text/markdown;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${filenameBase || 'post'}.md`
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
