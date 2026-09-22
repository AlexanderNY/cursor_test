import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { SitePromo, SpotlightItem } from '@/data/promo'

interface PromoSpotlightProps {
  promo: SitePromo
}

const AUTO_MS = 6500

function SlideCard({ item, active }: { item: SpotlightItem; active: boolean }) {
  return (
    <article
      className={`promo-spotlight-slide${active ? ' is-active' : ''}`}
      style={{ '--promo-accent': item.accent } as CSSProperties}
      aria-hidden={!active}
    >
      <div className="promo-spotlight-meta">
        <p className="promo-spotlight-service">
          {item.emoji ? <span aria-hidden>{item.emoji}</span> : null}
          {item.appTitle}
        </p>
      </div>
      <h2 className="promo-spotlight-title">{item.title}</h2>
      {item.excerpt ? <p className="promo-spotlight-body">{item.excerpt}</p> : null}
      <Link className="promo-spotlight-cta" to={item.href} tabIndex={active ? 0 : -1}>
        Читать статью
      </Link>
    </article>
  )
}

export function PromoSpotlight({ promo }: PromoSpotlightProps) {
  const items = promo.enabled ? promo.items.slice(0, 5) : []
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    setIndex(0)
  }, [items.length])

  useEffect(() => {
    if (items.length < 2 || paused) {
      return
    }
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % items.length)
    }, AUTO_MS)
    return () => window.clearInterval(timer)
  }, [items.length, paused])

  if (!promo.enabled || items.length === 0) {
    return null
  }

  const safeIndex = index % items.length
  const active = items[safeIndex]

  return (
    <section
      className="promo-spotlight promo-spotlight-carousel"
      style={{ '--promo-accent': active.accent } as CSSProperties}
      aria-roledescription="carousel"
      aria-label={promo.eyebrow || 'Спотлайт'}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setPaused(false)
        }
      }}
    >
      <div className="promo-spotlight-meta">
        {promo.eyebrow ? <p className="promo-spotlight-eyebrow">{promo.eyebrow}</p> : null}
        {items.length > 1 ? (
          <p className="promo-spotlight-count">
            {safeIndex + 1} / {items.length}
          </p>
        ) : null}
      </div>

      <div className="promo-spotlight-viewport">
        {items.map((item, itemIndex) => (
          <SlideCard key={`${item.appSlug}-${item.postSlug}`} item={item} active={itemIndex === safeIndex} />
        ))}
      </div>

      {items.length > 1 ? (
        <div className="promo-spotlight-controls">
          <button
            type="button"
            className="promo-spotlight-nav"
            aria-label="Предыдущая статья"
            onClick={() => setIndex((current) => (current - 1 + items.length) % items.length)}
          >
            ←
          </button>
          <div className="promo-spotlight-dots" role="tablist" aria-label="Слайды спотлайта">
            {items.map((item, itemIndex) => (
              <button
                key={`${item.appSlug}-${item.postSlug}-dot`}
                type="button"
                role="tab"
                aria-selected={itemIndex === safeIndex}
                className={`promo-spotlight-dot${itemIndex === safeIndex ? ' is-active' : ''}`}
                aria-label={`Слайд ${itemIndex + 1}: ${item.title}`}
                onClick={() => setIndex(itemIndex)}
              />
            ))}
          </div>
          <button
            type="button"
            className="promo-spotlight-nav"
            aria-label="Следующая статья"
            onClick={() => setIndex((current) => (current + 1) % items.length)}
          >
            →
          </button>
        </div>
      ) : null}
    </section>
  )
}
