import type { CSSProperties, ReactNode } from 'react'
import type { GuideBlockStyle } from '@/services/guide-service'

/** Minimal markdown: paragraphs, ### headings, lists, **bold**. */
export function renderGuideMarkdown(body: string, textColor?: string): ReactNode {
  if (!body.trim()) return null
  const blocks = body.replace(/\r\n/g, '\n').split(/\n{2,}/)
  const colorStyle = textColor ? { color: textColor } : undefined

  return blocks.map((block, bi) => {
    const lines = block.split('\n').filter((l) => l.length > 0)
    if (lines.length === 0) return null

    const isUl = lines.every((l) => /^[-*]\s+/.test(l))
    const isOl = lines.every((l) => /^\d+\.\s+/.test(l))
    if (isUl || isOl) {
      const ListTag = isOl ? 'ol' : 'ul'
      return (
        <ListTag
          key={bi}
          className={`${isOl ? 'list-decimal' : 'list-disc'} list-inside space-y-1 mb-3`}
          style={colorStyle}
        >
          {lines.map((line, li) => (
            <li key={li}>{inlineBold(line.replace(/^([-*]|\d+\.)\s+/, ''))}</li>
          ))}
        </ListTag>
      )
    }

    if (lines.length === 1 && /^###\s+/.test(lines[0])) {
      return (
        <h3 key={bi} className="font-medium text-[var(--text-primary)] mt-3 mb-1" style={colorStyle}>
          {inlineBold(lines[0].replace(/^###\s+/, ''))}
        </h3>
      )
    }

    return (
      <p key={bi} className="mb-3 leading-relaxed" style={colorStyle}>
        {lines.map((line, li) => (
          <span key={li}>
            {li > 0 && <br />}
            {inlineBold(line)}
          </span>
        ))}
      </p>
    )
  })
}

function inlineBold(text: string): ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="text-[var(--text-primary)] font-medium">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export function styleToCss(style?: GuideBlockStyle): CSSProperties {
  if (!style) return {}
  const css: CSSProperties = {}
  if (style.backgroundColor) css.backgroundColor = style.backgroundColor
  if (style.borderColor) css.borderColor = style.borderColor
  if (style.borderRadius) css.borderRadius = style.borderRadius
  if (style.padding) css.padding = style.padding
  if (style.textColor) css.color = style.textColor
  if (style.borderColor) css.borderWidth = 1
  if (style.borderColor) css.borderStyle = 'solid'
  return css
}

export function titleStyle(style?: GuideBlockStyle): CSSProperties {
  if (!style) return {}
  const css: CSSProperties = {}
  if (style.titleColor) css.color = style.titleColor
  if (style.titleFontSize) css.fontSize = style.titleFontSize
  if (style.titleFontWeight) css.fontWeight = style.titleFontWeight as CSSProperties['fontWeight']
  return css
}

export function subtitleStyle(style?: GuideBlockStyle): CSSProperties {
  if (!style) return {}
  const css: CSSProperties = {}
  if (style.subtitleColor) css.color = style.subtitleColor
  else if (style.textColor) css.color = style.textColor
  return css
}

export function bodyStyle(style?: GuideBlockStyle): CSSProperties {
  if (!style) return {}
  const css: CSSProperties = {}
  if (style.textColor) css.color = style.textColor
  if (style.bodyFontSize) css.fontSize = style.bodyFontSize
  return css
}
