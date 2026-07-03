import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { prefetchPyodideRuntime } from '@/game/bowl/pyodide-prefetch'
import type { Section } from '@/data/sections'

interface SectionTileProps {
  section: Section
}

function prefetchBowlRuntime(): void {
  prefetchPyodideRuntime()
}

export function SectionTile({ section }: SectionTileProps) {
  const isBowl = section.slug === 'bowl'

  return (
    <Link
      to={`/game/${section.slug}`}
      className="section-tile"
      style={{ '--tile-accent': section.accent } as CSSProperties}
      onMouseEnter={isBowl ? prefetchBowlRuntime : undefined}
      onFocus={isBowl ? prefetchBowlRuntime : undefined}
    >
      {section.emoji && (
        <span className="section-tile-emoji" aria-hidden>
          {section.emoji}
        </span>
      )}
      <span className="section-tile-title">{section.title}</span>
      <span className="section-tile-subtitle">{section.subtitle}</span>
    </Link>
  )
}
