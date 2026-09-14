import { useEffect } from 'react'

export type PageSeoInput = {
  title?: string
  description?: string
  image?: string
  canonical?: string
  keywords?: string[]
}

function upsertMeta(attr: 'name' | 'property', key: string, content: string): HTMLMetaElement {
  const selector = `meta[${attr}="${key}"]`
  let node = document.head.querySelector(selector) as HTMLMetaElement | null
  if (!node) {
    node = document.createElement('meta')
    node.setAttribute(attr, key)
    document.head.appendChild(node)
  }
  node.content = content
  return node
}

function upsertLink(rel: string, href: string): HTMLLinkElement {
  let node = document.head.querySelector(`link[rel="${rel}"]`) as HTMLLinkElement | null
  if (!node) {
    node = document.createElement('link')
    node.rel = rel
    document.head.appendChild(node)
  }
  node.href = href
  return node
}

/**
 * Client-side document title / meta / Open Graph for SPA article pages.
 * Restores previous title on unmount; leaves meta tags with last values (SPA-friendly).
 */
export function usePageSeo(input: PageSeoInput): void {
  useEffect(() => {
    const previousTitle = document.title
    const title = (input.title || '').trim()
    const description = (input.description || '').trim()
    const image = (input.image || '').trim()
    const canonical = (input.canonical || '').trim()
    const keywords = (input.keywords || []).map((item) => item.trim()).filter(Boolean)

    if (title) {
      document.title = title
      upsertMeta('property', 'og:title', title)
    }
    if (description) {
      upsertMeta('name', 'description', description)
      upsertMeta('property', 'og:description', description)
    }
    if (image) {
      upsertMeta('property', 'og:image', image)
    }
    if (keywords.length > 0) {
      upsertMeta('name', 'keywords', keywords.join(', '))
    }
    if (canonical) {
      upsertLink('canonical', canonical)
      upsertMeta('property', 'og:url', canonical)
    }

    return () => {
      document.title = previousTitle
    }
  }, [
    input.title,
    input.description,
    input.image,
    input.canonical,
    (input.keywords || []).join(','),
  ])
}
