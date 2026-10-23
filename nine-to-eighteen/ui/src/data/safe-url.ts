/** Navigation targets the site is willing to open. */

export const DATA_IMAGE_MAX_CHARS = 500 * 1024

export function safeHref(raw: string | null | undefined): string | null {
  if (!raw) return null
  const value = raw.trim()
  if (!value) return null
  if (value.startsWith('/')) {
    const second = value[1]
    if (second === '/' || second === '\\') return null
    return value
  }
  if (value.startsWith('#') && !value.includes(':')) {
    return value
  }
  try {
    const url = new URL(value)
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      return url.href
    }
  } catch {
    return null
  }
  return null
}

export function safeImageSrc(raw: string | null | undefined): string | null {
  if (!raw) return null
  const value = raw.trim()
  if (!value) return null
  if (value.toLowerCase().startsWith('data:image/')) {
    return value.length <= DATA_IMAGE_MAX_CHARS ? value : null
  }
  const href = safeHref(value)
  if (!href || href.startsWith('#')) return null
  return href
}

const SVG_DROP = new Set(['SCRIPT', 'FOREIGNOBJECT', 'IFRAME', 'OBJECT', 'EMBED'])

function isSafeSvgRef(value: string): boolean {
  const trimmed = value.trim()
  if (trimmed.startsWith('#') && !trimmed.includes(':')) return true
  return safeHref(trimmed)?.startsWith('http') ?? false
}

/** Drop active content from an SVG string before it is inserted into the page. */
export function sanitizeSvg(svg: string): string {
  if (!svg || typeof DOMParser === 'undefined') return ''
  const doc = new DOMParser().parseFromString(svg, 'image/svg+xml')
  const root = doc.documentElement
  if (!root || root.nodeName.toLowerCase() === 'parsererror') return ''

  const clean = (element: Element) => {
    for (const attr of Array.from(element.attributes)) {
      const name = attr.name.toLowerCase()
      if (name.startsWith('on')) {
        element.removeAttribute(attr.name)
        continue
      }
      if (name === 'href' || name.endsWith(':href')) {
        if (!isSafeSvgRef(attr.value)) element.removeAttribute(attr.name)
      }
    }
    for (const child of Array.from(element.children)) {
      if (SVG_DROP.has(child.tagName.toUpperCase().replace(/.*:/, ''))) {
        child.remove()
        continue
      }
      clean(child)
    }
  }

  clean(root)
  return root.outerHTML
}

export const MAX_SHARED_CODE_CHARS = 8000

/** Query-string snippets longer than the share cap are ignored. */
export function codeFromQuery(raw: string | null): string | null {
  if (!raw) return null
  let decoded = raw
  try {
    decoded = decodeURIComponent(raw)
  } catch {
    decoded = raw
  }
  if (decoded.length > MAX_SHARED_CODE_CHARS) return null
  return decoded
}
