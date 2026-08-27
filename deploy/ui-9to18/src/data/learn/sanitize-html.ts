const ALLOWED_TAGS = new Set([
  'H1',
  'H2',
  'H3',
  'P',
  'B',
  'STRONG',
  'I',
  'EM',
  'UL',
  'OL',
  'LI',
  'A',
  'IMG',
  'CODE',
  'PRE',
  'BR',
  'SPAN',
  'DIV',
])

function isSafeUrl(value: string): boolean {
  const trimmed = value.trim().toLowerCase()
  return (
    trimmed.startsWith('http://') ||
    trimmed.startsWith('https://') ||
    trimmed.startsWith('/') ||
    trimmed.startsWith('#') ||
    trimmed.startsWith('data:image/')
  )
}

function sanitizeElement(element: Element): void {
  const tag = element.tagName.toUpperCase()

  if (!ALLOWED_TAGS.has(tag)) {
    const text = element.ownerDocument.createTextNode(element.textContent ?? '')
    element.replaceWith(text)
    return
  }

  for (const attr of Array.from(element.attributes)) {
    const name = attr.name.toLowerCase()
    const isHref = tag === 'A' && name === 'href'
    const isSrc = tag === 'IMG' && name === 'src'
    const isAlt = tag === 'IMG' && name === 'alt'
    const isTitle = name === 'title'
    const isTarget = tag === 'A' && name === 'target'
    const isRel = tag === 'A' && name === 'rel'

    if (!(isHref || isSrc || isAlt || isTitle || isTarget || isRel)) {
      element.removeAttribute(attr.name)
      continue
    }

    if ((isHref || isSrc) && !isSafeUrl(attr.value)) {
      element.removeAttribute(attr.name)
    }
  }

  if (tag === 'A') {
    element.setAttribute('rel', 'noreferrer noopener')
    if (!element.getAttribute('target')) {
      element.setAttribute('target', '_blank')
    }
  }

  for (const child of Array.from(element.children)) {
    sanitizeElement(child)
  }
}

export function sanitizeLearnHtml(html: string): string {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return html
  }

  const parser = new DOMParser()
  const doc = parser.parseFromString(`<div id="root">${html}</div>`, 'text/html')
  const root = doc.getElementById('root')
  if (!root) {
    return ''
  }

  for (const child of Array.from(root.children)) {
    sanitizeElement(child)
  }

  return root.innerHTML
}

export function plainTextToHtml(text: string): string {
  const trimmed = text.trim()
  if (!trimmed) {
    return '<p></p>'
  }
  if (/<[a-z][\s\S]*>/i.test(trimmed)) {
    return trimmed
  }

  const escaped = trimmed
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  return escaped
    .split(/\n{2,}/)
    .map((block) => `<p>${block.replace(/\n/g, '<br>')}</p>`)
    .join('')
}
