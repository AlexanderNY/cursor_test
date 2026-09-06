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

function SectionTileContent({ section }: SectionTileProps) {
  return (
    <>
      {section.emoji && (
        <span className="section-tile-emoji" aria-hidden>
          {section.emoji}
        </span>
      )}
      <span className="section-tile-title">{section.title}</span>
      <span className="section-tile-subtitle">{section.subtitle}</span>
    </>
  )
}

/** Плашка на главной всегда ведёт на страницу описания сервиса. */
function tileTarget(section: Section): string {
  return `/app/${section.slug}`
}

export function SectionTile({ section }: SectionTileProps) {
  const isBowl = section.slug === 'bowl'
  const tileStyle = { '--tile-accent': section.accent } as CSSProperties
  const prefetchHandlers = {
    onMouseEnter: isBowl ? prefetchBowlRuntime : undefined,
    onFocus: isBowl ? prefetchBowlRuntime : undefined,
  }

  return (
    <Link
      to={tileTarget(section)}
      className="section-tile"
      style={tileStyle}
      {...prefetchHandlers}
    >
      <SectionTileContent section={section} />
    </Link>
  )
}
