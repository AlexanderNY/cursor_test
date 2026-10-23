import { safeHref } from '@/utils/safe-url'

const ALLOWED = new Set(['P', 'BR', 'STRONG', 'B', 'EM', 'I', 'UL', 'OL', 'LI', 'A'])

function sanitizeNode(node: Node, doc: Document): Node | null {
  if (node.nodeType === Node.TEXT_NODE) {
    return doc.createTextNode(node.textContent ?? '')
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return null

  const element = node as Element
  const tag = element.tagName.toUpperCase()
  if (!ALLOWED.has(tag)) {
    const fragment = doc.createDocumentFragment()
    for (const child of Array.from(element.childNodes)) {
      const next = sanitizeNode(child, doc)
      if (next) fragment.appendChild(next)
    }
    return fragment
  }

  const clean = doc.createElement(tag.toLowerCase())
  if (tag === 'A') {
    const href = safeHref(element.getAttribute('href'))
    if (href) {
      clean.setAttribute('href', href)
      if (href.startsWith('http://') || href.startsWith('https://')) {
        clean.setAttribute('target', '_blank')
        clean.setAttribute('rel', 'noreferrer noopener')
      }
    }
  }
  for (const child of Array.from(element.childNodes)) {
    const next = sanitizeNode(child, doc)
    if (next) clean.appendChild(next)
  }
  return clean
}

/** Keep a short tag list so stored notification HTML cannot run script. */
export function sanitizeNotificationHtml(html: string): string {
  if (!html) return ''
  if (typeof DOMParser === 'undefined') return ''
  const doc = new DOMParser().parseFromString(`<div id="n-root">${html}</div>`, 'text/html')
  const root = doc.getElementById('n-root')
  if (!root) return ''
  const out = doc.createElement('div')
  for (const child of Array.from(root.childNodes)) {
    const next = sanitizeNode(child, doc)
    if (next) out.appendChild(next)
  }
  return out.innerHTML
}
