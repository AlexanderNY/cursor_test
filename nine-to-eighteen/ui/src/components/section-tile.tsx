import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { prefetchPyodideRuntime } from '@/game/bowl/pyodide-prefetch'
import { serviceOpenTarget, type Section } from '@/data/sections'

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

export function SectionTile({ section }: SectionTileProps) {
  const needsPyodide = section.slug === 'bowl' || section.slug === 'code'
  const tileStyle = { '--tile-accent': section.accent } as CSSProperties
  const prefetchHandlers = {
    onMouseEnter: needsPyodide ? prefetchBowlRuntime : undefined,
    onFocus: needsPyodide ? prefetchBowlRuntime : undefined,
  }
  const target = serviceOpenTarget(section)
  const className = target.external ? 'section-tile section-tile-external' : 'section-tile'

  if (target.external) {
    return (
      <a
        href={target.href}
        className={className}
        style={tileStyle}
        target="_blank"
        rel="noopener noreferrer"
        {...prefetchHandlers}
      >
        <SectionTileContent section={section} />
      </a>
    )
  }

  return (
    <Link to={target.href} className={className} style={tileStyle} {...prefetchHandlers}>
      <SectionTileContent section={section} />
    </Link>
  )
}
