import { ReactNode, useState } from 'react'
import { safeHref } from '@/data/safe-url'
import type { PortfolioContacts } from '@/data/site/portfolio-api'

export type PortfolioTileModel = {
  id: string
  title: string
  blurb: string
  link: string
  imageUrl: string
  tags?: string[]
  extra?: ReactNode
  actions?: ReactNode
}

function mailHref(email: string): string | null {
  const value = email.trim()
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) {
    return null
  }
  return `mailto:${value}`
}

function linkHost(url: string): string {
  try {
    return new URL(url).host.replace(/^www\./, '')
  } catch {
    return 'Открыть'
  }
}

function TileImage({ src, title }: { src: string; title: string }) {
  const [failed, setFailed] = useState(false)
  if (!src || failed) {
    return (
      <div className="portfolio-tile-placeholder" aria-hidden>
        {(title || '•').slice(0, 1).toUpperCase()}
      </div>
    )
  }
  return (
    <img
      src={src}
      alt=""
      className="portfolio-tile-image"
      onError={() => setFailed(true)}
    />
  )
}

function TileContacts({ contacts }: { contacts: PortfolioContacts }) {
  const site = safeHref(contacts.url)
  const mail = mailHref(contacts.email)
  if (!contacts.phone && !mail && !site) {
    return null
  }
  return (
    <ul className="portfolio-tile-contacts">
      {contacts.phone ? <li>{contacts.phone}</li> : null}
      {mail ? (
        <li>
          <a href={mail}>{contacts.email.trim()}</a>
        </li>
      ) : null}
      {site ? (
        <li>
          <a href={site} target="_blank" rel="noopener noreferrer">
            {linkHost(site)}
          </a>
        </li>
      ) : null}
    </ul>
  )
}

export function PortfolioTileGrid({
  tiles,
  contacts,
}: {
  tiles: PortfolioTileModel[]
  contacts: PortfolioContacts
}) {
  if (tiles.length === 0) {
    return null
  }
  return (
    <div className="portfolio-tiles">
      {tiles.map((tile) => {
        const href = safeHref(tile.link)
        return (
          <article key={tile.id} className="portfolio-tile">
            <div className="portfolio-tile-media">
              <TileImage src={tile.imageUrl} title={tile.title} />
            </div>
            <div className="portfolio-tile-body">
              <h2 className="portfolio-tile-title">{tile.title}</h2>
              {tile.blurb ? <p className="portfolio-tile-blurb">{tile.blurb}</p> : null}
              {tile.tags && tile.tags.length > 0 ? (
                <p className="portfolio-case-meta">
                  {tile.tags.map((tag) => (
                    <span key={tag} className="portfolio-chip">
                      {tag}
                    </span>
                  ))}
                </p>
              ) : null}
              {href ? (
                <a className="portfolio-tile-link" href={href} target="_blank" rel="noopener noreferrer">
                  Ссылка · {linkHost(href)}
                </a>
              ) : null}
              <TileContacts contacts={contacts} />
              {tile.extra}
              {tile.actions}
            </div>
          </article>
        )
      })}
    </div>
  )
}
